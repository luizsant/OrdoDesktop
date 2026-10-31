"""Cards extras: tarefas, favoritos, área de transferência, relógios mundiais, conversor, música e imagem do dia."""
import json
import os
import time
import urllib.parse
from datetime import date, datetime

from PySide6.QtCore import QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
                               QHBoxLayout, QLabel, QLineEdit, QListView, QListWidget, QListWidgetItem, QMenu,
                               QPlainTextEdit, QToolButton, QVBoxLayout, QWidget)

from . import data, i18n, system
from .cards import InfoCard, section
from .i18n import _, fmt_num
from .widgets import run_async


def _buttons(dlg, lay):
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    bb.button(QDialogButtonBox.Ok).setText(_("Salvar"))
    bb.button(QDialogButtonBox.Cancel).setText(_("Cancelar"))
    bb.accepted.connect(dlg.accept)
    bb.rejected.connect(dlg.reject)
    lay.addWidget(bb)


# ---------------------------------------------------------------------------
# Tarefas
# ---------------------------------------------------------------------------
class TodoCard(InfoCard):
    EXTRA_H = 108  # + campo de nova tarefa
    def __init__(self, app):
        super().__init__(app, "todo", "Tarefas")
        self.app.cfg.setdefault("todos", [])
        self.entry = QLineEdit(placeholderText=_("Nova tarefa — Enter para adicionar"))
        self.entry.returnPressed.connect(self.add)
        self.card.layout().insertWidget(1, self.entry)
        self.build()

    def build(self):
        self.clear_body()
        todos = self.app.cfg["todos"]
        pending = sum(not t["done"] for t in todos)
        self.meta.setText(_("{n} pendentes", n=pending) if todos else "")
        if not todos:
            self.body.addWidget(QLabel(_("Nada por aqui. Escreva acima e tecle Enter."), objectName="muted"))
        for t in sorted(todos, key=lambda t: t["done"]):  # pendentes primeiro, na ordem em que entraram
            row = QWidget(objectName="row")
            hl = QHBoxLayout(row)
            hl.setContentsMargins(4, 2, 2, 2)
            box = QCheckBox()
            box.setChecked(t["done"])
            box.toggled.connect(lambda on, t=t: self.set_done(t, on))
            lbl = QLabel(t["text"], wordWrap=True, objectName="done" if t["done"] else "")
            if t["done"]:
                lbl.setStyleSheet("color: rgba(255,255,255,0.40); text-decoration: line-through;")
            rm = QToolButton(text="✕", objectName="flat", toolTip=_("Remover"))
            rm.clicked.connect(lambda _c=False, t=t: self.remove(t))
            hl.addWidget(box)
            hl.addWidget(lbl, 1)
            hl.addWidget(rm)
            self.body.addWidget(row)
        QTimer.singleShot(0, self.fit)

    def add(self):
        text = self.entry.text().strip()
        if text:
            self.app.cfg["todos"].append({"text": text, "done": False, "id": int(time.time() * 1000)})
            self.entry.clear()
            self.app.schedule_save()
            self.build()

    def set_done(self, t, on):
        t["done"] = on
        self.app.schedule_save()
        QTimer.singleShot(0, self.build)

    def remove(self, t):
        self.app.cfg["todos"] = [x for x in self.app.cfg["todos"] if x is not t]
        self.app.schedule_save()
        self.build()

    def extra_menu(self, menu):
        menu.addAction(_("Limpar concluídas"), self.clear_done)

    def clear_done(self):
        self.app.cfg["todos"] = [t for t in self.app.cfg["todos"] if not t["done"]]
        self.app.schedule_save()
        self.build()


