"""Cards de mercado financeiro e de notícias: arrastáveis, redimensionáveis e no estilo das caixas."""
import time

from PySide6.QtCore import QPointF, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QColor, QDesktopServices, QPainter, QPen
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QLabel, QPlainTextEdit,
                               QScrollArea, QVBoxLayout, QWidget)

from . import data
from .catalog import DEFAULT_ASSETS, NEWS_COUNTRIES, default_news_sources
from .i18n import _, fmt_num
from .widgets import DesktopWindow, Grip, run_async

CARD_W = 432


def card_style(theme):
    frame = {
        "vidro": "background: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.28); border-radius: 18px;",
        "contorno": "background: rgba(124,140,255,0.08); border: 2px solid rgba(124,140,255,0.70); border-radius: 18px;",
        "compacto": "background: rgba(6,7,10,0.86); border: none; border-radius: 10px;",
    }.get(theme, "background: rgba(18,20,26,0.55); border: 1px solid rgba(255,255,255,0.09); border-radius: 18px;")
    return f"""
        QWidget#card {{ {frame} }}
        QLabel {{ color: white; background: transparent; }}
        QLabel#ctitle {{ color: rgba(255,255,255,0.55); font-size: 8pt; font-weight: bold; letter-spacing: 1px; }}
        QLabel#cmeta, QLabel#csrc {{ color: rgba(255,255,255,0.40); font-size: 8pt; }}
        QScrollArea, QWidget#content {{ background: transparent; border: none; }}
        QScrollBar:vertical {{ background: transparent; width: 8px; }}
        QScrollBar::handle:vertical {{ background: rgba(255,255,255,0.25); border-radius: 4px; min-height: 30px; }}
        QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
        QLabel#mkname {{ font-size: 9.5pt; font-weight: bold; }}
        QLabel#mksub {{ color: rgba(255,255,255,0.45); font-size: 7.5pt; }}
        QLabel#mkval {{ font-size: 9.5pt; }}
        QLabel#up, QLabel#down, QLabel#flat {{ font-size: 8.5pt; font-weight: bold; border-radius: 6px;
                                               padding: 1px 6px; }}
        QLabel#up {{ color: #5fe0a0; background: rgba(62,207,142,0.16); }}
        QLabel#down {{ color: #ff8a8a; background: rgba(255,92,92,0.16); }}
        QLabel#flat {{ color: rgba(255,255,255,0.7); background: rgba(255,255,255,0.08); }}
        QLabel#ind {{ color: rgba(255,255,255,0.80); font-size: 8.5pt; }}
        QLabel#indv {{ font-size: 10pt; font-weight: bold; }}
        QWidget#sep {{ background: rgba(255,255,255,0.12); }}
        QWidget#news {{ border-radius: 8px; }}
        QWidget#news:hover {{ background: rgba(255,255,255,0.08); }}
        QLabel#ntitle {{ font-size: 9.5pt; }}
        QLabel#nsrc {{ color: #9fb2ff; font-size: 7.5pt; font-weight: bold; }}
        QLabel#nwhen {{ color: rgba(255,255,255,0.45); font-size: 7.5pt; }}
        QLabel#section {{ color: rgba(255,255,255,0.45); font-size: 7.5pt; font-weight: bold; margin-top: 6px; }}
        QLabel#muted {{ color: rgba(255,255,255,0.55); font-size: 8.5pt; }}
        QLabel#big {{ font-size: 20pt; font-weight: 300; }}
        QLabel#strong {{ font-size: 10pt; font-weight: bold; }}
        QLabel#done {{ color: rgba(255,255,255,0.40); text-decoration: line-through; }}
        QLabel#ok {{ color: #5fe0a0; font-weight: bold; }}
        QLabel#warn {{ color: #ffb347; font-weight: bold; }}
        QLabel#late {{ color: #ff8a8a; font-weight: bold; }}
        QWidget#row {{ border-radius: 8px; }}
        QWidget#row:hover {{ background: rgba(255,255,255,0.08); }}
        QPushButton, QToolButton {{ color: white; background: rgba(255,255,255,0.10);
                                    border: 1px solid rgba(255,255,255,0.15); border-radius: 7px; padding: 3px 9px; }}
        QPushButton:hover, QToolButton:hover {{ background: rgba(255,255,255,0.18); }}
        QToolButton#flat {{ background: transparent; border: none; padding: 2px 5px; }}
        QToolButton#flat:hover {{ background: rgba(255,255,255,0.12); }}
        QLineEdit, QComboBox, QDoubleSpinBox {{ color: white; background: rgba(0,0,0,0.25);
                    border: 1px solid rgba(255,255,255,0.18); border-radius: 7px; padding: 3px 6px; }}
        QComboBox QAbstractItemView {{ background: #1f2229; color: #e8eaf0; selection-background-color: #3a4060; }}
        QCheckBox {{ color: white; }}
        QListWidget {{ background: transparent; border: none; color: white; outline: none; }}
        QListWidget::item {{ border-radius: 8px; padding: 2px; }}
        QListWidget::item:hover {{ background: rgba(255,255,255,0.10); }}
        QListWidget::item:selected {{ background: rgba(120,160,255,0.30); }}
    """


