"""Card do relógio: hora, data, busca nas caixas, clima, uso do sistema e atalhos (visual próprio, fixo)."""
import time
from datetime import datetime

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMenu, QProgressBar, QToolButton, QVBoxLayout, QWidget)

from . import data, i18n, system
from .catalog import CAT_BY_KEY, WEATHER_CODES
from .i18n import WEEKDAYS_SHORT, _
from .widgets import DesktopWindow, Toast, run_async

CARD_STYLE = """
    QWidget#card { background: rgba(18,20,26,0.55); border: 1px solid rgba(255,255,255,0.09); border-radius: 18px; }
    QLabel { color: white; background: transparent; }
    QLabel#time { font-size: 46pt; font-weight: 300; }
    QLabel#sec { color: rgba(255,255,255,0.55); font-size: 18pt; font-weight: 300; }
    QLabel#date { color: rgba(255,255,255,0.85); font-size: 12pt; }
    QLabel#extra { color: rgba(255,255,255,0.55); font-size: 9.5pt; }
    QLineEdit#search { background: rgba(255,255,255,0.10); color: white; border: 1px solid rgba(255,255,255,0.18);
                       border-radius: 9px; padding: 5px 9px; margin-top: 10px; font-size: 10pt; }
    QLineEdit#search:focus { border-color: rgba(124,140,255,0.8); background: rgba(255,255,255,0.14); }
    QWidget#row { border-radius: 8px; }
    QWidget#row:hover, QWidget#row[first="true"] { background: rgba(255,255,255,0.10); }
    QLabel#sname { font-size: 9.5pt; }
    QLabel#swhere, QLabel#smore { color: rgba(255,255,255,0.45); font-size: 7.5pt; }
    QLabel#sempty { color: rgba(255,255,255,0.5); font-size: 8.5pt; padding: 6px; }
    QWidget#sep { background: rgba(255,255,255,0.12); }
    QLabel#section { color: rgba(255,255,255,0.45); font-size: 7.5pt; font-weight: bold; margin-top: 8px; }
    QLabel#wxtemp { font-size: 28pt; font-weight: 300; }
    QLabel#wxicon { color: #ffd76a; font-size: 30pt; }
    QLabel#wxdesc { font-size: 10.5pt; font-weight: bold; }
    QLabel#wxinfo { color: rgba(255,255,255,0.65); font-size: 8.5pt; }
    QLabel#wxday { color: rgba(255,255,255,0.75); font-size: 8pt; }
    QLabel#wxdayicon { color: #ffd76a; font-size: 14pt; }
    QLabel#wxdaytemp { font-size: 8.5pt; }
    QLabel#stat { color: rgba(255,255,255,0.70); font-size: 8.5pt; }
    QLabel#statv { color: rgba(255,255,255,0.90); font-size: 8.5pt; }
    QProgressBar { background: rgba(255,255,255,0.12); border: none; border-radius: 3px; max-height: 6px; }
    QProgressBar::chunk { background: #7c8cff; border-radius: 3px; }
    QProgressBar[level="warn"]::chunk { background: #ff9f43; }
    QProgressBar[level="crit"]::chunk { background: #ff5c5c; }
    QToolButton { color: rgba(255,255,255,0.88); background: transparent; border: none; border-radius: 10px;
                  padding: 6px 0; font-size: 8pt; min-width: 76px; }
    QToolButton:hover { background: rgba(255,255,255,0.12); }
    QToolButton:pressed { background: rgba(255,255,255,0.20); }
    QToolButton[on="true"] { background: rgba(124,140,255,0.35); }
"""

# Símbolos usados quando o sistema não tem o ícone do tema (Windows)
GLYPHS = {"view-grid-symbolic": "▦", "camera-photo-symbolic": "📷", "accessories-calculator-symbolic": "🖩",
          "utilities-terminal-symbolic": "⌨", "folder-download-symbolic": "⬇", "user-trash-symbolic": "🗑",
          "system-lock-screen-symbolic": "🔒", "notifications-disabled-symbolic": "🔕", "alarm-symbolic": "⏰",
          "go-up-symbolic": "▲", "go-down-symbolic": "▼", "utilities-system-monitor-symbolic": "📈",
          "document-new-symbolic": "📝"}