# ---------------------------------------------------------------------------
# Favoritos (atalhos para pastas, arquivos e aplicativos; não move nada)
# ---------------------------------------------------------------------------
class FavList(QListWidget):
    def __init__(self, card):
        super().__init__()
        self.card = card
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setIconSize(QSize(40, 40))
        self.setGridSize(QSize(80, 78))
        self.setWordWrap(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DropOnly)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_menu)
        self.itemActivated.connect(lambda it: system.open_path(it.data(Qt.UserRole)))

    def dragEnterEvent(self, ev):
        ev.acceptProposedAction() if ev.mimeData().hasUrls() else ev.ignore()

    def dragMoveEvent(self, ev):
        ev.acceptProposedAction() if ev.mimeData().hasUrls() else ev.ignore()

    def dropEvent(self, ev):
        self.card.add_paths([u.toLocalFile() for u in ev.mimeData().urls() if u.isLocalFile()])
        ev.setDropAction(Qt.LinkAction)  # só cria o atalho: o arquivo continua onde está
        ev.accept()

    def on_menu(self, pos):
        it = self.itemAt(pos)
        menu = QMenu(self)
        if it:
            path = it.data(Qt.UserRole)
            menu.addAction(_("Abrir"), lambda: system.open_path(path))
            menu.addAction(_("Mostrar no Gerenciador de Arquivos"), lambda: system.show_in_files(path))
            menu.addAction(_("Remover dos favoritos"), lambda: self.card.remove(path))
            menu.addSeparator()
        self.card.extra_menu(menu)
        menu.exec(self.mapToGlobal(pos))