class InfoCard(DesktopWindow):
    EXTRA_H = 70  # cabeçalho + margens do card além do conteúdo
    def __init__(self, app, key, title):
        super().__init__(app, _(title))
        self.key, self.loading = key, False
        self.card = QWidget(self, objectName="card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.card)
        lay = QVBoxLayout(self.card)
        lay.setContentsMargins(20, 14, 20, 12)
        lay.setSpacing(4)
        head = QHBoxLayout()
        self.title_lbl = QLabel(_(title).upper(), objectName="ctitle")
        self.meta = QLabel(_("carregando…"), objectName="cmeta")
        head.addWidget(self.title_lbl, 1)
        head.addWidget(self.meta)
        lay.addLayout(head)
        self.scroll = QScrollArea(widgetResizable=True, frameShape=QScrollArea.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content = QWidget(objectName="content")
        self.body = QVBoxLayout(self.content)
        self.body.setContentsMargins(0, 4, 0, 0)
        self.body.setSpacing(4)
        self.scroll.setWidget(self.content)
        lay.addWidget(self.scroll, 1)
        self.grip = Grip(self, min_size=(300, 160))
        self.apply_theme(app.cfg["theme"])
        g = self.geom()
        if "x" in g:
            self.move(g["x"], g["y"])

    def geom(self):
        return self.app.cfg["cards"].setdefault(self.key, {})

    def apply_theme(self, theme):
        self.setStyleSheet(card_style(theme))

    def fit(self):
        """Tamanho escolhido pelo usuário, ou o do conteúdo se ele nunca redimensionou."""
        g = self.geom()
        if "w" in g:
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.resize(g["w"], g["h"])
        else:
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.content.adjustSize()
            self.resize(self.app.cfg.get("card_width", CARD_W), self.content.sizeHint().height() + self.EXTRA_H)

    def resizeEvent(self, ev):
        self.grip.move(self.width() - self.grip.width() - 6, self.height() - self.grip.height() - 4)
        super().resizeEvent(ev)
        self.app.schedule_restack()  # a pilha de cards do Reorganizar se reajusta

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.begin_drag(ev)

    def geometry_changed(self):
        self.geom().update(x=self.x(), y=self.y())
        self.app.cards_moved_by_user()
        self.app.schedule_save()

    def resized_by_user(self):
        self.geom().update(w=self.width(), h=self.height())
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.geometry_changed()

    def contextMenuEvent(self, ev):
        menu = self.app.make_menu()
        menu.addAction(_("Ocultar este card"), self.hide_card)
        if "w" in self.geom():
            menu.addAction(_("Tamanho automático"), self.reset_size)
        menu.addSeparator()
        if type(self).refresh is not InfoCard.refresh:  # só cards que buscam dados
            menu.addAction(_("Atualizar agora"), self.refresh)
        self.extra_menu(menu)
        menu.addSeparator()
        menu.addMenu(self.app.main_menu()).setText(_("Configurações"))
        menu.exec(ev.globalPos())

    def extra_menu(self, menu):
        pass

    def reset_size(self):
        g = self.geom()
        g.pop("w", None)
        g.pop("h", None)
        self.app.schedule_save()
        self.fit()

    def hide_card(self):
        QTimer.singleShot(0, lambda: self.app.toggle_card(self.key, False))

    def clear_body(self):
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                _clear_layout(item.layout())

    def refresh(self):
        """Cards que buscam dados sobrescrevem; os locais (tarefas, favoritos…) não precisam."""


def section(text):
    return QLabel(text, objectName="section")


def _clear_layout(lay):
    while lay.count():
        item = lay.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            _clear_layout(item.layout())


class Sparkline(QWidget):
    def __init__(self, points, up):
        super().__init__()
        self.points, self.up = [p for p in points if p is not None], up
        self.setFixedSize(64, 20)

    def paintEvent(self, _ev):
        pts = self.points
        if len(pts) < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(95, 224, 160) if self.up else QColor(255, 138, 138), 1.6))
        w, h = self.width(), self.height()
        lo, hi = min(pts), max(pts)
        span = (hi - lo) or 1
        poly = [QPointF(i * (w - 2) / (len(pts) - 1) + 1, h - 2 - (v - lo) / span * (h - 4)) for i, v in enumerate(pts)]
        p.drawPolyline(poly)