WEATHER_GLYPHS = {"weather-clear-symbolic": "☀", "weather-clear-night-symbolic": "☾",
                  "weather-few-clouds-symbolic": "⛅", "weather-few-clouds-night-symbolic": "☁",
                  "weather-overcast-symbolic": "☁", "weather-fog-symbolic": "🌫",
                  "weather-showers-scattered-symbolic": "🌦", "weather-showers-symbolic": "🌧",
                  "weather-snow-symbolic": "❄", "weather-storm-symbolic": "⛈"}


def tinted(name, size, color):
    """Ícone "simbólico" do tema pintado numa cor (o GTK faz isso sozinho; o Qt não). None se não houver tema."""
    ic = QIcon.fromTheme(name)
    if ic.isNull():
        return None
    pm = ic.pixmap(size, size)
    p = QPainter(pm)
    p.setCompositionMode(QPainter.CompositionMode_SourceIn)
    p.fillRect(pm.rect(), QColor(color))
    p.end()
    return pm


def themed(label, name, size, glyphs, color="#ffd76a"):
    """Põe no QLabel o ícone do tema (Linux) ou, sem tema, o símbolo equivalente (Windows)."""
    pm = tinted(name, size, color)
    if pm:
        label.setPixmap(pm)
    else:
        label.setText(glyphs.get(name, "•"))


def sep():
    w = QWidget(objectName="sep")
    w.setFixedHeight(1)
    return w


