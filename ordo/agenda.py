"""Card "Agenda e prazos": calendário com feriados, prazos em dias úteis (CPC) e lembretes com horário."""
import time
from datetime import date, datetime, timedelta

from PySide6.QtCore import QDate, QDateTime, Qt, QTimer
from PySide6.QtWidgets import (QComboBox, QDateEdit, QDateTimeEdit, QDialog, QDialogButtonBox,
                               QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMenu, QPlainTextEdit,
                               QSpinBox, QToolButton, QVBoxLayout, QWidget)

from . import i18n, system
from .cards import InfoCard, section
from .deadlines import DEFAULT_GROUPS, HOLIDAY_GROUPS, Calendar
from .i18n import MONTHS, WEEKDAYS_SHORT, _
from .widgets import Toast

def fmt_date(d, weekday=True):
    wd = WEEKDAYS_SHORT[i18n.LANG][d.weekday()].lower() + ", " if weekday else ""
    return wd + (d.strftime("%m/%d/%Y") if i18n.LANG == "en" else d.strftime("%d/%m/%Y"))


class AgendaCard(InfoCard):
    def __init__(self, app):
        super().__init__(app, "agenda", "Agenda e prazos")
        self.meta.setText("")
        self.month = date.today().replace(day=1)
        self.build()
        self.check_timer = QTimer(self, interval=20000, timeout=self.check_alerts)
        self.check_timer.start()
        QTimer.singleShot(3000, self.check_alerts)
        # À meia-noite o "hoje" e as contagens mudam
        QTimer(self, interval=60 * 1000, timeout=self.maybe_new_day).start()
        self._today = date.today()

    # ---- dados ----
    @property
    def cfg(self):
        c = self.app.cfg
        c.setdefault("deadlines", [])
        c.setdefault("reminders", [])
        c.setdefault("holiday_groups", list(DEFAULT_GROUPS))
        c.setdefault("holiday_extra", [])
        c.setdefault("recess", True)
        return c

    def calendar(self):
        c = self.cfg
        return Calendar(c["holiday_groups"], c["holiday_extra"], c["recess"])

    def maybe_new_day(self):
        if date.today() != self._today:
            self._today = date.today()
            self.build()

    # ---- interface ----
    def build(self):
        self.clear_body()
        cal = self.calendar()
        self.body.addLayout(self.month_view(cal))
        due = {}
        for p in self.cfg["deadlines"]:
            due.setdefault(p["due"], []).append(p)
        # Prazos
        head = QHBoxLayout()
        head.addWidget(section(_("PRAZOS")), 1)
        add = QToolButton(text=_("+ Prazo"), objectName="flat")
        add.clicked.connect(lambda: self.edit_deadline())
        head.addWidget(add)
        self.body.addLayout(head)
        items = sorted(self.cfg["deadlines"], key=lambda p: p["due"])
        if not items:
            self.body.addWidget(QLabel(_("Nenhum prazo. Use “+ Prazo” para calcular um."), objectName="muted",
                                       wordWrap=True))
        today = date.today()
        for p in items:
            d = date.fromisoformat(p["due"])
            left = cal.business_days_between(today, d)
            if d < today:
                status, kind = _("vencido"), "late"
            elif d == today:
                status, kind = _("vence hoje"), "late"
            else:
                status = _("falta 1 dia útil") if left == 1 else _("faltam {n} dias úteis", n=left)
                kind = "warn" if left <= 3 else "ok"
            self.body.addWidget(self.row(p["title"] or _("Prazo"), _("vence {d}", d=fmt_date(d)), status, kind,
                                         on_click=lambda p=p: self.edit_deadline(p),
                                         on_remove=lambda p=p: self.remove("deadlines", p)))
        # Lembretes
        head = QHBoxLayout()
        head.addWidget(section(_("LEMBRETES")), 1)
        add = QToolButton(text=_("+ Lembrete"), objectName="flat")
        add.clicked.connect(lambda: self.edit_reminder())
        head.addWidget(add)
        self.body.addLayout(head)
        rems = sorted(self.cfg["reminders"], key=lambda r: r["when"])
        if not rems:
            self.body.addWidget(QLabel(_("Nenhum lembrete."), objectName="muted"))
        for r in rems:
            when = datetime.fromisoformat(r["when"])
            self.body.addWidget(self.row(r["text"], f"{fmt_date(when.date())} · {when:%H:%M}",
                                         _("avisado") if r.get("fired") else "", "muted" if r.get("fired") else "ok",
                                         on_click=lambda r=r: self.edit_reminder(r),
                                         on_remove=lambda r=r: self.remove("reminders", r)))
        QTimer.singleShot(0, self.fit)

    def month_view(self, cal):
        box = QVBoxLayout()
        nav = QHBoxLayout()
        prev = QToolButton(text="‹", objectName="flat")
        nxt = QToolButton(text="›", objectName="flat")
        prev.clicked.connect(lambda: self.shift_month(-1))
        nxt.clicked.connect(lambda: self.shift_month(1))
        title = QLabel(f"{MONTHS[i18n.LANG][self.month.month - 1].capitalize()} {self.month.year}",
                       objectName="strong", alignment=Qt.AlignCenter)
        title.setCursor(Qt.PointingHandCursor)
        title.mousePressEvent = lambda _e: self.go_today()
        title.setToolTip(_("Voltar para hoje"))
        nav.addWidget(prev)
        nav.addWidget(title, 1)
        nav.addWidget(nxt)
        box.addLayout(nav)
        grid = QGridLayout()
        grid.setSpacing(2)
        order = [6, 0, 1, 2, 3, 4, 5]  # domingo primeiro
        for c, wd in enumerate(order):
            grid.addWidget(QLabel(WEEKDAYS_SHORT[i18n.LANG][wd][:3], objectName="muted", alignment=Qt.AlignCenter),
                           0, c)
        marks = {p["due"] for p in self.cfg["deadlines"]} | {r["when"][:10] for r in self.cfg["reminders"]}
        first = self.month - timedelta(days=(self.month.weekday() + 1) % 7)
        today = date.today()
        for i in range(42):
            d = first + timedelta(days=i)
            lbl = QLabel(str(d.day) + ("•" if d.isoformat() in marks else ""), objectName="day",
                         alignment=Qt.AlignCenter)
            hol = cal.holiday(d)
            color = "rgba(255,255,255,0.25)" if d.month != self.month.month else (
                "#ff8a8a" if hol else "rgba(255,255,255,0.55)" if d.weekday() >= 5 else "white")
            extra = "background: #7c8cff; font-weight: bold;" if d == today else ""
            if cal.recess and d.month == self.month.month and not hol and d.weekday() < 5 and \
                    not cal.is_business(d):
                color = "#ffb347"  # suspensão de 20/12 a 20/01
            lbl.setStyleSheet(f"QLabel {{ color: {color}; border-radius: 6px; padding: 3px 0; {extra} }}"
                              "QLabel:hover { background: rgba(255,255,255,0.14); }")
            tips = [t for t in (hol, _("Suspensão de prazos (20/12 a 20/01)") if cal.recess and
                                not hol and d.weekday() < 5 and not cal.is_business(d) else None) if t]
            tips += [p["title"] or _("Prazo") for p in self.cfg["deadlines"] if p["due"] == d.isoformat()]
            tips += [r["text"] for r in self.cfg["reminders"] if r["when"][:10] == d.isoformat()]
            if tips:
                lbl.setToolTip("\n".join(_(t) if t == hol else t for t in tips))
            lbl.setCursor(Qt.PointingHandCursor)
            lbl.mousePressEvent = lambda ev, d=d: self.day_menu(d, ev)
            grid.addWidget(lbl, 1 + i // 7, i % 7)
        box.addLayout(grid)
        return box

    def row(self, title, sub, status, kind, on_click, on_remove):
        w = QWidget(objectName="row")
        w.setCursor(Qt.PointingHandCursor)
        hl = QHBoxLayout(w)
        hl.setContentsMargins(6, 4, 2, 4)
        texts = QVBoxLayout()
        texts.setSpacing(0)
        t = QLabel(title, wordWrap=True)
        texts.addWidget(t)
        texts.addWidget(QLabel(sub, objectName="muted"))
        hl.addLayout(texts, 1)
        if status:
            hl.addWidget(QLabel(status, objectName=kind))
        rm = QToolButton(text="✕", objectName="flat", toolTip=_("Remover"))
        rm.clicked.connect(on_remove)
        hl.addWidget(rm)
        w.mousePressEvent = lambda ev: ev.button() == Qt.LeftButton and on_click()
        return w

    def shift_month(self, n):
        m = self.month.month - 1 + n
        self.month = date(self.month.year + m // 12, m % 12 + 1, 1)
        self.build()

    def go_today(self):
        self.month = date.today().replace(day=1)
        self.build()

    def day_menu(self, d, ev):
        menu = QMenu(self)
        menu.addAction(_("Novo lembrete em {d}", d=fmt_date(d, False)), lambda: self.edit_reminder(day=d))
        menu.addAction(_("Prazo a partir de {d}", d=fmt_date(d, False)), lambda: self.edit_deadline(start=d))
        menu.exec(ev.globalPosition().toPoint())

    def extra_menu(self, menu):
        sub = menu.addMenu(_("Feriados considerados"))
        for key, (label, _fn) in HOLIDAY_GROUPS.items():
            act = sub.addAction(_(label))
            act.setCheckable(True)
            act.setChecked(key in self.cfg["holiday_groups"])
            act.toggled.connect(lambda on, k=key: self.toggle_group(k, on))
        sub.addSeparator()
        rec = sub.addAction(_("Suspensão de 20/12 a 20/01 (art. 220 do CPC)"))
        rec.setCheckable(True)
        rec.setChecked(self.cfg["recess"])
        rec.toggled.connect(self.toggle_recess)
        sub.addAction(_("Feriados extras do meu tribunal…"), self.edit_extra)

    def toggle_group(self, key, on):
        groups = [g for g in self.cfg["holiday_groups"] if g != key] + ([key] if on else [])
        self.cfg["holiday_groups"] = [g for g in HOLIDAY_GROUPS if g in groups]
        self.recompute()

    def toggle_recess(self, on):
        self.cfg["recess"] = on
        self.recompute()

    def recompute(self):
        """Feriados mudaram: recalcula o vencimento de todos os prazos."""
        cal = self.calendar()
        for p in self.cfg["deadlines"]:
            p["due"] = cal.deadline(date.fromisoformat(p["start"]), p["days"], p.get("business", True)).isoformat()
        self.app.schedule_save()
        self.build()

    def remove(self, kind, item):
        self.cfg[kind] = [x for x in self.cfg[kind] if x is not item]
        self.app.schedule_save()
        self.build()

    # ---- diálogos ----
    def edit_deadline(self, item=None, start=None):
        dlg = DeadlineDialog(self, item, start)
        if dlg.exec():
            data = dlg.result_data()
            if item:
                item.update(data)
            else:
                data["id"] = int(time.time() * 1000)
                self.cfg["deadlines"].append(data)
            self.app.schedule_save()
            self.build()

    def edit_reminder(self, item=None, day=None):
        dlg = QDialog(self)
        dlg.setWindowTitle(_("Lembrete"))
        form = QFormLayout(dlg)
        text = QLineEdit(item["text"] if item else "", placeholderText=_("Audiência, reunião, ligar para…"))
        when = QDateTimeEdit(calendarPopup=True, displayFormat="dd/MM/yyyy HH:mm")
        if item:
            when.setDateTime(QDateTime.fromString(item["when"][:16], "yyyy-MM-ddTHH:mm"))
        else:
            base = datetime.combine(day or date.today(), datetime.now().time()).replace(second=0, microsecond=0)
            base += timedelta(hours=1) - timedelta(minutes=base.minute)
            when.setDateTime(QDateTime.fromString(base.strftime("%Y-%m-%dT%H:%M"), "yyyy-MM-ddTHH:mm"))
        form.addRow(_("O quê"), text)
        form.addRow(_("Quando"), when)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(_("Salvar"))
        bb.button(QDialogButtonBox.Cancel).setText(_("Cancelar"))
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow(bb)
        if dlg.exec() and text.text().strip():
            data = {"text": text.text().strip(), "when": when.dateTime().toString("yyyy-MM-ddTHH:mm"), "fired": False}
            if item:
                item.update(data)
            else:
                data["id"] = int(time.time() * 1000)
                self.cfg["reminders"].append(data)
            self.app.schedule_save()
            self.build()

    def edit_extra(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(_("Feriados extras do meu tribunal"))
        dlg.resize(420, 360)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(_("Um por linha: AAAA-MM-DD = Nome (só naquele ano) ou MM-DD = Nome (todo ano)."),
                             wordWrap=True))
        edit = QPlainTextEdit("\n".join(self.cfg["holiday_extra"]))
        edit.setPlaceholderText("2026-10-30 = Ponto facultativo\n10-28 = Dia do Servidor Público")
        lay.addWidget(edit, 1)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(_("Salvar"))
        bb.button(QDialogButtonBox.Cancel).setText(_("Cancelar"))
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)
        if dlg.exec():
            self.cfg["holiday_extra"] = [x.strip() for x in edit.toPlainText().splitlines() if x.strip()]
            self.recompute()

    # ---- avisos ----
    def check_alerts(self):
        now = datetime.now()
        changed = False
        for r in self.cfg["reminders"]:
            if not r.get("fired") and datetime.fromisoformat(r["when"]) <= now:
                r["fired"] = True
                changed = True
                self.notify(_("Lembrete"), r["text"])
        # Lembretes avisados há mais de 7 dias saem da lista sozinhos
        keep = [r for r in self.cfg["reminders"]
                if not r.get("fired") or datetime.fromisoformat(r["when"]) > now - timedelta(days=7)]
        if len(keep) != len(self.cfg["reminders"]):
            self.cfg["reminders"] = keep
            changed = True
        # Uma vez por dia: prazos que vencem hoje ou amanhã (útil)
        today = date.today().isoformat()
        if self.cfg.get("deadline_alert_day") != today:
            self.cfg["deadline_alert_day"] = today
            changed = True
            cal = self.calendar()
            soon = [p for p in self.cfg["deadlines"]
                    if 0 <= cal.business_days_between(date.today(), date.fromisoformat(p["due"])) <= 1]
            if soon:
                self.notify(_("Prazos vencendo"), "\n".join(
                    f"{p['title'] or _('Prazo')} — {fmt_date(date.fromisoformat(p['due']))}" for p in soon))
        if changed:
            self.app.schedule_save()
            self.build()

    def notify(self, title, body):
        system.play_alarm()
        self._toasts = getattr(self, "_toasts", [])
        self._toasts.append(Toast(title, body, seconds=30))


class DeadlineDialog(QDialog):
    def __init__(self, card, item=None, start=None):
        super().__init__(card)
        self.card = card
        self.setWindowTitle(_("Prazo"))
        self.setMinimumWidth(420)
        form = QFormLayout(self)
        self.title = QLineEdit(item["title"] if item else "", placeholderText=_("Contestação, recurso, processo…"))
        self.start = QDateEdit(calendarPopup=True, displayFormat="dd/MM/yyyy")
        s = date.fromisoformat(item["start"]) if item else (start or date.today())
        self.start.setDate(QDate(s.year, s.month, s.day))
        self.days = QSpinBox(minimum=1, maximum=365, value=item["days"] if item else 15)
        self.kind = QComboBox()
        self.kind.addItems([_("dias úteis"), _("dias corridos")])
        self.kind.setCurrentIndex(0 if (item or {}).get("business", True) else 1)
        self.result = QLabel(objectName="strong", wordWrap=True)
        self.skipped = QLabel(wordWrap=True)
        self.skipped.setStyleSheet("color: #888;")
        form.addRow(_("Descrição"), self.title)
        form.addRow(_("Intimação / publicação"), self.start)
        row = QHBoxLayout()
        row.addWidget(self.days)
        row.addWidget(self.kind, 1)
        form.addRow(_("Prazo"), row)
        form.addRow(_("Vencimento"), self.result)
        form.addRow("", self.skipped)
        note = QLabel(_("Conta a partir do primeiro dia útil seguinte (art. 224 do CPC). Confira os feriados do "
                        "seu tribunal no menu do card (botão direito → Feriados considerados)."), wordWrap=True)
        note.setStyleSheet("color: #888; font-size: 8pt;")
        form.addRow(note)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(_("Salvar"))
        bb.button(QDialogButtonBox.Cancel).setText(_("Cancelar"))
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        form.addRow(bb)
        for w in (self.start.dateChanged, self.days.valueChanged, self.kind.currentIndexChanged):
            w.connect(self.update_result)
        self.update_result()

    def compute(self):
        q = self.start.date()
        s = date(q.year(), q.month(), q.day())
        cal = self.card.calendar()
        due = cal.deadline(s, self.days.value(), self.kind.currentIndex() == 0)
        return s, due, cal.skipped(s, due)

    def update_result(self):
        _s, due, skipped = self.compute()
        self.result.setText(fmt_date(due))
        self.skipped.setText(_("Não contou: {lista}", lista="; ".join(
            f"{d.strftime('%d/%m')} {_(n)}" if d else _(n) for d, n in skipped)) if skipped else "")

    def result_data(self):
        s, due, _sk = self.compute()
        return {"title": self.title.text().strip(), "start": s.isoformat(), "days": self.days.value(),
                "business": self.kind.currentIndex() == 0, "due": due.isoformat()}