class MarketCard(InfoCard):
    """Índices, moedas e ações (Yahoo Finance) + Selic/CDI/IPCA (Banco Central)."""

    REFRESH_MS = 5 * 60 * 1000

    def __init__(self, app):
        super().__init__(app, "market", "Mercado")
        self.refresh()
        QTimer(self, interval=self.REFRESH_MS, timeout=self.refresh).start()

    def extra_menu(self, menu):
        menu.addAction(_("Editar ativos…"), self.edit_assets)

    def refresh(self):
        if self.loading:
            return
        self.loading = True
        assets = [list(a) for a in self.app.cfg["market_assets"]]
        run_async(lambda: data.fetch_market(assets), self.show_data)

    def show_data(self, res, err):
        self.loading = False
        if err or not res:
            self.meta.setText(_("sem conexão"))
            return
        quotes, inds = res
        self.clear_body()
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(7)
        for row, (name, sym, kind, price, prev, closes) in enumerate(quotes):
            names = QVBoxLayout()
            names.setSpacing(0)
            names.addWidget(QLabel(_(name), objectName="mkname"))
            names.addWidget(QLabel(sym.replace(".SA", "").replace("=X", ""), objectName="mksub"))
            grid.addLayout(names, row, 0)
            if price is None:
                grid.addWidget(QLabel(_("indisponível"), objectName="mksub", alignment=Qt.AlignRight), row, 1, 1, 3)
                continue
            chg = (price / prev - 1) * 100 if prev else 0.0
            grid.addWidget(Sparkline(closes, chg >= 0), row, 1)
            text = fmt_num(price, 0) if kind == "pts" else f"R$ {fmt_num(price)}" if kind == "brl" else fmt_num(price)
            grid.addWidget(QLabel(text, objectName="mkval", alignment=Qt.AlignRight | Qt.AlignVCenter), row, 2)
            pill = QLabel(f"{'+' if chg > 0 else ''}{fmt_num(chg)}%", alignment=Qt.AlignCenter,
                          objectName="up" if chg > 0.004 else "down" if chg < -0.004 else "flat")
            pill.setMinimumWidth(62)
            grid.addWidget(pill, row, 3, Qt.AlignVCenter)
        grid.setColumnStretch(0, 1)
        self.body.addLayout(grid)
        sep = QWidget(objectName="sep")
        sep.setFixedHeight(1)
        self.body.addSpacing(6)
        self.body.addWidget(sep)
        self.body.addSpacing(4)
        ind = QHBoxLayout()
        for name, v in inds:
            col = QVBoxLayout()
            col.setSpacing(0)
            col.addWidget(QLabel(_(name), objectName="ind", alignment=Qt.AlignCenter))
            col.addWidget(QLabel(f"{fmt_num(v)}%" if v is not None else "—", objectName="indv",
                                 alignment=Qt.AlignCenter))
            ind.addLayout(col)
        self.body.addLayout(ind)
        self.body.addSpacing(6)
        self.body.addWidget(QLabel(_("Fontes: Yahoo Finance · Banco Central · atraso de até 15 min"),
                                   objectName="csrc"))
        self.meta.setText(_("atualizado {t}", t=time.strftime("%H:%M")))
        QTimer.singleShot(0, self.fit)
        QTimer.singleShot(80, self.app.restack_cards)

    def edit_assets(self):
        dlg = QDialog()
        dlg.setWindowTitle(_("Ativos do card de mercado"))
        dlg.resize(460, 420)
        lay = QVBoxLayout(dlg)
        help_ = QLabel(_("Um ativo por linha, no formato  SÍMBOLO = Nome.\nAções da B3: PETR4, VALE3, BBAS3… (o .SA é "
                         "colocado sozinho). Índices: ^BVSP, ^GSPC. Moedas: BRL=X (dólar), EURBRL=X. Cripto: BTC-BRL, "
                         "ETH-BRL."), wordWrap=True)
        lay.addWidget(help_)
        edit = QPlainTextEdit("\n".join(f"{s} = {n}" for s, n, _k in self.app.cfg["market_assets"]))
        edit.setStyleSheet("font-family: monospace;")
        lay.addWidget(edit, 1)
        bb = QDialogButtonBox()
        restore = bb.addButton(_("Restaurar padrão"), QDialogButtonBox.ResetRole)
        bb.addButton(_("Cancelar"), QDialogButtonBox.RejectRole)
        bb.addButton(_("Salvar"), QDialogButtonBox.AcceptRole)
        restore.clicked.connect(lambda: edit.setPlainText("\n".join(f"{s} = {n}" for s, n, _k in DEFAULT_ASSETS)))
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)
        if not dlg.exec():
            return
        assets = []
        for line in edit.toPlainText().splitlines():
            if line.strip():
                sym, _sep, name = line.partition("=")
                sym = data.normalize_symbol(sym)
                assets.append([sym, name.strip() or sym.replace(".SA", ""), data.asset_kind(sym)])
        if assets:
            self.app.cfg["market_assets"] = assets
            self.app.schedule_save()
            self.refresh()


