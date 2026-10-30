"""Peças comuns das janelas do Ordo: janela de fundo de tela, alça de redimensionar, tarefas e avisos."""
import os

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QVBoxLayout, QWidget

from . import system
from .catalog import APP_NAME, HEADER_H


class _Result(QObject):
    done = Signal(object, object)


class _Job(QRunnable):
    def __init__(self, work, emitter):
        super().__init__()
        self.work, self.emitter = work, emitter

    def run(self):
        try:
            res, err = self.work(), None
        except Exception as e:  # rede fora, timeout, formato inesperado
            res, err = None, e
        try:
            self.emitter.done.emit(res, err)
        except RuntimeError:  # o app fechou antes da resposta chegar
            pass


_alive = set()  # mantém os emissores vivos até a resposta chegar


def run_async(work, done):
    """Roda work() fora da interface e entrega (resultado, erro) a done() de volta na thread do Qt."""
    emitter = _Result()
    _alive.add(emitter)

    def finish(res, err):
        _alive.discard(emitter)
        done(res, err)

    emitter.done.connect(finish, Qt.QueuedConnection)
    QThreadPool.globalInstance().start(_Job(work, emitter))


class Toast(QWidget):
    """Aviso discreto no canto da tela (substitui notificação do sistema, que exigiria ícone na bandeja)."""

    def __init__(self, title, body, seconds=8):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        box = QWidget(self)
        box.setObjectName("toast")
        box.setStyleSheet("QWidget#toast { background: rgba(24,26,33,0.95); border: 1px solid #3a4060;"
                          " border-radius: 12px; } QLabel { color: white; } QLabel#b { color: #b8bdcc; }")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(18, 12, 18, 14)
        t = QLabel(f"<b>{title}</b>")
        b = QLabel(body, objectName="b")
        lay.addWidget(t)
        lay.addWidget(b)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(box)
        self.adjustSize()
        wa = workarea()
        self.move(wa.right() - self.width() - 24, wa.bottom() - self.height() - 24)
        self.show()
        QTimer.singleShot(seconds * 1000, self.close)

    def mousePressEvent(self, _ev):
        self.close()


def error(title, detail=""):
    box = QMessageBox(QMessageBox.Warning, APP_NAME, title)
    if detail:
        box.setInformativeText(detail)
    box.exec()


def workarea():
    return QApplication.primaryScreen().availableGeometry()


# ---------------------------------------------------------------------------
# Janela base: fica no fundo da tela, sem borda, arrastável e com posição salva
# ---------------------------------------------------------------------------
class DesktopWindow(QWidget):
    SNAP = 8

    def __init__(self, app, title):
        super().__init__(None)
        self.app = app
        self.setWindowTitle(f"{APP_NAME} — {title}")
        self.setAttribute(Qt.WA_TranslucentBackground)
        flags = Qt.FramelessWindowHint
        if system.IS_LINUX:
            # Tipo "área de trabalho": o gerenciador de janelas mantém atrás das janelas normais.
            self.setAttribute(Qt.WA_X11NetWmWindowTypeDesktop)
        else:
            flags |= Qt.Tool  # Windows: fora da barra de tarefas e do Alt+Tab; showEvent prende ao desktop
        if os.environ.get("ORDO_TEST_ABOVE"):  # só para capturas de teste
            flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        self.setWindowFlags(flags)
        self._drag = None

    def showEvent(self, ev):
        super().showEvent(ev)
        if system.IS_WINDOWS and not os.environ.get("ORDO_TEST_ABOVE"):
            system.pin_to_desktop(int(self.winId()))

    def nativeEvent(self, event_type, message):
        if system.IS_WINDOWS and not os.environ.get("ORDO_TEST_ABOVE") and event_type == b"windows_generic_MSG":
            system.keep_at_bottom(message)
        return False, 0

    # arrastar pela área que chamar begin_drag()
    def begin_drag(self, ev):
        self._drag = (ev.globalPosition().toPoint(), self.pos())

    def mouseMoveEvent(self, ev):
        if self._drag:
            start, origin = self._drag
            p = origin + (ev.globalPosition().toPoint() - start)
            x, y = magnet_move(self, p.x(), p.y())
            wa = workarea()
            self.move(min(max(x, wa.left()), wa.right() - 60), min(max(y, wa.top()), wa.bottom() - HEADER_H))
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        if self._drag:
            self._drag = None
            self.geometry_changed()
        super().mouseReleaseEvent(ev)

    def geometry_changed(self):
        """Chamado depois de mover/redimensionar; cada janela grava onde precisa."""

    def contextMenuEvent(self, ev):
        self.app.main_menu().exec(ev.globalPos())


