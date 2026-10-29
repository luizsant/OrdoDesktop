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
            wa = workarea()
            x = min(max(round(p.x() / self.SNAP) * self.SNAP, wa.left()), wa.right() - 60)
            y = min(max(round(p.y() / self.SNAP) * self.SNAP, wa.top()), wa.bottom() - HEADER_H)
            self.move(x, y)
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
            snap = DesktopWindow.SNAP
            self.win.resize(max(self.min_size[0], round((size.width() + d.x()) / snap) * snap),
                            max(self.min_size[1], round((size.height() + d.y()) / snap) * snap))

    def mouseReleaseEvent(self, ev):
        if self.start:
            self.start = None
            getattr(self.win, "resized_by_user", self.win.geometry_changed)()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setPen(QColor(255, 255, 255, 90))
        p.drawText(self.rect(), Qt.AlignRight | Qt.AlignBottom, "◢")