class NewsCard(InfoCard):
    """Manchetes gerais por país, de veículos reconhecidos, mais recentes primeiro."""

    REFRESH_MS = 15 * 60 * 1000

    def __init__(self, app):
        super().__init__(app, "news", "Notícias")
        self.update_title()
        self.refresh()
        QTimer(self, interval=self.REFRESH_MS, timeout=self.refresh).start()

    def country(self):
        c = self.app.cfg["news_country"]
        return c if c in NEWS_COUNTRIES else "br"

    def sources(self):
        c = self.country()
        chosen = self.app.cfg["news_sources"].get(c)
        return default_news_sources(c) if chosen is None else [k for k in chosen if k in NEWS_COUNTRIES[c][1]]

    def update_title(self):
        self.title_lbl.setText(_("NOTÍCIAS · {c}", c=_(NEWS_COUNTRIES[self.country()][0]).upper()))

    def extra_menu(self, menu):
        sub = menu.addMenu(_("País"))
        group = QActionGroup(sub)
        for code, (label, _feeds) in NEWS_COUNTRIES.items():
            act = QAction(_(label), sub, checkable=True, checked=code == self.country())
            act.triggered.connect(lambda _c=False, c=code: self.set_country(c))
            group.addAction(act)
            sub.addAction(act)
        src = menu.addMenu(_("Fontes ({c})", c=_(NEWS_COUNTRIES[self.country()][0])))
        active = self.sources()
        for key, (name, _url, _on) in NEWS_COUNTRIES[self.country()][1].items():
            act = QAction(_(name), src, checkable=True, checked=key in active)
            act.toggled.connect(lambda on, k=key: self.toggle_source(k, on))
            src.addAction(act)

    def set_country(self, code):
        self.app.cfg["news_country"] = code
        self.app.schedule_save()
        self.update_title()
        self.refresh()

    def toggle_source(self, key, on):
        c = self.country()
        srcs = [k for k in self.sources() if k != key] + ([key] if on else [])
        self.app.cfg["news_sources"][c] = [k for k in NEWS_COUNTRIES[c][1] if k in srcs]
        self.app.schedule_save()
        self.refresh()

    def refresh(self):
        if self.loading:
            return
        self.loading = True
        country, keys = self.country(), self.sources()
        run_async(lambda: data.fetch_news(country, keys), self.show_items)

    def show_items(self, items, err):
        self.loading = False
        self.clear_body()
        if not self.sources():
            self.meta.setText("")
            self.info(_("Nenhuma fonte escolhida — botão direito para escolher."))
        elif err or not items:
            self.meta.setText(_("sem conexão"))
            self.info(_("Não foi possível carregar as notícias agora."))
        else:
            for dt, src, title, link in items:
                row = QWidget(objectName="news")
                row.setCursor(Qt.PointingHandCursor)
                row.setToolTip(f"{title}\n\n{_('Clique para abrir no navegador')}")
                rl = QVBoxLayout(row)
                rl.setContentsMargins(6, 5, 6, 5)
                rl.setSpacing(2)
                t = QLabel(title, objectName="ntitle", wordWrap=True)
                rl.addWidget(t)
                meta = QHBoxLayout()
                meta.setSpacing(6)
                meta.addWidget(QLabel(src.upper(), objectName="nsrc"))
                meta.addWidget(QLabel(data.ago(dt) if dt else "", objectName="nwhen"))
                meta.addStretch()
                rl.addLayout(meta)
                row.mousePressEvent = lambda ev, u=link: ev.button() == Qt.LeftButton and \
                    QDesktopServices.openUrl(QUrl(u))
                self.body.addWidget(row)
            self.meta.setText(_("atualizado {t}", t=time.strftime("%H:%M")))
        self.body.addStretch()
        QTimer.singleShot(0, self.fit)

    def info(self, text):
        self.body.addWidget(QLabel(text, objectName="csrc", wordWrap=True))

