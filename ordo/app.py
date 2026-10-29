"""Ordo Desktop em Qt (PySide6): caixas automáticas, relógio e menus — Windows e Linux."""
import os
import shutil
import signal
import sys
import time
from datetime import datetime

if sys.platform.startswith("linux") and os.environ.get("XDG_SESSION_TYPE") == "wayland":
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")  # posicionar janelas exige X11 (XWayland)

from PySide6.QtCore import QFileInfo, QFileSystemWatcher, QMimeData, QPoint, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QColor, QFont, QIcon, QImageReader, QPainter, QPixmap
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFileIconProvider, QHBoxLayout, QInputDialog,
                               QLabel, QListView, QListWidget, QListWidgetItem, QMenu, QMessageBox, QStyle,
                               QStyledItemDelegate, QVBoxLayout, QWidget)

from . import i18n, system
from .catalog import APP_NAME, CAT_BY_KEY, CATEGORIES, HEADER_H, ICON_SIZE, THEMES, categorize
from .config import load_config, save_config
from .i18n import LANGUAGES, _, fold

SERVER_NAME = "ordo-desktop-qt"
ACCENT = "#7c8cff"


# ---------------------------------------------------------------------------
# Itens da área de trabalho
# ---------------------------------------------------------------------------
class DesktopItem:
    """Um arquivo/pasta/atalho presente na área de trabalho."""

    _icons = None

    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.is_dir = os.path.isdir(path)
        self.category = categorize(self.name, self.is_dir)
        self.display_name, self.theme_icon = self.name, None
        info = system.shortcut_info(path) if not self.is_dir else None
        if info:
            self.display_name, self.theme_icon = info
        self.sort_key = fold(self.display_name)

    def icon(self, size=ICON_SIZE):
        if self.category == "imagens":
            reader = QImageReader(self.path)
            if reader.canRead():
                reader.setScaledSize(reader.size().scaled(size, size, Qt.KeepAspectRatio))
                img = reader.read()
                if not img.isNull():
                    return QIcon(QPixmap.fromImage(img))
        if self.theme_icon:
            ic = QIcon(self.theme_icon) if os.path.isabs(self.theme_icon) else QIcon.fromTheme(self.theme_icon)
            if not ic.isNull():
                return ic
        if DesktopItem._icons is None:
            DesktopItem._icons = QFileIconProvider()
        return DesktopItem._icons.icon(QFileInfo(self.path))

    def open(self):
        try:
            system.open_path(self.path)
        except OSError as e:
            error(_("Não foi possível abrir “{name}”.", name=self.display_name), str(e))


def scan_desktop(show_hidden=False):
    folder = system.desktop_dir()
    try:
        names = os.listdir(folder)
    except OSError:
        return []
    items = []
    for n in names:
        if not show_hidden and (n.startswith(".") or n.endswith("~") or n.lower() == "desktop.ini"):
            continue
        items.append(DesktopItem(os.path.join(folder, n)))
    return items


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
            flags |= Qt.Tool | Qt.WindowStaysOnBottomHint  # Windows: fase 3 prende ao WorkerW
        if os.environ.get("ORDO_TEST_ABOVE"):  # só para capturas de teste
            flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        self.setWindowFlags(flags)
        self._drag = None

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
            self.win.geometry_changed()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setPen(QColor(255, 255, 255, 90))
        p.drawText(self.rect(), Qt.AlignRight | Qt.AlignBottom, "◢")


# ---------------------------------------------------------------------------
# Caixa (estilo Fences/360)
# ---------------------------------------------------------------------------
GRID_W, GRID_H = 76, 90