class ClockCard(DesktopWindow):
    MAX_RESULTS = 6

    def __init__(self, app):
        super().__init__(app, _("Relógio"))
        self.card = QWidget(self, objectName="card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.card)
        self.lay = lay = QVBoxLayout(self.card)
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
        # busca nas caixas
        self.search = QLineEdit(objectName="search", placeholderText=_("Buscar nas caixas"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.app.set_query)
        self.search.returnPressed.connect(self.open_first)
        lay.addWidget(self.search)
        self.results = QVBoxLayout()
        self.results.setSpacing(1)
        lay.addLayout(self.results)
        self.first_item = None
        self.gadgets = None
        self.set_gadgets(app.cfg["show_gadgets"])
        self.setStyleSheet(CARD_STYLE)
        g = app.cfg["clock"]
        if "x" in g:
            self.move(g["x"], g["y"])
        self.tick()
        self.timer = QTimer(self, interval=1000, timeout=self.tick)
        QTimer.singleShot(1000 - int(time.time() * 1000) % 1000, self.timer.start)

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Escape:
            self.search.clear()  # Esc limpa a busca
        super().keyPressEvent(ev)

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

    # ---- busca ----
    def show_results(self, query, items):
        while self.results.count():
            w = self.results.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.first_item = items[0] if items else None
        if query and not items:
            self.results.addWidget(QLabel(_("Nada nas caixas com esse nome."), objectName="sempty"))
        for i, item in enumerate(items[: self.MAX_RESULTS]):
            row = QWidget(objectName="row")
            row.setProperty("first", i == 0)  # é o que o Enter abre
            row.setCursor(Qt.PointingHandCursor)
            row.setToolTip(item.path)
            hl = QHBoxLayout(row)
            hl.setContentsMargins(6, 4, 6, 4)
            icon = QLabel()
            icon.setPixmap(item.icon(24).pixmap(24, 24))
            hl.addWidget(icon)
            texts = QVBoxLayout()
            texts.setSpacing(0)
            name = QLabel(objectName="sname")
            name.setText(name.fontMetrics().elidedText(item.display_name, Qt.ElideMiddle, 260))
            texts.addWidget(name)
            texts.addWidget(QLabel(_("em {box}", box=_(CAT_BY_KEY[item.category][1])), objectName="swhere"))
            hl.addLayout(texts, 1)
            row.mousePressEvent = lambda ev, it=item: self.on_result(ev, it)
            self.results.addWidget(row)
        if len(items) > self.MAX_RESULTS:
            self.results.addWidget(QLabel(_("+ {n} nas caixas destacadas", n=len(items) - self.MAX_RESULTS),
                                          objectName="smore"))
        self.adjustSize()

    def on_result(self, ev, item):
        if ev.button() == Qt.LeftButton:
            item.open()
            self.search.clear()
        elif ev.button() == Qt.RightButton:
            system.show_in_files(item.path)

    def open_first(self):
        if self.first_item:
            self.first_item.open()
            self.search.clear()

    # ---- gadgets ----
    def set_gadgets(self, show):
        if show and not self.gadgets:
            self.gadgets = GadgetPanel(self.app)
            self.lay.addWidget(self.gadgets)
        elif not show and self.gadgets:
            self.gadgets.deleteLater()
            self.gadgets = None
        QTimer.singleShot(0, self.adjustSize)


class GadgetPanel(QWidget):
    """Clima, uso do sistema e atalhos rápidos abaixo do relógio."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.stats = system.Stats()
        self.timer_end = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(sep())
        self.weather = WeatherWidget(app)
        lay.addWidget(self.weather)
        lay.addWidget(QLabel(_("SISTEMA"), objectName="section"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)
        self.bars = {}
        for r, (key, label) in enumerate([("cpu", "CPU"), ("mem", "Memória"), ("disk", "Disco")]):
            bar = QProgressBar(textVisible=False, maximum=1000)
            val = QLabel(objectName="statv", alignment=Qt.AlignRight | Qt.AlignVCenter)
            val.setMinimumWidth(110)
            grid.addWidget(QLabel(_(label), objectName="stat"), r, 0)
            grid.addWidget(bar, r, 1)
            grid.addWidget(val, r, 2)
            self.bars[key] = (bar, val)
        grid.setColumnStretch(1, 1)
        lay.addLayout(grid)
        lay.addWidget(QLabel(_("ATALHOS"), objectName="section"))
        buttons = QGridLayout()
        buttons.setSpacing(2)
        self.btn = {}
        defs = [
            ("organize", "view-grid-symbolic", "Reorganizar", app.auto_layout),
            ("shot", "camera-photo-symbolic", "Captura", lambda: QTimer.singleShot(200, system.screenshot)),
            ("calc", "accessories-calculator-symbolic", "Calculadora", system.calculator),
            ("term", "utilities-terminal-symbolic", "Terminal", system.terminal),
            ("down", "folder-download-symbolic", "Downloads", lambda: system.open_path(system.downloads_dir())),
            ("trash", "user-trash-symbolic", "Lixeira", system.open_trash),
            ("lock", "system-lock-screen-symbolic", "Bloquear", system.lock_screen),
            ("dnd", "notifications-disabled-symbolic", "Não perturbe", self.toggle_dnd),
            ("timer", "alarm-symbolic", "Foco", self.toggle_timer),
            ("collapse", "go-up-symbolic", "Recolher", self.toggle_collapse_all),
            ("monitor", "utilities-system-monitor-symbolic", "Monitor", system.system_monitor),
            ("note", "document-new-symbolic", "Nova nota", lambda: app.new_note()),
        ]
        for i, (key, icon, label, cb) in enumerate(defs):
            b = QToolButton(toolButtonStyle=Qt.ToolButtonTextUnderIcon, text=_(label))
            self.set_icon(b, icon)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(cb)
            buttons.addWidget(b, i // 4, i % 4)
            self.btn[key] = b
        self.btn["timer"].setToolTip(_("Clique para iniciar/parar · botão direito escolhe a duração"))
        self.btn["timer"].setContextMenuPolicy(Qt.CustomContextMenu)
        self.btn["timer"].customContextMenuRequested.connect(self.timer_menu)
        self.btn["shot"].setToolTip(_("Abre a ferramenta de captura de tela (tecla Print)"))
        self.btn["organize"].setToolTip(_("Reorganiza as caixas automaticamente"))
        lay.addLayout(buttons)
        self.update_stats()
        QTimer(self, interval=2000, timeout=self.update_stats).start()
        self.tick_timer = QTimer(self, interval=500, timeout=self.timer_tick)

    @staticmethod
    def set_icon(button, name):
        pm = tinted(name, 22, "#ffffff")
        if pm is None:  # Windows: sem tema de ícones, usa um símbolo
            button.setText(f"{GLYPHS.get(name, '•')}\n{button.text().split(chr(10))[-1]}")
            button.setToolButtonStyle(Qt.ToolButtonTextOnly)
        else:
            button.setIcon(QIcon(pm))
            button.setIconSize(QSize(22, 22))

    def set_label(self, key, text):
        b = self.btn[key]
        if b.toolButtonStyle() == Qt.ToolButtonTextOnly:
            b.setText(f"{b.text().split(chr(10))[0]}\n{text}")
        else:
            b.setText(text)

    # ---- sistema ----
    def set_bar(self, key, frac, text):
        bar, val = self.bars[key]
        bar.setValue(int(min(max(frac, 0), 1) * 1000))
        bar.setProperty("level", "crit" if frac >= 0.9 else "warn" if frac >= 0.75 else "")
        bar.style().unpolish(bar)
        bar.style().polish(bar)
        val.setText(text)

    def update_stats(self):
        cpu = self.stats.cpu()
        self.set_bar("cpu", cpu, f"{cpu * 100:.0f}%")
        frac, used, total = self.stats.mem()
        self.set_bar("mem", frac, f"{i18n.fmt_num(used, 1)} / {total:.0f} GB")
        frac, free = self.stats.disk()
        self.set_bar("disk", frac, _("{n} GB livres", n=f"{free:.0f}"))
        n = system.trash_count()
        self.set_label("trash", _("Lixeira ({n})", n=n) if n else _("Lixeira"))
        collapsed = bool(self.app.fences) and all(f.collapsed for f in self.app.fences.values())
        self.set_label("collapse", _("Expandir") if collapsed else _("Recolher"))
        dnd = system.dnd_state()
        self.btn["dnd"].setProperty("on", bool(dnd))
        self.btn["dnd"].style().polish(self.btn["dnd"])
        self.btn["dnd"].setToolTip(_("Notificações silenciadas") if dnd else _("Silenciar notificações"))

    def toggle_dnd(self):
        system.toggle_dnd()
        QTimer.singleShot(300, self.update_stats)

    def toggle_collapse_all(self):
        fences = self.app.fences.values()
        collapse = not (fences and all(f.collapsed for f in fences))
        self.app.set_collapsed_all(collapse)
        self.set_icon(self.btn["collapse"], "go-down-symbolic" if collapse else "go-up-symbolic")
        self.update_stats()

    # ---- timer de foco ----
    def timer_menu(self, pos):
        menu = QMenu(self)
        for m in (5, 15, 25, 45, 60):
            act = menu.addAction(_("{n} minutos", n=m), lambda m=m: self.start_timer(m))
            act.setCheckable(True)
            act.setChecked(m == self.app.cfg["timer_min"])
        menu.exec(self.btn["timer"].mapToGlobal(pos))

    def toggle_timer(self):
        self.stop_timer() if self.timer_end else self.start_timer(self.app.cfg["timer_min"])

    def start_timer(self, minutes):
        self.app.cfg["timer_min"] = minutes
        self.app.schedule_save()
        self.timer_end = time.monotonic() + minutes * 60
        self.btn["timer"].setProperty("on", True)
        self.btn["timer"].style().polish(self.btn["timer"])
        self.tick_timer.start()
        self.timer_tick()

    def stop_timer(self, done=False):
        self.timer_end = None
        self.tick_timer.stop()
        self.btn["timer"].setProperty("on", False)
        self.btn["timer"].style().polish(self.btn["timer"])
        self.set_label("timer", _("Foco"))
        if done:
            system.play_alarm()
            self._toast = Toast(_("Tempo de foco concluído"),
                                _("{n} minutos — hora de uma pausa.", n=self.app.cfg["timer_min"]))

    def timer_tick(self):
        if not self.timer_end:
            return
        left = int(self.timer_end - time.monotonic())
        if left <= 0:
            self.stop_timer(done=True)
            return
        self.set_label("timer", f"{left // 60:02d}:{left % 60:02d}")


class WeatherWidget(QWidget):
    """Tempo atual + próximos dias via Open-Meteo. Clique atualiza; botão direito troca a cidade."""

    REFRESH_MS = 20 * 60 * 1000

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(_("Clique para atualizar · botão direito para trocar a cidade"))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.setSpacing(6)
        top = QHBoxLayout()
        top.setSpacing(12)
        self.icon = QLabel(objectName="wxicon")
        self.temp = QLabel("--°", objectName="wxtemp")
        info = QVBoxLayout()
        info.setSpacing(0)
        self.desc = QLabel(_("Carregando clima…"), objectName="wxdesc")
        self.lines = [QLabel(objectName="wxinfo") for _i in range(3)]
        info.addWidget(self.desc)
        for line in self.lines:
            info.addWidget(line)
        top.addWidget(self.icon)
        top.addWidget(self.temp)
        top.addLayout(info, 1)
        lay.addLayout(top)
        self.days = QHBoxLayout()
        lay.addLayout(self.days)
        self.fetching = False
        self.refresh()
        QTimer(self, interval=self.REFRESH_MS, timeout=self.refresh).start()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.refresh()
        elif ev.button() == Qt.RightButton:
            if CityDialog(self.app).exec():
                self.refresh()

    def contextMenuEvent(self, ev):
        ev.accept()  # o botão direito aqui é da cidade, não do menu geral

    def refresh(self):
        city = self.app.cfg["weather_city"]
        if not city:
            self.desc.setText(_("Defina sua cidade"))
            self.lines[0].setText(_("Botão direito aqui para escolher"))
            return
        if self.fetching:
            return
        self.fetching = True
        run_async(lambda: data.fetch_weather(city), self.show_weather)

    def show_weather(self, d, err):
        self.fetching = False
        city = self.app.cfg["weather_city"]
        if err or not d:
            self.desc.setText(_("Clima indisponível"))
            self.lines[0].setText(_("Sem conexão — tento de novo em 20 min"))
            return
        cur, daily = d["current"], d["daily"]
        desc, day_icon, night_icon = WEATHER_CODES.get(cur["weather_code"], ("—", "weather-overcast-symbolic", None))
        themed(self.icon, day_icon if cur["is_day"] else (night_icon or day_icon), 52, WEATHER_GLYPHS)
        self.temp.setText(f"{round(cur['temperature_2m'])}°")
        self.desc.setText(_(desc))
        rain = daily["precipitation_probability_max"][0]
        self.lines[0].setText(_("{city} · sensação {t}°", city=city["name"], t=round(cur["apparent_temperature"])))
        self.lines[1].setText(_("Máx {hi}° · mín {lo}°", hi=round(daily["temperature_2m_max"][0]),
                                lo=round(daily["temperature_2m_min"][0]))
                              + (_(" · chuva {p}%", p=rain) if rain is not None else ""))
        self.lines[2].setText(_("Umidade {h}% · vento {w} km/h", h=cur["relative_humidity_2m"],
                                w=round(cur["wind_speed_10m"])))
        self.setToolTip(_("Atualizado às {t} · clique para atualizar · botão direito para trocar a cidade",
                          t=time.strftime("%H:%M")))
        while self.days.count():
            item = self.days.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i in range(1, min(5, len(daily["time"]))):
            day = datetime.strptime(daily["time"][i], "%Y-%m-%d")
            col = QWidget()
            cl = QVBoxLayout(col)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setSpacing(2)
            cl.addWidget(QLabel(WEEKDAYS_SHORT[i18n.LANG][day.weekday()], objectName="wxday",
                                alignment=Qt.AlignCenter))
            ic = QLabel(objectName="wxdayicon", alignment=Qt.AlignCenter)
            themed(ic, WEATHER_CODES.get(daily["weather_code"][i], (None, "weather-overcast-symbolic"))[1], 24,
                   WEATHER_GLYPHS)
            cl.addWidget(ic)
            t = QLabel(f"{round(daily['temperature_2m_max'][i])}° <span style='color:rgba(255,255,255,0.5)'>"
                       f"{round(daily['temperature_2m_min'][i])}°</span>", objectName="wxdaytemp",
                       alignment=Qt.AlignCenter)
            cl.addWidget(t)
            col.setToolTip(_(WEATHER_CODES.get(daily["weather_code"][i], ("",))[0]))
            self.days.addWidget(col)


class CityDialog(QDialog):
    """Busca a cidade no geocoding do Open-Meteo."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle(_("Cidade do clima"))
        self.resize(380, 320)
        lay = QVBoxLayout(self)
        self.entry = QLineEdit(placeholderText=_("Digite a cidade e tecle Enter"))
        self.entry.returnPressed.connect(self.search)
        self.list = QListWidget()
        self.list.itemActivated.connect(self.pick)
        lay.addWidget(self.entry)
        lay.addWidget(self.list, 1)
        bb = QDialogButtonBox(QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Cancel).setText(_("Cancelar"))
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def search(self):
        q = self.entry.text().strip()
        if q:
            run_async(lambda: data.search_city(q, i18n.LANG), self.fill)

    def fill(self, results, err):
        self.list.clear()
        if err or not results:
            self.list.addItem(_("Sem conexão.") if err else _("Nada encontrado."))
            return
        for r in results:
            it = QListWidgetItem(r["label"])
            it.setData(Qt.UserRole, r)
            self.list.addItem(it)

    def pick(self, it):
        city = it.data(Qt.UserRole)
        if city:
            city.pop("label", None)
            self.app.cfg["weather_city"] = city
            self.app.schedule_save()
            self.accept()