class FavoritesCard(InfoCard):
    def __init__(self, app):
        super().__init__(app, "favorites", "Favoritos")
        self.meta.setText("")
        self.app.cfg.setdefault("favorites", [])
        self.list = FavList(self)
        self.body.addWidget(self.list)
        self.build()

    def build(self):
        from .app import DesktopItem  # importado aqui para evitar import circular
        self.list.clear()
        for path in self.app.cfg["favorites"]:
            if not os.path.exists(path):
                continue
            item = DesktopItem(path)
            w = QListWidgetItem(item.icon(40), item.display_name)
            w.setData(Qt.UserRole, path)
            w.setToolTip(path)
            self.list.addItem(w)
        empty = not self.list.count()
        self.list.setVisible(not empty)
        if empty and not getattr(self, "hint", None):
            self.hint = QLabel(_("Arraste para cá pastas, arquivos ou aplicativos (o original continua onde "
                                 "está), ou use o botão direito → Adicionar."), objectName="muted", wordWrap=True)
            self.body.addWidget(self.hint)
        if getattr(self, "hint", None):
            self.hint.setVisible(empty)
        rows = max(1, -(-self.list.count() // 4))
        self.list.setFixedHeight(rows * 80 + 6)
        QTimer.singleShot(0, self.fit)

    def add_paths(self, paths):
        favs = self.app.cfg["favorites"]
        favs += [p for p in paths if p and p not in favs]
        self.app.schedule_save()
        self.build()

    def remove(self, path):
        self.app.cfg["favorites"] = [p for p in self.app.cfg["favorites"] if p != path]
        self.app.schedule_save()
        self.build()

    def extra_menu(self, menu):
        menu.addAction(_("Adicionar pasta…"), lambda: self.add_paths(
            [QFileDialog.getExistingDirectory(None, _("Adicionar pasta"), os.path.expanduser("~"))]))
        menu.addAction(_("Adicionar arquivo…"), lambda: self.add_paths(
            QFileDialog.getOpenFileNames(None, _("Adicionar arquivo"), os.path.expanduser("~"))[0]))
        if system.IS_LINUX:
            menu.addAction(_("Adicionar aplicativo…"), lambda: self.add_paths(QFileDialog.getOpenFileNames(
                None, _("Adicionar aplicativo"), "/usr/share/applications", "*.desktop")[0]))

    def contextMenuEvent(self, ev):
        menu = self.app.make_menu()
        self.extra_menu(menu)
        menu.addSeparator()
        menu.addAction(_("Ocultar este card"), self.hide_card)
        menu.addMenu(self.app.main_menu()).setText(_("Configurações"))
        menu.exec(ev.globalPos())


# ---------------------------------------------------------------------------
# Área de transferência (só na memória: nada é gravado em disco)
# ---------------------------------------------------------------------------
class ClipboardCard(InfoCard):
    MAX = 12

    def __init__(self, app):
        super().__init__(app, "clipboard", "Área de transferência")
        self.meta.setText(_("não fica salvo"))
        self.meta.setToolTip(_("O histórico fica só na memória e some ao fechar o Ordo."))
        self.history = []
        self.cb = QApplication.clipboard()
        self.cb.dataChanged.connect(self.on_change)
        self.on_change()

    def on_change(self):
        text = (self.cb.text() or "").strip()
        if text and (not self.history or self.history[0] != text):
            self.history = [text] + [h for h in self.history if h != text][: self.MAX - 1]
            self.build()
        elif not self.history:
            self.build()

    def build(self):
        self.clear_body()
        if not self.history:
            self.body.addWidget(QLabel(_("O que você copiar aparece aqui."), objectName="muted"))
        for i, text in enumerate(self.history):
            row = QWidget(objectName="row")
            row.setCursor(Qt.PointingHandCursor)
            row.setToolTip(text[:1000])
            hl = QHBoxLayout(row)
            hl.setContentsMargins(6, 4, 2, 4)
            lbl = QLabel(" ".join(text.split())[:140], wordWrap=True)
            if i == 0:
                lbl.setStyleSheet("font-weight: bold;")
            hl.addWidget(lbl, 1)
            rm = QToolButton(text="✕", objectName="flat", toolTip=_("Remover"))
            rm.clicked.connect(lambda _c=False, t=text: self.remove(t))
            hl.addWidget(rm)
            row.mousePressEvent = lambda ev, t=text: ev.button() == Qt.LeftButton and self.copy(t)
            self.body.addWidget(row)
        QTimer.singleShot(0, self.fit)

    def copy(self, text):
        self.cb.setText(text)
        self.meta.setText(_("copiado!"))
        QTimer.singleShot(1500, lambda: self.meta.setText(_("não fica salvo")))

    def remove(self, text):
        self.history = [h for h in self.history if h != text]
        self.build()

    def extra_menu(self, menu):
        menu.addAction(_("Limpar histórico"), self.clear)

    def clear(self):
        self.history = []
        self.build()


# ---------------------------------------------------------------------------
# Relógios mundiais
# ---------------------------------------------------------------------------
DEFAULT_ZONES = ["America/Sao_Paulo", "Europe/Lisbon", "America/New_York", "Europe/London", "Asia/Tokyo"]


def zone_name(tz):
    return tz.rsplit("/", 1)[-1].replace("_", " ")


class WorldClockCard(InfoCard):
    def __init__(self, app):
        super().__init__(app, "worldclock", "Relógios mundiais")
        self.meta.setText("")
        self.app.cfg.setdefault("world_clocks", list(DEFAULT_ZONES))
        self.labels = []
        self.build()
        QTimer(self, interval=15000, timeout=self.tick).start()

    def build(self):
        from zoneinfo import ZoneInfo
        self.clear_body()
        self.labels = []
        for tz in self.app.cfg["world_clocks"]:
            try:
                zone = ZoneInfo(tz)
            except Exception:  # fuso inválido digitado à mão
                continue
            row = QHBoxLayout()
            names = QVBoxLayout()
            names.setSpacing(0)
            names.addWidget(QLabel(zone_name(tz), objectName="strong"))
            sub = QLabel(objectName="muted")
            names.addWidget(sub)
            row.addLayout(names, 1)
            t = QLabel(objectName="big")
            row.addWidget(t)
            self.body.addLayout(row)
            self.labels.append((zone, t, sub))
        self.tick()
        QTimer.singleShot(0, self.fit)

    def tick(self):
        local = datetime.now().astimezone()
        for zone, t, sub in self.labels:
            now = datetime.now(zone)
            t.setText(now.strftime("%H:%M"))
            diff = (now.utcoffset() - local.utcoffset()).total_seconds() / 3600
            day = (now.date() - local.date()).days
            parts = [_("mesmo horário") if diff == 0 else f"{diff:+g} h"]
            if day:
                parts.append(_("amanhã") if day > 0 else _("ontem"))
            sub.setText(" · ".join(parts))

    def extra_menu(self, menu):
        menu.addAction(_("Escolher cidades…"), self.edit)

    def edit(self):
        from zoneinfo import available_timezones
        dlg = QDialog(self)
        dlg.setWindowTitle(_("Relógios mundiais"))
        dlg.resize(380, 380)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(_("Um fuso por linha (ex.: America/Belem, Europe/Paris). Escolha abaixo para "
                               "acrescentar."), wordWrap=True))
        edit = QPlainTextEdit("\n".join(self.app.cfg["world_clocks"]))
        lay.addWidget(edit, 1)
        pick = QComboBox(editable=True)
        pick.addItems(sorted(z for z in available_timezones() if "/" in z and not z.startswith("Etc")))
        pick.setCurrentIndex(-1)
        pick.activated.connect(lambda _i: edit.appendPlainText(pick.currentText()))
        lay.addWidget(pick)
        _buttons(dlg, lay)
        if dlg.exec():
            self.app.cfg["world_clocks"] = [x.strip() for x in edit.toPlainText().splitlines() if x.strip()]
            self.app.schedule_save()
            self.build()


# ---------------------------------------------------------------------------
# Conversor (moedas com a cotação do dia + unidades)
# ---------------------------------------------------------------------------
CURRENCIES = ["BRL", "USD", "EUR", "GBP", "ARS", "JPY", "CNY", "CHF", "CAD", "BTC"]
UNITS = {
    "Comprimento": {"m": 1, "km": 1000, "cm": 0.01, "mm": 0.001, "mi": 1609.344, "ft": 0.3048, "in": 0.0254},
    "Massa": {"kg": 1, "g": 0.001, "t": 1000, "lb": 0.45359237, "oz": 0.028349523125},
    "Área": {"m²": 1, "km²": 1e6, "ha": 1e4, "alqueire (SP)": 24200, "alqueire (MG/GO)": 48400, "acre": 4046.8564224},
    "Volume": {"L": 1, "mL": 0.001, "m³": 1000, "gal (EUA)": 3.785411784},
    "Dados": {"MB": 1, "GB": 1000, "TB": 1e6, "KB": 0.001},
    "Temperatura": {"°C": None, "°F": None, "K": None},
}


def convert_temp(v, a, b):
    c = v if a == "°C" else (v - 32) * 5 / 9 if a == "°F" else v - 273.15
    return c if b == "°C" else c * 9 / 5 + 32 if b == "°F" else c + 273.15


class ConverterCard(InfoCard):
    def __init__(self, app):
        super().__init__(app, "converter", "Conversor")
        self.rates = {"BRL": 1.0}
        self.meta.setText(_("carregando…"))
        # moedas
        self.body.addWidget(section(_("MOEDAS")))
        row = QHBoxLayout()
        self.amount = QLineEdit("1")
        self.cur_from, self.cur_to = QComboBox(), QComboBox()
        self.cur_from.addItems(CURRENCIES)
        self.cur_to.addItems(CURRENCIES)
        self.cur_from.setCurrentText("USD")
        swap = QToolButton(text="⇄", objectName="flat", toolTip=_("Inverter"))
        swap.clicked.connect(self.swap)
        for w in (self.amount, self.cur_from, swap, self.cur_to):
            row.addWidget(w)
        self.body.addLayout(row)
        self.cur_out = QLabel(objectName="big")
        self.body.addWidget(self.cur_out)
        # unidades
        self.body.addWidget(section(_("UNIDADES")))
        self.kind = QComboBox()
        self.kind.addItems([_(k) for k in UNITS])
        self.body.addWidget(self.kind)
        row = QHBoxLayout()
        self.u_amount = QLineEdit("1")
        self.u_from, self.u_to = QComboBox(), QComboBox()
        for w in (self.u_amount, self.u_from, self.u_to):
            row.addWidget(w)
        self.body.addLayout(row)
        self.u_out = QLabel(objectName="big")
        self.body.addWidget(self.u_out)
        for w in (self.amount.textChanged, self.cur_from.currentIndexChanged, self.cur_to.currentIndexChanged):
            w.connect(self.update_currency)
        for w in (self.u_amount.textChanged, self.u_from.currentIndexChanged, self.u_to.currentIndexChanged):
            w.connect(self.update_units)
        self.kind.currentIndexChanged.connect(self.fill_units)
        self.fill_units()
        self.refresh()
        QTimer(self, interval=30 * 60 * 1000, timeout=self.refresh).start()

    @staticmethod
    def number(text):
        try:
            return float(text.replace(".", "").replace(",", ".") if i18n.LANG != "en" and "," in text
                         else text.replace(",", ""))
        except ValueError:
            return None

    def refresh(self):
        pairs = ",".join(f"{c}-BRL" for c in CURRENCIES if c != "BRL")
        run_async(lambda: data.http_json(f"https://economia.awesomeapi.com.br/json/last/{pairs}"), self.got_rates)

    def got_rates(self, res, err):
        if err or not res:
            self.meta.setText(_("sem conexão"))
            return
        for v in res.values():
            self.rates[v["code"]] = float(v["bid"])
        self.meta.setText(_("atualizado {t}", t=time.strftime("%H:%M")))
        self.update_currency()

    def swap(self):
        a, b = self.cur_from.currentText(), self.cur_to.currentText()
        self.cur_from.setCurrentText(b)
        self.cur_to.setCurrentText(a)

    def update_currency(self):
        v = self.number(self.amount.text())
        a, b = self.cur_from.currentText(), self.cur_to.currentText()
        if v is None or a not in self.rates or b not in self.rates:
            self.cur_out.setText("—")
            return
        res = v * self.rates[a] / self.rates[b]
        self.cur_out.setText(f"{fmt_num(res, 8 if b == 'BTC' else 2)} {b}")

    def fill_units(self):
        units = list(UNITS)[self.kind.currentIndex()]
        for combo, idx in ((self.u_from, 0), (self.u_to, 1)):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(list(UNITS[units]))
            combo.setCurrentIndex(min(idx, combo.count() - 1))
            combo.blockSignals(False)
        self.update_units()

    def update_units(self):
        units = UNITS[list(UNITS)[self.kind.currentIndex()]]
        v = self.number(self.u_amount.text())
        a, b = self.u_from.currentText(), self.u_to.currentText()
        if v is None or a not in units or b not in units:
            self.u_out.setText("—")
            return
        res = convert_temp(v, a, b) if units[a] is None else v * units[a] / units[b]
        self.u_out.setText(f"{fmt_num(res, 4).rstrip('0').rstrip(',.') or '0'} {b}")


# ---------------------------------------------------------------------------
# Música tocando (Linux, MPRIS)
# ---------------------------------------------------------------------------
class MediaCard(InfoCard):
    def __init__(self, app):
        super().__init__(app, "media", "Tocando agora")
        self.meta.setText("")
        self.player = None
        self.art_url = None
        top = QHBoxLayout()
        self.art = QLabel(alignment=Qt.AlignCenter)
        self.art.setFixedSize(72, 72)
        self.art.setStyleSheet("background: rgba(255,255,255,0.08); border-radius: 8px; font-size: 26pt;")
        texts = QVBoxLayout()
        self.title = QLabel(objectName="strong", wordWrap=True)
        self.artist = QLabel(objectName="muted", wordWrap=True)
        texts.addWidget(self.title)
        texts.addWidget(self.artist)
        texts.addStretch()
        top.addWidget(self.art)
        top.addLayout(texts, 1)
        self.body.addLayout(top)
        ctl = QHBoxLayout()
        ctl.addStretch()
        self.btns = {}
        for key, glyph in (("Previous", "⏮"), ("PlayPause", "⏯"), ("Next", "⏭")):
            b = QToolButton(text=glyph)
            b.setStyleSheet("font-size: 14pt; padding: 4px 14px;")
            b.clicked.connect(lambda _c=False, k=key: self.command(k))
            ctl.addWidget(b)
            self.btns[key] = b
        ctl.addStretch()
        self.body.addLayout(ctl)
        self.refresh()
        QTimer(self, interval=2500, timeout=self.refresh).start()
        QTimer.singleShot(0, self.fit)

    def refresh(self):
        if self.loading:
            return
        self.loading = True
        run_async(system.media_now, self.show_media)

    def show_media(self, p, _err):
        self.loading = False
        self.player = p
        playing = bool(p and p["title"])
        self.title.setText(p["title"] if playing else _("Nada tocando"))
        self.artist.setText(" · ".join(x for x in (p["artist"], p["app"]) if x) if playing else
                            _("Toque algo no Spotify, no navegador ou em outro player."))
        self.meta.setText(_("tocando") if p and p["status"] == "Playing" else _("pausado") if playing else "")
        for b in self.btns.values():
            b.setEnabled(bool(p))
        url = p["art"] if playing else ""
        if url != self.art_url:
            self.art_url = url
            self.art.setText("♪")
            if url.startswith("file://"):
                self.set_art(QPixmap(QUrl(url).toLocalFile()))
            elif url.startswith("http"):
                run_async(lambda u=url: data.http_get(u), self.got_art)

    def got_art(self, raw, err):
        if raw and not err:
            pm = QPixmap()
            pm.loadFromData(raw)
            self.set_art(pm)

    def set_art(self, pm):
        if not pm.isNull():
            self.art.setPixmap(pm.scaled(72, 72, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))

    def command(self, method):
        if self.player:
            system.media_command(self.player["bus"], method)
            QTimer.singleShot(400, self.refresh)


# ---------------------------------------------------------------------------
# Imagem do dia (Bing), com opção de virar papel de parede
# ---------------------------------------------------------------------------
class ImageOfDayCard(InfoCard):
    def __init__(self, app):
        super().__init__(app, "image", "Imagem do dia")
        self.app.cfg.setdefault("auto_wallpaper", False)
        self.path = None
        self.img = QLabel(alignment=Qt.AlignCenter)
        self.img.setMinimumHeight(200)
        self.img.setStyleSheet("border-radius: 10px;")
        self.caption = QLabel(objectName="muted", wordWrap=True)
        self.title = QLabel(objectName="strong", wordWrap=True)
        self.body.addWidget(self.img)
        self.body.addWidget(self.title)
        self.body.addWidget(self.caption)
        row = QHBoxLayout()
        self.use = QToolButton(text=_("Usar como papel de parede"))
        self.use.clicked.connect(self.use_wallpaper)
        row.addWidget(self.use)
        row.addStretch()
        self.body.addLayout(row)
        self.refresh()
        QTimer(self, interval=60 * 60 * 1000, timeout=self.refresh).start()

    def folder(self):
        d = os.path.join(system.config_dir(), "imagem-do-dia")
        os.makedirs(d, exist_ok=True)
        return d

    def refresh(self):
        if self.loading:
            return
        self.loading = True
        mkt = {"pt": "pt-BR", "es": "es-ES"}.get(i18n.LANG, "en-US")
        folder = self.folder()

        def work():
            info = data.http_json("https://www.bing.com/HPImageArchive.aspx?" + urllib.parse.urlencode(
                {"format": "js", "idx": 0, "n": 1, "mkt": mkt}))["images"][0]
            path = os.path.join(folder, f"bing-{info['startdate']}.jpg")
            if not os.path.exists(path):
                raw = data.http_get("https://www.bing.com" + info["url"])
                with open(path, "wb") as f:
                    f.write(raw)
                for old in sorted(os.listdir(folder))[:-7]:  # guarda só as 7 mais recentes
                    os.remove(os.path.join(folder, old))
            with open(path + ".json", "w", encoding="utf-8") as f:
                json.dump(info, f)
            return path, info

        run_async(work, self.show_image)

    def show_image(self, res, err):
        self.loading = False
        if err or not res:
            self.meta.setText(_("sem conexão"))
            return
        self.path, info = res
        pm = QPixmap(self.path)
        w = max(300, self.width() - 40)
        self.img.setPixmap(pm.scaledToWidth(w, Qt.SmoothTransformation))
        self.title.setText(info.get("title", ""))
        self.caption.setText(info.get("copyright", ""))
        self.meta.setText(date.today().strftime("%d/%m") if i18n.LANG != "en" else date.today().strftime("%m/%d"))
        if self.app.cfg["auto_wallpaper"] and self.app.cfg.get("wallpaper_current") != self.path:
            self.use_wallpaper()
        QTimer.singleShot(0, self.fit)

    def use_wallpaper(self):
        if not self.path:
            return
        old = system.set_wallpaper(self.path)
        if not self.app.cfg.get("wallpaper_original") and old and "imagem-do-dia" not in old:
            self.app.cfg["wallpaper_original"] = old  # para "Restaurar papel de parede original"
        self.app.cfg["wallpaper_current"] = self.path
        self.app.schedule_save()

    def extra_menu(self, menu):
        auto = menu.addAction(_("Trocar o papel de parede todo dia"))
        auto.setCheckable(True)
        auto.setChecked(self.app.cfg["auto_wallpaper"])
        auto.toggled.connect(self.set_auto)
        if self.app.cfg.get("wallpaper_original"):
            menu.addAction(_("Restaurar papel de parede original"), self.restore)

    def set_auto(self, on):
        self.app.cfg["auto_wallpaper"] = on
        self.app.schedule_save()
        if on:
            self.use_wallpaper()

    def restore(self):
        orig = self.app.cfg.pop("wallpaper_original", None)
        if orig:
            system.set_wallpaper(orig)
        self.app.cfg["auto_wallpaper"] = False
        self.app.cfg.pop("wallpaper_current", None)
        self.app.schedule_save()
