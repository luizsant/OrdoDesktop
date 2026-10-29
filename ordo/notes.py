"""Notas adesivas coloridas, soltas na área de trabalho."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMenu, QMessageBox, QPlainTextEdit, QToolButton, \
    QVBoxLayout, QWidget

from .catalog import NOTE_COLOR_NAMES, NOTE_COLORS
from .i18n import _
from .widgets import DesktopWindow, Grip


class StickyNote(DesktopWindow):
    def __init__(self, app, data):
        super().__init__(app, _("Nota"))
        self.data = data
        self.frame = QWidget(self, objectName="note")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.frame)
        lay = QVBoxLayout(self.frame)
        lay.setContentsMargins(0, 0, 0, 8)
        lay.setSpacing(0)
        self.head = QWidget(objectName="head")
        self.head.setCursor(Qt.OpenHandCursor)
        hl = QHBoxLayout(self.head)
        hl.setContentsMargins(12, 3, 6, 3)
        hl.addWidget(QLabel(data.get("created", ""), objectName="date"), 1)
        for glyph, tip, cb in (("+", _("Nova nota"), lambda: app.new_note(near=self)),
                               ("🎨", _("Cor"), self.color_menu),
                               ("✕", _("Apagar nota"), self.delete)):
            b = QToolButton(text=glyph, toolTip=tip, cursor=Qt.PointingHandCursor)
            b.clicked.connect(cb)
            hl.addWidget(b)
        self.head.mousePressEvent = lambda ev: ev.button() == Qt.LeftButton and self.begin_drag(ev)
        self.head.mouseMoveEvent = self.mouseMoveEvent
        self.head.mouseReleaseEvent = self.mouseReleaseEvent
        lay.addWidget(self.head)
        self.title = QLineEdit(data.get("title", ""), objectName="title", placeholderText=_("Título"))
        self.title.textChanged.connect(lambda t: self.store("title", t))
        lay.addWidget(self.title)
        self.text = QPlainTextEdit(data.get("text", ""), objectName="text")
        self.text.textChanged.connect(lambda: self.store("text", self.text.toPlainText()))
        lay.addWidget(self.text, 1)
        self.grip = Grip(self, min_size=(180, 140))
        self.apply_color()
        self.move(data["x"], data["y"])
        self.resize(data.get("w", 260), data.get("h", 220))

    def resizeEvent(self, ev):
        self.grip.move(self.width() - self.grip.width() - 4, self.height() - self.grip.height() - 2)
        super().resizeEvent(ev)

    def store(self, key, value):
        self.data[key] = value
        self.app.schedule_save()

    def apply_color(self):
        bg, head = NOTE_COLORS.get(self.data.get("color"), NOTE_COLORS["amarelo"])
        self.setStyleSheet(f"""
            QWidget#note {{ background: {bg}; border-radius: 14px; }}
            QWidget#head {{ background: {head}; border-top-left-radius: 14px; border-top-right-radius: 14px; }}
            QLabel#date {{ color: rgba(0,0,0,0.55); font-size: 8pt; font-weight: bold; background: transparent; }}
            QToolButton {{ color: rgba(0,0,0,0.62); background: transparent; border: none; padding: 0 6px;
                           font-size: 12pt; font-weight: bold; }}
            QToolButton:hover {{ background: rgba(0,0,0,0.10); border-radius: 6px; }}
            QLineEdit#title {{ background: transparent; border: none; color: #1d1d24; font-size: 15pt;
                               font-weight: 800; padding: 6px 12px 0 12px; }}
            QPlainTextEdit#text {{ background: transparent; border: none; color: #2b2b35; font-size: 10.5pt;
                                   padding: 2px 8px; }}
        """)

    def color_menu(self):
        menu = QMenu(self)
        for key, name in NOTE_COLOR_NAMES.items():
            menu.addAction(_(name), lambda k=key: (self.store("color", k), self.apply_color()))
        menu.exec(self.cursor().pos())

    def geometry_changed(self):
        self.data.update(x=self.x(), y=self.y(), w=self.width(), h=self.height())
        self.app.schedule_save()

    def delete(self):
        if self.data.get("text", "").strip() or self.data.get("title", "").strip():
            ok = QMessageBox.question(None, _("Apagar nota"), _("Apagar esta nota?") + "\n"
                                      + _("O conteúdo da nota será perdido.")) == QMessageBox.Yes
            if not ok:
                return
        self.app.remove_note(self)