class TileDelegate(QStyledItemDelegate):
    """Ícone em cima e nome em até duas linhas (quebra em espaço/ponto/traço, ou no meio da palavra)."""

    def sizeHint(self, _option, _index):
        return QSize(GRID_W, GRID_H)

    def paint(self, p, option, index):
        r = option.rect.adjusted(2, 2, -2, -2)
        if option.state & QStyle.State_Selected:
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(120, 160, 255, 80))
            p.drawRoundedRect(r, 8, 8)
        elif option.state & QStyle.State_MouseOver:
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 26))
            p.drawRoundedRect(r, 8, 8)
        icon = index.data(Qt.DecorationRole)
        icon.paint(p, r.x() + (r.width() - ICON_SIZE) // 2, r.y() + 4, ICON_SIZE, ICON_SIZE)
        fm = option.fontMetrics
        lines = two_lines(index.data(Qt.DisplayRole), fm, r.width() - 2)
        p.setPen(QColor(255, 255, 255))
        y = r.y() + ICON_SIZE + 8
        for line in lines:
            p.drawText(r.x(), y, r.width(), fm.height(), Qt.AlignHCenter, line)
            y += fm.height()


def two_lines(text, fm, width):
    if fm.horizontalAdvance(text) <= width:
        return [text]
    cut = len(text)
    while cut > 1 and fm.horizontalAdvance(text[:cut]) > width:
        cut -= 1
    brk = max(text.rfind(c, 0, cut + 1) for c in " -_.")  # prefere quebrar entre palavras
    if brk > cut // 2:
        cut = brk + 1
    return [text[:cut].rstrip(), fm.elidedText(text[cut:].lstrip(), Qt.ElideRight, width)]


class ItemList(QListWidget):
    """Grade de ícones de uma caixa; arrastar leva o arquivo, soltar traz para a caixa."""

    def __init__(self, fence):
        super().__init__()
        self.fence = fence
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        self.setGridSize(QSize(GRID_W, GRID_H))
        self.setSpacing(0)
        self.setItemDelegate(TileDelegate(self))
        self.setWordWrap(True)
        self.setUniformItemSizes(True)
        self.setTextElideMode(Qt.ElideMiddle)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setFrameShape(QListWidget.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_menu)
        self.itemActivated.connect(lambda it: it.data(Qt.UserRole).open())

    def mimeData(self, items):
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(it.data(Qt.UserRole).path) for it in items])
        return mime

    def dragEnterEvent(self, ev):
        ev.acceptProposedAction() if ev.mimeData().hasUrls() else ev.ignore()

    def dragMoveEvent(self, ev):
        ev.acceptProposedAction() if ev.mimeData().hasUrls() else ev.ignore()

    def dropEvent(self, ev):
        self.fence.app.drop_into(self.fence.key, [u.toLocalFile() for u in ev.mimeData().urls()])
        ev.acceptProposedAction()

    def on_menu(self, pos):
        it = self.itemAt(pos)
        if not it:
            self.fence.app.main_menu().exec(self.mapToGlobal(pos))
            return
        item = it.data(Qt.UserRole)
        app = self.fence.app
        menu = QMenu(self)
        menu.addAction(_("Abrir"), item.open)
        menu.addAction(_("Mostrar no Gerenciador de Arquivos"), lambda: system.show_in_files(item.path))
        menu.addAction(_("Renomear…"), lambda: app.rename_item(item))
        menu.addAction(_("Copiar caminho"), lambda: QApplication.clipboard().setText(item.path))
        sub = menu.addMenu(_("Mover para a caixa"))
        for key, title, _c, _e in CATEGORIES:
            if key != item.category:
                sub.addAction(_(title), lambda k=key: app.assign_box(item.name, k))
        if item.name in app.cfg["overrides"]:
            sub.addSeparator()
            sub.addAction(_("Voltar para a caixa automática"), lambda: app.assign_box(item.name, None))
        menu.addSeparator()
        menu.addAction(_("Mover para a lixeira"), lambda: app.trash_item(item))
        menu.exec(self.mapToGlobal(pos))