if not system.IS_WINDOWS:
    del DesktopWindow.nativeEvent  # no Linux, evita uma chamada Python a cada evento do X11


# ---------------------------------------------------------------------------
# Encaixe magnético: bordas grudam nas das outras janelas e da tela, sempre com o mesmo espaço
# ---------------------------------------------------------------------------
GAP = 16      # espaço entre janelas (o mesmo do Reorganizar)
MARGIN = 24   # distância das bordas da tela
PULL = 14     # a partir de quantos pixels de distância a borda "puxa"
NEAR = 120    # só alinha com janelas que estão perto no outro eixo


def _others(win):
    return [w.geometry() for w in QApplication.topLevelWidgets()
            if w is not win and w.isVisible() and isinstance(w, DesktopWindow)]


def _nearest(value, targets):
    best = min(targets, key=lambda t: abs(t - value), default=None)
    return best if best is not None and abs(best - value) <= PULL else None


def _snap_axis(pos, size, lo, hi, others, horizontal, my_cross):
    """Melhor posição num eixo: alinhar bordas, ficar ao lado com GAP, ou na margem da tela."""
    cands = [lo + MARGIN, hi - MARGIN - size + 1]  # margens da tela
    for o in others:
        a0, a1 = (o.left(), o.right()) if horizontal else (o.top(), o.bottom())
        c0, c1 = (o.top(), o.bottom()) if horizontal else (o.left(), o.right())
        if c0 - NEAR > my_cross[1] or c1 + NEAR < my_cross[0]:
            continue  # longe no outro eixo: não interfere
        cands += [a0, a1 - size + 1,                 # alinhada pela esquerda/topo ou pela direita/base
                  a1 + 1 + GAP, a0 - GAP - size]     # encostada do lado, com o espaço padrão
    snapped = _nearest(pos, cands)
    return snapped if snapped is not None else round(pos / DesktopWindow.SNAP) * DesktopWindow.SNAP


def magnet_move(win, x, y):
    wa, others, w, h = workarea(), _others(win), win.width(), win.height()
    nx = _snap_axis(x, w, wa.left(), wa.right(), others, True, (y, y + h))
    ny = _snap_axis(y, h, wa.top(), wa.bottom(), others, False, (nx, nx + w))
    return nx, ny


def magnet_resize(win, w, h):
    """Redimensionar pelo canto: a borda direita/de baixo gruda nas das outras janelas e da tela."""
    wa, others, x, y = workarea(), _others(win), win.x(), win.y()
    right, bottom = x + w - 1, y + h - 1
    rights = [wa.right() - MARGIN]
    bottoms = [wa.bottom() - MARGIN]
    for o in others:
        if not (o.top() - NEAR > bottom or o.bottom() + NEAR < y):
            rights += [o.right(), o.left() - GAP - 1]
        if not (o.left() - NEAR > right or o.right() + NEAR < x):
            bottoms += [o.bottom(), o.top() - GAP - 1]
    r, b = _nearest(right, rights), _nearest(bottom, bottoms)
    snap = DesktopWindow.SNAP
    return (r - x + 1 if r is not None else round(w / snap) * snap,
            b - y + 1 if b is not None else round(h / snap) * snap)


class Grip(QWidget):
    """Alça ◢ de redimensionar. Manual: o Mutter não redimensiona janelas tipo "área de trabalho"."""

    def __init__(self, win, min_size=(160, HEADER_H + 60)):
        super().__init__(win)
        self.win, self.min_size, self.start = win, min_size, None
        self.setFixedSize(16, 16)
        self.setCursor(Qt.SizeFDiagCursor)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.start = (ev.globalPosition().toPoint(), self.win.size())

    def mouseMoveEvent(self, ev):
        if self.start:
            p0, size = self.start
            d = ev.globalPosition().toPoint() - p0
            w, h = magnet_resize(self.win, size.width() + d.x(), size.height() + d.y())
            self.win.resize(max(self.min_size[0], w), max(self.min_size[1], h))

    def mouseReleaseEvent(self, ev):
        if self.start:
            self.start = None
            getattr(self.win, "resized_by_user", self.win.geometry_changed)()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setPen(QColor(255, 255, 255, 90))
        p.drawText(self.rect(), Qt.AlignRight | Qt.AlignBottom, "◢")


