"""Ordo Desktop em Qt (PySide6): caixas automáticas, relógio e menus — Windows e Linux."""
import json
import os
import shutil
import signal
import sys
import time
from datetime import datetime

if sys.platform.startswith("linux") and os.environ.get("XDG_SESSION_TYPE") == "wayland":
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")  # posicionar janelas exige X11 (XWayland)

from PySide6.QtCore import QFileInfo, QFileSystemWatcher, QMimeData, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QColor, QFont, QIcon, QImageReader, QPainter, QPixmap
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFileIconProvider, QHBoxLayout, QInputDialog,
                               QLabel, QListView, QListWidget, QListWidgetItem, QMenu, QStyle,
                               QStyledItemDelegate, QVBoxLayout, QWidget)

from . import i18n, system
from .cards import CARD_W, MarketCard, NewsCard
from .clock import ClockCard
from .notes import StickyNote
from .widgets import DesktopWindow, Grip, error, workarea
from .catalog import APP_NAME, CAT_BY_KEY, CATEGORIES, HEADER_H, ICON_SIZE, NOTE_COLORS, THEMES, categorize
from .config import load_config, save_config
from .i18n import LANGUAGES, _, fold

import getpass  # noqa: E402

SERVER_NAME = f"ordo-desktop-{getpass.getuser()}"  # uma instância por usuário
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
    items = []
    for folder in system.desktop_dirs():
        try:
            names = os.listdir(folder)
        except OSError:
            continue
        for n in names:
            path = os.path.join(folder, n)
            if show_hidden or not system.is_hidden(path):
                items.append(DesktopItem(path))
    return items


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
        self.fences, self.clock, self.notes, self.cards = {}, None, [], {}
        self.stack_news = self.cards_below_clock = False
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
        try:
            system.set_autostart(self.cfg["autostart"])
        except OSError as e:  # sem permissão no registro/pasta: o resto do app funciona igual
            log_error(f"iniciar com o sistema: {e}")
        self.watcher = QFileSystemWatcher(system.desktop_dirs(), self)
        self.watcher.directoryChanged.connect(lambda _p: self.refresh_timer.start())
        first_run = not self.cfg["boxes"]
        wa = workarea()
        if first_run and wa.width() - 48 - 380 - 16 - CARD_W - 16 < 340:
            # Tela pequena: relógio + caixas já ocupam tudo; mercado e notícias ficam no menu para ligar.
            self.cfg["show_market"] = self.cfg["show_news"] = False
        if self.cfg["show_clock"]:
            self.toggle_clock(True)
        for data in self.cfg["notes"]:
            self.show_note(data)
        for key in ("market", "news"):
            if self.cfg[f"show_{key}"]:
                self.toggle_card(key, True)
        self.refresh()
        if first_run:
            self.auto_layout()
        # Por último: se algo acima falhar, os ícones nativos continuam onde estavam.
        if self.cfg["hide_native"]:
            self.apply_hide_native(True)

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
        if self.query:  # arquivo novo/renomeado durante uma busca: reaplica o filtro
            self.set_query(self.query)

    def matches(self, item):
        return not self.query or self.query in fold(item.display_name) or self.query in fold(item.name)

    def set_query(self, text):
        self.query = fold(text.strip())
        for f in self.fences.values():
            f.apply_filter()
        found = sorted((i for i in self.all_items if self.query and self.matches(i)),
                       key=lambda i: (not fold(i.display_name).startswith(self.query), i.sort_key))
        if self.clock:
            self.clock.show_results(self.query, found)

    def auto_layout(self):
        """Relógio no canto direito; mercado e notícias ao lado dele (ou embaixo, em telas estreitas);
        caixas em colunas a partir da esquerda, no espaço que sobra."""
        wa = workarea()
        margin, gap, col_w = 24, 16, 340
        top, bottom = wa.top() + margin, wa.bottom() - margin
        market, news = self.cards.get("market"), self.cards.get("news")
        right = wa.right() - margin
        clock_w = 0
        if self.clock:
            self.clock.adjustSize()
            clock_w = max(self.clock.width(), 380)
            right -= clock_w
            self.clock.move(right, top)
            self.clock.geometry_changed()
        # Cards ao lado do relógio só se ainda couberem duas colunas de caixas; senão, embaixo do relógio.
        has_cards = bool(market or news)
        side = has_cards and wa.width() - 2 * margin - clock_w - gap - CARD_W - gap >= col_w
        if has_cards and not side and self.clock:
            card_x, card_w = right, clock_w
            y = self.clock.y() + self.clock.height() + gap
            fences_right = right - gap
        else:
            card_w = CARD_W
            card_x = right - gap - CARD_W if self.clock else right - CARD_W
            y = top
            fences_right = (card_x if has_cards else right) - gap
        self.cfg["card_width"] = card_w
        if market:
            g = market.geom()
            g.pop("w", None)
            g.pop("h", None)
            g.update(x=card_x, y=y)
            market.move(card_x, y)
            market.fit()
            y += market.height() + gap
        if news:
            news.geom().update(x=card_x, y=y, w=card_w, h=max(200, bottom - y))
            news.move(card_x, y)
            news.fit()
        self.stack_news = bool(market and news)
        self.cards_below_clock = has_cards and not side and bool(self.clock)
        # Caixas: colunas da esquerda até onde começam o relógio/cards.
        x, y = wa.left() + margin, top
        cols = max(1, (fences_right - x + gap) // (col_w + gap))
        col = 0
        for key, *_rest in CATEGORIES:
            fence = self.fences.get(key)
            if not fence:
                continue
            per_row = max(1, (col_w - 30) // GRID_W)
            rows = min(max(1, -(-fence.list.count() // per_row)), 4)
            h = HEADER_H + 22 + rows * 92
            if y + h > bottom and y > top and col + 1 < cols:  # coluna cheia: passa para a próxima
                col += 1
                x += col_w + gap
                y = top
            # Sem mais colunas e sem espaço: a caixa fica recolhida (só o título); clique duplo expande.
            collapsed = y + h > bottom and col + 1 >= cols and y > top
            fence.geom().update(x=x, y=y, w=col_w, h=h, collapsed=collapsed)
            fence.apply_geometry()
            y += fence.height() + (8 if collapsed else gap)
        self.schedule_save()

    def restack_cards(self):
        """Depois do Reorganizar, mantém a pilha relógio → mercado → notícias quando algo muda de altura
        (o clima e as cotações chegam depois e mudam o tamanho dos cards)."""
        market, news = self.cards.get("market"), self.cards.get("news")
        bottom = workarea().bottom() - 24
        y = None
        if self.cards_below_clock and self.clock:
            y = self.clock.y() + self.clock.height() + 16
            for card in (market, news):
                if card:
                    card.geom().update(x=card.x(), y=y)
                    card.move(card.x(), y)
                    if card is news:
                        news.geom().update(h=max(200, bottom - y))
                        news.fit()
                    y += card.height() + 16
        elif self.stack_news and market and news:
            y = market.y() + market.height() + 16
            news.geom().update(x=news.x(), y=y, h=max(200, bottom - y))
            news.move(news.x(), y)
            news.fit()
        if y is not None:
            self.schedule_save()

    def cards_moved_by_user(self):
        self.stack_news = self.cards_below_clock = False  # o usuário posicionou à mão: respeita

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
        desks = {os.path.normcase(os.path.abspath(d)) for d in system.desktop_dirs()}
        for p in paths:
            if os.path.normcase(os.path.dirname(os.path.abspath(p))) in desks:
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

    # ---- notas ----
    def show_note(self, data):
        note = StickyNote(self, data)
        self.notes.append(note)
        note.show()
        return note

    def new_note(self, near=None):
        wa = workarea()
        if near:
            x, y = near.x() + 28, near.y() + 28
        else:
            x, y = wa.center().x() - 130 + 24 * (len(self.cfg["notes"]) % 6), wa.top() + wa.height() // 3
        colors = list(NOTE_COLORS)
        data = {"id": int(time.time() * 1000) % 10**10, "title": "", "text": "",
                "color": colors[len(self.cfg["notes"]) % len(colors)],
                "created": datetime.now().strftime("%d/%m/%Y"), "x": x, "y": y, "w": 260, "h": 220}
        self.cfg["notes"].append(data)
        self.schedule_save()
        note = self.show_note(data)
        note.activateWindow()
        note.title.setFocus()

    def remove_note(self, note):
        self.cfg["notes"] = [n for n in self.cfg["notes"] if n is not note.data]
        self.notes.remove(note)
        note.close()
        note.deleteLater()
        self.schedule_save()

    # ---- cards de mercado e notícias ----
    def toggle_card(self, key, show):
        self.cfg[f"show_{key}"] = show
        card = self.cards.get(key)
        if show and not card:
            card = self.cards[key] = (MarketCard if key == "market" else NewsCard)(self)
            if "x" not in card.geom():
                wa = workarea()
                y = wa.top() + 24 + (0 if key == "market" else 500)
                card.move(wa.right() - 24 - 405 - 16 - CARD_W, y)
            card.fit()
            card.show()
        elif not show and card:
            card.close()
            card.deleteLater()
            del self.cards[key]
        self.schedule_save()

    def set_gadgets(self, on):
        self.cfg["show_gadgets"] = on
        if self.clock:
            self.clock.set_gadgets(on)
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
        for card in self.cards.values():  # o card do relógio mantém o visual próprio
            card.apply_theme(theme)
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
    @staticmethod
    def make_menu():
        return QMenu()

    def main_menu(self):
        menu = QMenu()
        menu.addAction(_("Reorganizar automaticamente"), self.auto_layout)
        menu.addAction(_("Nova nota"), self.new_note)
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
        check(_("Mostrar gadgets abaixo do relógio"), "show_gadgets", self.set_gadgets)
        check(_("Mostrar mercado financeiro"), "show_market", lambda on: self.toggle_card("market", on))
        check(_("Mostrar notícias"), "show_news", lambda on: self.toggle_card("news", on))
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


def log_error(text):
    """Grava erros em ordo-error.log, na pasta de configuração (o app não tem console no Windows)."""
    try:
        os.makedirs(system.config_dir(), exist_ok=True)
        with open(os.path.join(system.config_dir(), "ordo-error.log"), "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {text}\n")
    except OSError:
        pass
    print(text, file=sys.stderr)


def install_error_handler(app):
    """Erro inesperado não derruba o Ordo (nem deixa a área de trabalho sem ícones): registra e segue."""
    import traceback

    def hook(kind, value, tb):
        log_error("".join(traceback.format_exception(kind, value, tb)))

    sys.excepthook = hook


def selftest(app, spec):
    """ORDO_SELFTEST="arquivo.png;segundos": captura a tela, grava um diagnóstico e fecha (usado no CI)."""
    path, _sep, secs = spec.partition(";")

    def run():
        QApplication.primaryScreen().grabWindow(0).save(path)
        info = {"platform": sys.platform, "desktop_dirs": system.desktop_dirs(), "items": app.item_count,
                "boxes": sorted(app.fences), "cards": sorted(app.cards), "notes": len(app.notes),
                "native_hidden": app.cfg["native_disabled"], "clock": bool(app.clock),
                "windows": [w.windowTitle() for w in app.topLevelWidgets() if w.isVisible()]}
        with open(os.path.splitext(path)[0] + ".json", "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        app.quit_app()

    QTimer.singleShot(int(float(secs or 20) * 1000), run)


def main():
    # "ordo-desktop --quit" fecha a instância aberta com segurança (devolve os ícones nativos).
    # O desinstalador do Windows usa isso em vez de matar o processo.
    if "--quit" in sys.argv:
        from PySide6.QtCore import QCoreApplication
        app = QCoreApplication(sys.argv)  # sem tela: o desinstalador roda fora da sessão gráfica
        sock = QLocalSocket()
        sock.connectToServer(SERVER_NAME)
        if sock.waitForConnected(1000):
            sock.write(b"quit")
            sock.flush()
            sock.waitForBytesWritten(1000)
            sock.waitForDisconnected(5000)
        return 0
    app = OrdoApp(sys.argv)
    # Uma instância só: se já existe, apenas sai (a primeira continua cuidando do desktop).
    probe = QLocalSocket()
    probe.connectToServer(SERVER_NAME)
    if probe.waitForConnected(300):
        return 0
    QLocalServer.removeServer(SERVER_NAME)
    server = QLocalServer(app)
    server.listen(SERVER_NAME)

    def on_client():
        conn = server.nextPendingConnection()
        conn.readyRead.connect(lambda: conn.readAll().data().strip() == b"quit" and app.quit_app())

    server.newConnection.connect(on_client)
    if os.environ.get("ORDO_SELFTEST"):
        selftest(app, os.environ["ORDO_SELFTEST"])
    app.setStyleSheet(MENU_STYLE)
    app.setFont(QFont(app.font().family(), 10))
    # Logout/kill também devolvem os ícones nativos, não só o menu "Sair".
    for sig in (signal.SIGINT, signal.SIGTERM) + ((signal.SIGHUP,) if hasattr(signal, "SIGHUP") else ()):
        signal.signal(sig, lambda *_a: app.quit_app())
    tick = QTimer(app, interval=500, timeout=lambda: None)  # deixa o Python tratar sinais durante o loop do Qt
    tick.start()
    install_error_handler(app)
    try:
        app.start()
    except Exception:  # noqa: BLE001 — falha ao abrir: registra, devolve os ícones e segue com o que abriu
        sys.excepthook(*sys.exc_info())
        app.restore_native()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