class Fence(DesktopWindow):
    def __init__(self, app, key):
        _k, title, color, _e = CAT_BY_KEY[key]
        super().__init__(app, _(title))
        self.key, self.color, self.title = key, color, _(title)
        self.frame = QWidget(self)
        self.frame.setObjectName("frame")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.frame)
        lay = QVBoxLayout(self.frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.header = QWidget()
        self.header.setObjectName("header")
        self.header.setFixedHeight(HEADER_H)
        self.header.setCursor(Qt.OpenHandCursor)
        hl = QHBoxLayout(self.header)
        hl.setContentsMargins(12, 0, 10, 0)
        self.arrow = QLabel()
        self.arrow.setObjectName("arrow")
        self.title_lbl = QLabel(self.title)
        self.title_lbl.setObjectName("title")
        self.count_lbl = QLabel()
        self.count_lbl.setObjectName("count")
        hl.addWidget(self.arrow)
        hl.addWidget(self.title_lbl, 1)
        hl.addWidget(self.count_lbl)
        lay.addWidget(self.header)
        self.list = ItemList(self)
        lay.addWidget(self.list, 1)
        self.grip = Grip(self)
        self.header.mousePressEvent = self.on_header_press
        self.header.mouseDoubleClickEvent = lambda ev: self.toggle_collapse()
        self.header.mouseMoveEvent = self.mouseMoveEvent
        self.header.mouseReleaseEvent = self.mouseReleaseEvent
        self.apply_theme(app.cfg["theme"])
        self.apply_geometry()

    def geom(self):
        return self.app.cfg["boxes"].setdefault(self.key, {})

    def apply_geometry(self):
        g = self.geom()
        self.collapsed = g.get("collapsed", False)
        self.list.setVisible(not self.collapsed)
        self.grip.setVisible(not self.collapsed)
        self.arrow.setText("▸" if self.collapsed else "▾")
        self.setMinimumSize(160, HEADER_H)
        self.move(g.get("x", 40), g.get("y", 40))
        self.resize(g.get("w", 340), HEADER_H if self.collapsed else g.get("h", 220))

    def resizeEvent(self, ev):
        self.grip.move(self.width() - self.grip.width() - 4, self.height() - self.grip.height() - 2)
        super().resizeEvent(ev)

    def geometry_changed(self):
        g = self.geom()
        g.update(x=self.x(), y=self.y(), w=self.width())
        if not self.collapsed:
            g["h"] = self.height()
        self.app.schedule_save()

    def on_header_press(self, ev):
        if ev.button() == Qt.LeftButton:
            self.begin_drag(ev)

    def toggle_collapse(self):
        self.geom()["collapsed"] = not self.collapsed
        self.apply_geometry()
        self.app.schedule_save()

    def set_items(self, items):
        self.list.clear()
        for it in items:
            w = QListWidgetItem(it.icon(), it.display_name)
            w.setData(Qt.UserRole, it)
            w.setToolTip(it.display_name)
            w.setTextAlignment(Qt.AlignHCenter | Qt.AlignTop)
            self.list.addItem(w)
        self.apply_filter()

    def apply_filter(self):
        hits = 0
        for i in range(self.list.count()):
            w = self.list.item(i)
            ok = self.app.matches(w.data(Qt.UserRole))
            w.setHidden(not ok)
            hits += ok
        total = self.list.count()
        self.count_lbl.setText(f"{hits}/{total}" if self.app.query else str(total))
        self.setWindowOpacity(1.0 if hits or not self.app.query else 0.35)

    def apply_theme(self, theme):
        self.title_lbl.setText(self.title.upper() if theme == "compacto" else self.title)
        self.title_lbl.setAlignment(Qt.AlignCenter if theme == "vidro" else Qt.AlignLeft | Qt.AlignVCenter)
        self.setStyleSheet(fence_style(theme, self.color))


def fence_style(theme, color):
    c = QColor(color)
    rgba = lambda a: f"rgba({c.red()},{c.green()},{c.blue()},{a})"  # noqa: E731
    base = """
        QLabel#title { color: white; font-weight: bold; font-size: 10.5pt; }
        QLabel#arrow { color: rgba(255,255,255,0.6); font-size: 9pt; }
        QLabel#count { color: rgba(255,255,255,0.75); font-size: 8.5pt; background: rgba(255,255,255,0.10);
                       border-radius: 8px; padding: 0 7px; }
        QListWidget { background: transparent; color: white; font-size: 8pt; padding: 4px 2px 10px 4px;
                      outline: none; }
        QListWidget::item { border-radius: 8px; padding: 2px; }
        QListWidget::item:hover { background: rgba(255,255,255,0.10); }
        QListWidget::item:selected { background: rgba(120,160,255,0.30); color: white; }
        QScrollBar:vertical { background: transparent; width: 8px; }
        QScrollBar::handle:vertical { background: rgba(255,255,255,0.25); border-radius: 4px; min-height: 30px; }
        QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
    """
    if theme == "vidro":
        return base + """
            QWidget#frame { background: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.28);
                            border-radius: 14px; }
            QWidget#header { background: rgba(255,255,255,0.14); border-top-left-radius: 14px;
                             border-top-right-radius: 14px; }
            QLabel#count { background: transparent; }
        """
    if theme == "contorno":
        return base + f"""
            QWidget#frame {{ background: {rgba(0.10)}; border: 2px solid {rgba(0.75)}; border-radius: 14px; }}
            QWidget#header {{ background: transparent; }}
            QLabel#title {{ color: {QColor(color).lighter(150).name()}; }}
        """
    if theme == "compacto":
        return base + """
            QWidget#frame { background: rgba(6,7,10,0.86); border-radius: 10px; }
            QWidget#header { border-bottom: 1px solid rgba(255,255,255,0.08); }
            QLabel#title { font-size: 8pt; letter-spacing: 1.5px; color: rgba(255,255,255,0.75); }
            QLabel#count { background: transparent; color: rgba(255,255,255,0.6); }
        """
    return base + f"""
        QWidget#frame {{ background: rgba(18,20,26,0.58); border: 1px solid rgba(255,255,255,0.09);
                         border-radius: 14px; }}
        QWidget#header {{ border-bottom: 2px solid {color}; border-top-left-radius: 14px;
                          border-top-right-radius: 14px;
                          background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {rgba(0.22)},
                                                      stop:1 {rgba(0.04)}); }}
    """


# ---------------------------------------------------------------------------
# Card do relógio (visual próprio, não segue o estilo das caixas)
# ---------------------------------------------------------------------------
CARD_STYLE = """
    QWidget#card { background: rgba(18,20,26,0.55); border: 1px solid rgba(255,255,255,0.09); border-radius: 18px; }
    QLabel { color: white; }
    QLabel#time { font-size: 46pt; font-weight: 300; }
    QLabel#sec { color: rgba(255,255,255,0.55); font-size: 18pt; font-weight: 300; }
    QLabel#date { color: rgba(255,255,255,0.85); font-size: 12pt; }
    QLabel#extra { color: rgba(255,255,255,0.55); font-size: 9.5pt; }
"""


class ClockCard(DesktopWindow):
    def __init__(self, app):
        super().__init__(app, _("Relógio"))
        self.card = QWidget(self)
        self.card.setObjectName("card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.card)
        lay = QVBoxLayout(self.card)
        lay.setContentsMargins(26, 14, 26, 16)
        lay.setSpacing(2)
        row = QHBoxLayout()
        row.addStretch()
        self.time_lbl = QLabel(objectName="time")
        self.sec_lbl = QLabel(objectName="sec")
        row.addWidget(self.time_lbl)
        row.addWidget(self.sec_lbl, 0, Qt.AlignBottom)
        row.addStretch()
        lay.addLayout(row)
        self.date_lbl = QLabel(objectName="date", alignment=Qt.AlignCenter)
        self.extra_lbl = QLabel(objectName="extra", alignment=Qt.AlignCenter)
        lay.addWidget(self.date_lbl)
        lay.addWidget(self.extra_lbl)
        self.setStyleSheet(CARD_STYLE)
        g = app.cfg["clock"]
        if "x" in g:
            self.move(g["x"], g["y"])
        self.tick()
        self.timer = QTimer(self, interval=1000, timeout=self.tick)
        QTimer.singleShot(1000 - int(time.time() * 1000) % 1000, self.timer.start)

    def tick(self):
        now = datetime.now()
        self.time_lbl.setText(now.strftime("%H:%M"))
        self.sec_lbl.setVisible(self.app.cfg["show_seconds"])
        self.sec_lbl.setText(now.strftime("%S"))
        self.date_lbl.setText(i18n.long_date(now))
        h = now.hour
        greet = _("Bom dia") if 5 <= h < 12 else _("Boa tarde") if 12 <= h < 18 else _("Boa noite")
        user = self.app.first_name
        self.extra_lbl.setText(f"{greet}{', ' + user if user else ''} · {_('semana {n}', n=now.isocalendar()[1])}"
                               f" · {_('{n} itens na área de trabalho', n=self.app.item_count)}")

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.begin_drag(ev)

    def geometry_changed(self):
        self.app.cfg["clock"].update(x=self.x(), y=self.y())
        self.app.schedule_save()


# ---------------------------------------------------------------------------
# Aplicativo
# ---------------------------------------------------------------------------
class OrdoApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName(APP_NAME)
        self.setQuitOnLastWindowClosed(False)
        self.setWindowIcon(QIcon.fromTheme("ordo-desktop", QIcon(os.path.join(os.path.dirname(__file__), "..",
                                                                              "ordo-desktop.svg"))))
        self.cfg = load_config()
        i18n.set_language(self.cfg["language"])
        self.fences, self.clock = {}, None
        self.query, self.all_items, self.item_count = "", [], 0
        self.first_name = self.real_first_name()
        self.save_timer = QTimer(self, singleShot=True, interval=600, timeout=self.save_now)
        self.refresh_timer = QTimer(self, singleShot=True, interval=350, timeout=self.refresh)

    @staticmethod
    def real_first_name():
        if system.IS_WINDOWS:
            name = os.environ.get("USERNAME", "")
        else:
            import pwd
            name = (pwd.getpwuid(os.getuid()).pw_gecos or "").split(",")[0]
        return name.split(" ")[0] if name else ""

    def start(self):
        if self.cfg["hide_native"]:
            self.apply_hide_native(True)
        system.set_autostart(self.cfg["autostart"])
        self.watcher = QFileSystemWatcher([system.desktop_dir()], self)
        self.watcher.directoryChanged.connect(lambda _p: self.refresh_timer.start())
        if self.cfg["show_clock"]:
            self.toggle_clock(True)
        first_run = not self.cfg["boxes"]
        self.refresh()
        if first_run:
            self.auto_layout()

    def quit_app(self):
        try:
            self.save_now()
        except OSError as e:  # nunca deixar de devolver os ícones nativos por falha ao salvar
            print(f"ordo-desktop: não foi possível salvar a configuração: {e}", file=sys.stderr)
        self.restore_native()
        self.quit()

    # ---- persistência ----
    def schedule_save(self):
        self.save_timer.start()

    def save_now(self):
        save_config(self.cfg)

    # ---- conteúdo ----
    def refresh(self):
        items = scan_desktop(self.cfg["show_hidden"])
        self.all_items, self.item_count = items, len(items)
        groups = {}
        for it in items:
            if self.cfg["overrides"].get(it.name) in CAT_BY_KEY:
                it.category = self.cfg["overrides"][it.name]
            groups.setdefault(it.category, []).append(it)
        for key, *_rest in CATEGORIES:
            members = sorted(groups.get(key, []), key=lambda i: i.sort_key)
            fence = self.fences.get(key)
            if members:
                if not fence:
                    fence = self.fences[key] = Fence(self, key)
                    if "x" not in self.cfg["boxes"].get(key, {}):
                        self.place_new(fence)
                    fence.show()
                fence.set_items(members)
            elif fence:
                fence.close()
                fence.deleteLater()
                del self.fences[key]
        if self.clock:
            self.clock.tick()

    def matches(self, item):
        return not self.query or self.query in fold(item.display_name) or self.query in fold(item.name)

    def auto_layout(self):
        """Caixas em colunas a partir da esquerda; relógio no canto direito."""
        wa = workarea()
        margin, gap, col_w = 24, 16, 340
        x, y = wa.left() + margin, wa.top() + margin
        bottom = wa.bottom() - margin
        for key, *_rest in CATEGORIES:
            fence = self.fences.get(key)
            if not fence:
                continue
            per_row = max(1, (col_w - 30) // GRID_W)
            rows = min(max(1, -(-fence.list.count() // per_row)), 4)
            h = HEADER_H + 22 + rows * 92
            if y + h > bottom and y > wa.top() + margin:
                x += col_w + gap
                y = wa.top() + margin
            fence.geom().update(x=x, y=y, w=col_w, h=h, collapsed=False)
            fence.apply_geometry()
            y += h + gap
        if self.clock:
            self.clock.adjustSize()
            w = max(self.clock.width(), 380)
            self.clock.move(wa.right() - margin - w, wa.top() + margin)
            self.clock.geometry_changed()
        self.schedule_save()

    def place_new(self, fence):
        wa = workarea()
        fence.geom().update(x=wa.center().x() - 170, y=wa.center().y() - 110, w=340, h=220)
        fence.apply_geometry()

    # ---- ações ----
    def assign_box(self, name, key):
        """Fixa um item numa caixa escolhida (None = volta à categoria automática)."""
        auto = categorize(name, os.path.isdir(os.path.join(system.desktop_dir(), name)))
        if key is None or key == auto:
            self.cfg["overrides"].pop(name, None)
        else:
            self.cfg["overrides"][name] = key
        self.schedule_save()
        self.refresh_timer.start()

    def drop_into(self, key, paths):
        desk = os.path.normcase(os.path.abspath(system.desktop_dir()))
        for p in paths:
            if os.path.normcase(os.path.dirname(os.path.abspath(p))) == desk:
                self.assign_box(os.path.basename(p), key)  # já está na área de trabalho: só troca de caixa
                continue
            target = os.path.join(system.desktop_dir(), os.path.basename(p))
            if os.path.exists(target):
                error(_("Já existe “{name}” na área de trabalho.", name=os.path.basename(p)))
                continue
            try:
                shutil.move(p, target)
            except OSError as e:
                error(_("Não foi possível mover “{name}”.", name=os.path.basename(p)), str(e))

    def trash_item(self, item):
        err = system.move_to_trash(item.path)
        if err:
            error(_("Não foi possível mover “{name}” para a lixeira.", name=item.display_name), err)

    def rename_item(self, item):
        new, ok = QInputDialog.getText(None, _("Renomear"), "", text=item.name)
        new = new.strip()
        if ok and new and new != item.name:
            try:
                os.rename(item.path, os.path.join(os.path.dirname(item.path), new))
                if item.name in self.cfg["overrides"]:  # caixa escolhida acompanha o novo nome
                    self.cfg["overrides"][new] = self.cfg["overrides"].pop(item.name)
                    self.schedule_save()
            except OSError as e:
                error(_("Não foi possível renomear."), str(e))

    def set_collapsed_all(self, collapsed):
        for f in self.fences.values():
            f.geom()["collapsed"] = collapsed
            f.apply_geometry()
        self.schedule_save()

    def toggle_clock(self, show):
        self.cfg["show_clock"] = show
        if show and not self.clock:
            self.clock = ClockCard(self)
            if "x" not in self.cfg["clock"]:
                self.clock.adjustSize()
                wa = workarea()
                self.clock.move(wa.right() - 24 - max(self.clock.width(), 380), wa.top() + 24)
            self.clock.show()
        elif not show and self.clock:
            self.clock.close()
            self.clock = None
        self.schedule_save()

    def apply_hide_native(self, hide):
        self.cfg["hide_native"] = hide
        if hide:
            done = system.hide_native_icons()
            self.cfg["native_disabled"] = sorted(set(self.cfg["native_disabled"]) | set(done))
            self.save_now()  # grava antes: se o app travar, a próxima saída devolve os ícones
        else:
            self.restore_native()
        self.schedule_save()

    def restore_native(self):
        if self.cfg["native_disabled"]:
            system.restore_native_icons(self.cfg["native_disabled"])
            self.cfg["native_disabled"] = []
            try:
                self.save_now()
            except OSError:
                pass

    def set_theme(self, theme):
        self.cfg["theme"] = theme
        for f in self.fences.values():
            f.apply_theme(theme)
        self.schedule_save()

    def set_language(self, choice):
        """Troca o idioma e reabre o Ordo para redesenhar tudo já traduzido."""
        if choice == self.cfg["language"]:
            return
        self.cfg["language"] = choice
        self.save_now()
        self.restore_native()  # a nova instância volta a ocultá-los
        if getattr(sys, "frozen", False):  # executável empacotado
            os.execv(sys.executable, sys.argv)
        pkg_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.environ["PYTHONPATH"] = pkg_parent + os.pathsep + os.environ.get("PYTHONPATH", "")
        os.execv(sys.executable, [sys.executable, "-m", "ordo"] + sys.argv[1:])

    def set_option(self, key, on):
        self.cfg[key] = on
        if key == "show_hidden":
            self.refresh()
        if key == "autostart":
            system.set_autostart(on)
        if key == "show_seconds" and self.clock:
            self.clock.tick()
            self.clock.adjustSize()
        self.schedule_save()

    # ---- menu geral (botão direito) ----
    def main_menu(self):
        menu = QMenu()
        menu.addAction(_("Reorganizar automaticamente"), self.auto_layout)
        menu.addAction(_("Recolher todas"), lambda: self.set_collapsed_all(True))
        menu.addAction(_("Expandir todas"), lambda: self.set_collapsed_all(False))
        menu.addAction(_("Abrir pasta da Área de Trabalho"), lambda: system.open_path(system.desktop_dir()))
        menu.addSeparator()
        for label, options, current, setter in (
                (_("Estilo das caixas"), THEMES, self.cfg["theme"], self.set_theme),
                (_("Idioma"), LANGUAGES, self.cfg["language"], self.set_language)):
            sub = menu.addMenu(label)
            group = QActionGroup(sub)
            for key, name in options.items():
                act = QAction(_(name) if options is THEMES or key == "auto" else name, sub, checkable=True,
                              checked=key == current)
                act.triggered.connect(lambda _c=False, k=key, f=setter: f(k))
                group.addAction(act)
                sub.addAction(act)
        menu.addSeparator()

        def check(label, key, cb=None):
            act = QAction(label, menu, checkable=True, checked=self.cfg[key])
            act.toggled.connect(cb or (lambda on, k=key: self.set_option(k, on)))
            menu.addAction(act)

        check(_("Mostrar relógio"), "show_clock", self.toggle_clock)
        check(_("Mostrar segundos"), "show_seconds")
        check(_("Ocultar ícones nativos da área de trabalho"), "hide_native", self.apply_hide_native)
        check(_("Mostrar arquivos ocultos"), "show_hidden")
        check(_("Iniciar com o sistema"), "autostart")
        menu.addSeparator()
        menu.addAction(_("Sair"), self.quit_app)
        self._menu = menu  # mantém vivo enquanto aberto
        return menu


MENU_STYLE = """
    QMenu { background: #1f2229; color: #e8eaf0; border: 1px solid #343846; border-radius: 8px; padding: 4px; }
    QMenu::item { padding: 6px 22px 6px 22px; border-radius: 5px; }
    QMenu::item:selected { background: #3a4060; }
    QMenu::separator { height: 1px; background: #343846; margin: 4px 8px; }
    QMenu::indicator { width: 14px; height: 14px; left: 4px; }
    QToolTip { background: #1f2229; color: #e8eaf0; border: 1px solid #343846; }
"""


def main():
    app = OrdoApp(sys.argv)
    # Uma instância só: se já existe, apenas sai (a primeira continua cuidando do desktop).
    probe = QLocalSocket()
    probe.connectToServer(SERVER_NAME)
    if probe.waitForConnected(300):
        return 0
    QLocalServer.removeServer(SERVER_NAME)
    server = QLocalServer(app)
    server.listen(SERVER_NAME)
    app.setStyleSheet(MENU_STYLE)
    app.setFont(QFont(app.font().family(), 10))
    # Logout/kill também devolvem os ícones nativos, não só o menu "Sair".
    for sig in (signal.SIGINT, signal.SIGTERM) + ((signal.SIGHUP,) if hasattr(signal, "SIGHUP") else ()):
        signal.signal(sig, lambda *_a: app.quit_app())
    tick = QTimer(app, interval=500, timeout=lambda: None)  # deixa o Python tratar sinais durante o loop do Qt
    tick.start()
    app.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
