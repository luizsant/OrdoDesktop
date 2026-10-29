#!/usr/bin/env python3
"""Ordo Desktop — organizador da área de trabalho: caixas automáticas na área de trabalho + card de relógio.

Inspirado no "Desktop Organizer" do 360 Total Security. Não move nem apaga
arquivos: só agrupa visualmente o conteúdo de ~/Área de trabalho em caixas
por categoria, atualizando sozinho quando algo muda.
"""
import gzip
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import gi

# As caixas dependem de posicionar janelas, o que o Wayland não permite: usa XWayland.
if os.environ.get("XDG_SESSION_TYPE") == "wayland":
    os.environ.setdefault("GDK_BACKEND", "x11")

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk, Pango  # noqa: E402


APP_ID = "br.luizsant.OrdoDesktop"
# Estilos das caixas: chave -> nome no menu
THEMES = {"padrao": "Padrão (degradê)", "vidro": "Vidro claro", "contorno": "Contorno colorido",
          "compacto": "Preto compacto"}
APP_NAME = "Ordo Desktop"
# Extensões que desenham os ícones nativos da área de trabalho (Zorin, Ubuntu, DING GTK4, antiga).
NATIVE_ICON_EXTS = ["zorin-desktop-icons@zorinos.com", "ding@rastersoft.com",
                    "gtk4-ding@smedius.gitlab.com", "desktop-icons@csoriano"]
CONFIG_DIR = os.path.join(GLib.get_user_config_dir(), "ordo-desktop")
OLD_CONFIG_FILE = os.path.join(GLib.get_user_config_dir(), "organizador-desktop", "config.json")  # nome antigo
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
AUTOSTART_FILE = os.path.join(GLib.get_user_config_dir(), "autostart", "ordo-desktop.desktop")
OLD_AUTOSTART_FILE = os.path.join(GLib.get_user_config_dir(), "autostart", "organizador-desktop.desktop")
ICON_SIZE = 48
HEADER_H = 34

# (chave, título, cor de destaque, extensões). Ordem = prioridade de exibição.
CATEGORIES = [
    ("atalhos", "Aplicativos", "#7c8cff", {"desktop"}),
    ("pastas", "Pastas", "#f5c04a", set()),
    ("pdf", "PDFs", "#ff6b6b", {"pdf", "p7s"}),
    ("docs", "Documentos", "#4aa8ff", {"doc", "docx", "odt", "rtf", "txt", "md", "dotx", "pages", "epub"}),
    ("planilhas", "Planilhas", "#3ecf8e", {"xls", "xlsx", "ods", "csv", "tsv", "numbers"}),
    ("apresentacoes", "Apresentações", "#ff9f43", {"ppt", "pptx", "odp", "key"}),
    ("imagens", "Imagens", "#e06cff", {"jpg", "jpeg", "png", "gif", "webp", "bmp", "svg", "heic", "tif", "tiff", "ico"}),
    ("videos", "Vídeos", "#ff5c8a", {"mp4", "mkv", "avi", "mov", "webm", "wmv", "flv", "m4v"}),
    ("audio", "Áudio", "#2ed1c7", {"mp3", "wav", "ogg", "flac", "m4a", "aac", "opus"}),
    ("compactados", "Compactados", "#c0a080", {"zip", "rar", "7z", "tar", "gz", "xz", "bz2", "zst", "tgz"}),
    ("programas", "Instaladores", "#9aa5b1", {"deb", "appimage", "sh", "run", "rpm", "flatpakref", "exe", "msi"}),
    ("outros", "Outros", "#8892a0", set()),
]
CAT_BY_KEY = {c[0]: c for c in CATEGORIES}

CSS = b"""
window.org-window { background-color: transparent; }
.fence {
    background-color: rgba(18, 20, 26, 0.58);
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.09);
}
.fence-header { padding: 6px 12px; border-radius: 14px 14px 0 0; }
.fence-title { color: #ffffff; font-weight: 700; font-size: 10.5pt; }
.fence-count {
    color: rgba(255,255,255,0.75); font-size: 8.5pt;
    background-color: rgba(255,255,255,0.10); border-radius: 9px; padding: 0 7px;
}
.fence-toggle { color: rgba(255,255,255,0.6); font-size: 9pt; }
.fence flowbox { background-color: transparent; padding: 4px 6px 8px 6px; }
.fence flowboxchild { border-radius: 8px; padding: 4px 2px; }
.fence flowboxchild:hover { background-color: rgba(255, 255, 255, 0.10); }
.fence flowboxchild:selected { background-color: rgba(120, 160, 255, 0.30); }
.fence scrolledwindow, .fence viewport { background-color: transparent; }
.item-label { color: #ffffff; font-size: 8.5pt; text-shadow: 0 1px 2px rgba(0,0,0,0.9); }
.grip { color: rgba(255,255,255,0.35); font-size: 8pt; padding: 0 6px 2px 0; }

/* Estilo "Vidro claro" */
.fence.theme-vidro { background-color: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.28); }
.theme-vidro .fence-header { background-color: rgba(255,255,255,0.14); padding: 5px 12px; }
.theme-vidro .fence-title { font-weight: 600; font-size: 10pt; text-shadow: 0 1px 2px rgba(0,0,0,0.5); }
.theme-vidro .fence-count { background-color: transparent; }

/* Estilo "Contorno colorido" (cor da borda vem do CSS de cada caixa) */
.fence.theme-contorno { border-radius: 14px; }
.theme-contorno .fence-header { padding: 8px 12px 2px 12px; }

/* Estilo "Preto compacto" */
.fence.theme-compacto { background-color: rgba(6,7,10,0.86); border: none; border-radius: 10px; }
.theme-compacto .fence-header { border-bottom: 1px solid rgba(255,255,255,0.08); border-radius: 10px 10px 0 0; padding: 7px 12px; }
.theme-compacto .fence-title { font-size: 8pt; font-weight: 600; letter-spacing: 1.5px; color: rgba(255,255,255,0.75); }
.theme-compacto .fence-count { background-color: transparent; color: rgba(255,255,255,0.6); }
.theme-compacto .fence-toggle { font-size: 7.5pt; }
.drop-hover { border: 1px dashed rgba(255,255,255,0.6); }

.clock-card {
    background-color: rgba(18, 20, 26, 0.55);
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.09);
    padding: 14px 26px 16px 26px;
}
.clock-time { color: #ffffff; font-size: 46pt; font-weight: 300; }
.clock-sec { color: rgba(255,255,255,0.55); font-size: 18pt; font-weight: 300; }
.clock-date { color: rgba(255,255,255,0.85); font-size: 12pt; }
.clock-extra { color: rgba(255,255,255,0.55); font-size: 9.5pt; }

.gadget-sep { background-color: rgba(255,255,255,0.12); min-height: 1px; margin: 12px 0 8px 0; }
.gadget-section { color: rgba(255,255,255,0.45); font-size: 7.5pt; font-weight: 700; margin: 2px 0 4px 2px; }
.stat-label { color: rgba(255,255,255,0.70); font-size: 8.5pt; }
.stat-value { color: rgba(255,255,255,0.90); font-size: 8.5pt; }
.clock-card progressbar trough { min-height: 6px; background-color: rgba(255,255,255,0.12); border-radius: 3px; border: none; }
.clock-card progressbar progress { min-height: 6px; border-radius: 3px; border: none; background-color: #7c8cff; }
.clock-card progressbar.warn progress { background-color: #ff9f43; }
.clock-card progressbar.crit progress { background-color: #ff5c5c; }
.gadget-btn {
    background: transparent; border: none; box-shadow: none; border-radius: 10px;
    padding: 6px 0; min-width: 76px; color: #ffffff;
}
.gadget-btn:hover { background-color: rgba(255,255,255,0.12); }
.gadget-btn:active { background-color: rgba(255,255,255,0.20); }
.gadget-btn.on { background-color: rgba(124,140,255,0.35); }
.gadget-btn label { color: rgba(255,255,255,0.88); font-size: 8pt; }
.note-view, .note-view text {
    background-color: rgba(0,0,0,0.25); color: #ffffff; caret-color: #ffffff;
    border-radius: 8px; font-size: 9.5pt;
}
.note-view { padding: 6px 8px; border: 1px solid rgba(255,255,255,0.15); }

.wx-temp { color: #ffffff; font-size: 28pt; font-weight: 300; }
.wx-desc { color: #ffffff; font-size: 10.5pt; font-weight: 600; }
.wx-info { color: rgba(255,255,255,0.65); font-size: 8.5pt; }
.wx-day { color: rgba(255,255,255,0.75); font-size: 8pt; }
.wx-day-temp { color: #ffffff; font-size: 8.5pt; }
.wx-day-min { color: rgba(255,255,255,0.5); font-size: 8.5pt; }
.wx-icon { color: #ffd76a; }

.card-title { color: rgba(255,255,255,0.55); font-size: 8pt; font-weight: 700; letter-spacing: 1px; }
.card-meta { color: rgba(255,255,255,0.40); font-size: 8pt; }
.mk-name { color: #ffffff; font-size: 9.5pt; font-weight: 600; }
.mk-sub { color: rgba(255,255,255,0.45); font-size: 7.5pt; }
.mk-val { color: #ffffff; font-size: 9.5pt; }
.mk-chg { font-size: 8.5pt; font-weight: 700; border-radius: 6px; padding: 1px 6px; }
.mk-up { color: #5fe0a0; background-color: rgba(62,207,142,0.16); }
.mk-down { color: #ff8a8a; background-color: rgba(255,92,92,0.16); }
.mk-flat { color: rgba(255,255,255,0.7); background-color: rgba(255,255,255,0.08); }
.mk-ind { color: rgba(255,255,255,0.80); font-size: 8.5pt; }
.mk-ind-val { color: #ffffff; font-size: 10pt; font-weight: 600; }
.news-row { border-radius: 8px; padding: 6px 6px; }
.news-row:hover { background-color: rgba(255,255,255,0.08); }
.news-title { color: #ffffff; font-size: 9.5pt; }
.news-meta { color: rgba(255,255,255,0.45); font-size: 7.5pt; }
.news-src { color: #9fb2ff; font-size: 7.5pt; font-weight: 700; }

.sticky { border-radius: 14px; box-shadow: 0 4px 14px rgba(0,0,0,0.35); }
.sticky-head { border-radius: 14px 14px 0 0; padding: 4px 6px 4px 12px; }
.sticky-date { font-size: 8pt; font-weight: 700; color: rgba(0,0,0,0.55); }
.sticky-btn { background: transparent; border: none; box-shadow: none; padding: 2px 4px; min-height: 0; min-width: 0;
              color: rgba(0,0,0,0.55); }
.sticky-btn:hover { background-color: rgba(0,0,0,0.10); border-radius: 6px; }
.sticky-title, .sticky-title:focus {
    background: transparent; border: none; box-shadow: none; outline: none;
    color: #1d1d24; font-size: 15pt; font-weight: 800; padding: 6px 14px 0 14px;
}
.sticky-text, .sticky-text text { background-color: transparent; color: #2b2b35; caret-color: #2b2b35; font-size: 10.5pt; }
.sticky-text { padding: 4px 14px 6px 14px; }
.sticky .grip { color: rgba(0,0,0,0.30); }
.sticky scrolledwindow, .sticky viewport, .sticky eventbox { background-color: transparent; }
.sticky > eventbox:last-child { border-radius: 0 0 14px 14px; }
"""

# cor: (fundo, cabeçalho)
NOTE_COLORS = {
    "amarelo": ("#fff1d0", "#ffc98a"),
    "lilas": ("#efe4ff", "#c9a7ff"),
    "azul": ("#e1e9ff", "#a3b8ff"),
    "verde": ("#dcf5e3", "#93dcab"),
    "rosa": ("#ffe1ea", "#ffa3bf"),
    "cinza": ("#eceef2", "#b9bfca"),
}
NOTE_COLOR_NAMES = {"amarelo": "Amarelo", "lilas": "Lilás", "azul": "Azul", "verde": "Verde", "rosa": "Rosa",
                    "cinza": "Cinza"}

# Ativos do card de mercado: (símbolo no Yahoo Finance, nome exibido, tipo de valor)
DEFAULT_ASSETS = [
    ["^BVSP", "Ibovespa", "pts"], ["^GSPC", "S&P 500", "pts"], ["^IXIC", "Nasdaq", "pts"],
    ["BRL=X", "Dólar", "brl"], ["EURBRL=X", "Euro", "brl"], ["BTC-BRL", "Bitcoin", "brl"],
    ["PETR4.SA", "Petrobras", "brl"], ["VALE3.SA", "Vale", "brl"], ["ITUB4.SA", "Itaú", "brl"],
]
# Indicadores do Banco Central (API SGS, oficial): código da série -> nome
BCB_SERIES = [(432, "Selic"), (4389, "CDI"), (13522, "IPCA 12m")]
# Feeds RSS públicos de notícias
NEWS_FEEDS = {
    "infomoney": ("InfoMoney", "https://www.infomoney.com.br/feed/"),
    "valor": ("Valor", "https://valor.globo.com/rss/valor"),
    "agenciabrasil": ("Agência Brasil", "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml"),
    "g1": ("G1 Economia", "https://g1.globo.com/rss/g1/economia/"),
    "cnn": ("CNN Brasil", "https://www.cnnbrasil.com.br/feed/"),
    "exame": ("Exame", "https://exame.com/feed/"),
    "moneytimes": ("Money Times", "https://www.moneytimes.com.br/feed/"),
    "poder360": ("Poder360", "https://www.poder360.com.br/feed/"),
}

# Códigos WMO do Open-Meteo -> (descrição, ícone de dia, ícone de noite)
WEATHER_CODES = {
    0: ("Céu limpo", "weather-clear-symbolic", "weather-clear-night-symbolic"),
    1: ("Predomínio de sol", "weather-few-clouds-symbolic", "weather-few-clouds-night-symbolic"),
    2: ("Parcialmente nublado", "weather-few-clouds-symbolic", "weather-few-clouds-night-symbolic"),
    3: ("Nublado", "weather-overcast-symbolic", "weather-overcast-symbolic"),
    45: ("Neblina", "weather-fog-symbolic", "weather-fog-symbolic"),
    48: ("Neblina com geada", "weather-fog-symbolic", "weather-fog-symbolic"),
    51: ("Garoa fraca", "weather-showers-scattered-symbolic", "weather-showers-scattered-symbolic"),
    53: ("Garoa", "weather-showers-scattered-symbolic", "weather-showers-scattered-symbolic"),
    55: ("Garoa forte", "weather-showers-symbolic", "weather-showers-symbolic"),
    61: ("Chuva fraca", "weather-showers-scattered-symbolic", "weather-showers-scattered-symbolic"),
    63: ("Chuva", "weather-showers-symbolic", "weather-showers-symbolic"),
    65: ("Chuva forte", "weather-showers-symbolic", "weather-showers-symbolic"),
    71: ("Neve fraca", "weather-snow-symbolic", "weather-snow-symbolic"),
    73: ("Neve", "weather-snow-symbolic", "weather-snow-symbolic"),
    75: ("Neve forte", "weather-snow-symbolic", "weather-snow-symbolic"),
    80: ("Pancadas de chuva", "weather-showers-scattered-symbolic", "weather-showers-scattered-symbolic"),
    81: ("Pancadas de chuva", "weather-showers-symbolic", "weather-showers-symbolic"),
    82: ("Pancadas fortes", "weather-storm-symbolic", "weather-storm-symbolic"),
    95: ("Trovoadas", "weather-storm-symbolic", "weather-storm-symbolic"),
    96: ("Trovoadas com granizo", "weather-storm-symbolic", "weather-storm-symbolic"),
    99: ("Trovoadas com granizo", "weather-storm-symbolic", "weather-storm-symbolic"),
}



def desktop_dir():
    return GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP) or os.path.expanduser("~/Desktop")


def load_config():
    # Era "Organizador de Desktop": aproveita caixas, notas e posições já salvas.
    path = CONFIG_FILE if os.path.exists(CONFIG_FILE) or not os.path.exists(OLD_CONFIG_FILE) else OLD_CONFIG_FILE
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError):
        cfg = {}
    cfg.setdefault("boxes", {})
    cfg.setdefault("clock", {})
    cfg.setdefault("show_seconds", True)
    cfg.setdefault("show_clock", True)
    cfg.setdefault("hide_native", True)
    cfg.setdefault("show_hidden", False)
    cfg.setdefault("show_gadgets", True)
    cfg.setdefault("theme", "padrao")
    cfg.setdefault("show_market", True)
    cfg.setdefault("show_news", True)
    cfg.setdefault("market_assets", DEFAULT_ASSETS)
    cfg.setdefault("news_sources", ["infomoney", "valor", "agenciabrasil"])
    cfg.setdefault("cards", {})  # posição dos cards de mercado/notícias
    cfg.setdefault("autostart", True)
    cfg.setdefault("note", "")
    cfg.setdefault("notes", [])
    cfg.setdefault("weather_city", None)  # escolhida pelo usuário no primeiro uso
    cfg.setdefault("native_disabled", [])  # extensões que o Ordo desligou (para religar mesmo após travar)
    cfg.setdefault("timer_min", 25)
    cfg.setdefault("overrides", {})  # nome do arquivo -> caixa escolhida pelo usuário
    return cfg


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = CONFIG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONFIG_FILE)


def categorize(name, is_dir):
    if is_dir:
        return "pastas"
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    for key, _t, _c, exts in CATEGORIES:
        if ext in exts:
            return key
    return "outros"


def workarea():
    display = Gdk.Display.get_default()
    mon = display.get_primary_monitor() or display.get_monitor(0)
    return mon.get_workarea()


def active_native_icon_exts():
    """Extensões de ícones nativos que estão ligadas agora."""
    active = []
    for uuid in NATIVE_ICON_EXTS:
        try:
            out = subprocess.run(["gnome-extensions", "info", uuid], capture_output=True, text=True,
                                 timeout=5).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        # O rótulo é traduzido ("Estado:"/"State:"), o valor não.
        if re.search(r":\s*(ACTIVE|ENABLED)\b", out):
            active.append(uuid)
    return active


def set_extensions(uuids, enabled):
    for uuid in uuids:
        try:
            subprocess.run(["gnome-extensions", "enable" if enabled else "disable", uuid], timeout=5, check=False)
        except (OSError, subprocess.SubprocessError):
            pass


def setup_transparent(win):
    win.get_style_context().add_class("org-window")
    visual = win.get_screen().get_rgba_visual()
    if visual:
        win.set_visual(visual)
    win.set_app_paintable(True)
    win.set_decorated(False)
    win.set_skip_taskbar_hint(True)
    win.set_skip_pager_hint(True)
    if os.environ.get("ORG_TEST_ABOVE"):  # só para capturas de teste
        win.set_keep_above(True)
    else:
        win.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        win.set_keep_below(True)
    win.stick()


class WindowDragger:
    """Move/redimensiona a janela na mão: o Mutter não aceita begin_move_drag em janelas tipo DESKTOP."""

    SNAP = 8

    def __init__(self, widget, win, mode, cursor):
        self.win, self.mode, self.start = win, mode, None
        widget.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK
                          | Gdk.EventMask.BUTTON1_MOTION_MASK)
        widget.connect("motion-notify-event", self.on_motion)
        widget.connect("button-release-event", self.on_release)
        widget.connect("realize", lambda w: w.get_window().set_cursor(
            Gdk.Cursor.new_from_name(w.get_display(), cursor)))

    @staticmethod
    def pointer(ev):
        # x_root do evento fica defasado enquanto a própria janela anda; o ponteiro real não.
        _screen, px, py = ev.get_device().get_position()
        return px, py

    def begin(self, ev):
        x, y = self.win.get_position()
        w, h = self.win.get_size()
        self.start = (*self.pointer(ev), x, y, w, h)

    def on_motion(self, _w, ev):
        if not self.start:
            return False
        sx, sy, x, y, w, h = self.start
        px, py = self.pointer(ev)
        dx, dy = px - sx, py - sy
        snap = lambda v: int(round(v / self.SNAP) * self.SNAP)  # noqa: E731
        if self.mode == "move":
            wa = workarea()
            nx = min(max(snap(x + dx), wa.x), wa.x + wa.width - 60)
            ny = min(max(snap(y + dy), wa.y), wa.y + wa.height - HEADER_H)
            self.win.move(nx, ny)
        else:
            self.win.resize(max(160, snap(w + dx)), max(HEADER_H + 60, snap(h + dy)))
        return True

    def on_release(self, _w, _ev):
        self.start = None
        return False


class DesktopItem:
    """Um arquivo/pasta/atalho presente na área de trabalho."""

    def __init__(self, gfile, info):
        self.gfile = gfile
        self.path = gfile.get_path()
        self.name = info.get_name()
        self.is_dir = info.get_file_type() == Gio.FileType.DIRECTORY
        self.category = categorize(self.name, self.is_dir)
        self.display_name = info.get_display_name()
        self.gicon = info.get_icon()
        self.thumb = info.get_attribute_byte_string(Gio.FILE_ATTRIBUTE_THUMBNAIL_PATH)
        self.app_info = None
        if self.category == "atalhos":
            try:
                self.app_info = Gio.DesktopAppInfo.new_from_filename(self.path)
            except TypeError:
                self.app_info = None
            if self.app_info:
                self.display_name = self.app_info.get_display_name() or self.display_name
                if self.app_info.get_icon():
                    self.gicon = self.app_info.get_icon()
            else:
                self._read_keyfile()
        self.sort_key = GLib.utf8_collate_key_for_filename(self.display_name, -1)

    def _read_keyfile(self):
        """Atalhos que o GIO recusa (ex.: NoDisplay/Exec ausente): lê Name/Icon direto."""
        kf = GLib.KeyFile()
        try:
            kf.load_from_file(self.path, GLib.KeyFileFlags.NONE)
            self.display_name = kf.get_locale_string("Desktop Entry", "Name", None) or self.display_name
            icon = kf.get_string("Desktop Entry", "Icon")
            self.gicon = Gio.FileIcon.new(Gio.File.new_for_path(icon)) if icon.startswith("/") \
                else Gio.ThemedIcon.new(icon)
        except GLib.Error:
            pass

    def pixbuf(self, size=ICON_SIZE):
        if self.thumb and os.path.exists(self.thumb):
            try:
                return GdkPixbuf.Pixbuf.new_from_file_at_scale(self.thumb, size, size, True)
            except GLib.Error:
                pass
        theme = Gtk.IconTheme.get_default()
        if self.gicon:
            info = theme.lookup_by_gicon(self.gicon, size, Gtk.IconLookupFlags.FORCE_SIZE)
            if info:
                try:
                    return info.load_icon()
                except GLib.Error:
                    pass
        return theme.load_icon("text-x-generic", size, Gtk.IconLookupFlags.FORCE_SIZE)

    def open(self):
        try:
            if self.app_info:
                self.app_info.launch([], None)
            elif self.category == "atalhos":
                kf = GLib.KeyFile()
                kf.load_from_file(self.path, GLib.KeyFileFlags.NONE)
                cmd = " ".join(t for t in kf.get_string("Desktop Entry", "Exec").split()
                               if not (len(t) == 2 and t[0] == "%"))
                GLib.spawn_command_line_async(cmd)
            else:
                Gio.AppInfo.launch_default_for_uri(self.gfile.get_uri(), None)
        except GLib.Error as e:
            show_error(f"Não foi possível abrir “{self.display_name}”.", e.message)


def show_error(title, detail=""):
    dlg = Gtk.MessageDialog(message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK, text=title)
    if detail:
        dlg.format_secondary_text(detail)
    dlg.run()
    dlg.destroy()


def scan_desktop(show_hidden=False):
    d = Gio.File.new_for_path(desktop_dir())
    attrs = ",".join([
        "standard::name", "standard::display-name", "standard::icon", "standard::type",
        "standard::is-hidden", "standard::is-backup", "thumbnail::path",
    ])
    items = []
    try:
        en = d.enumerate_children(attrs, Gio.FileQueryInfoFlags.NONE, None)
    except GLib.Error:
        return items
    for info in en:
        if not show_hidden and (info.get_is_hidden() or info.get_is_backup()):
            continue
        items.append(DesktopItem(d.get_child(info.get_name()), info))
    en.close(None)
    return items


class Fence(Gtk.Window):
    """Uma caixa (estilo Fences/360) com os itens de uma categoria."""

    def __init__(self, app, key):
        super().__init__(title=f"{APP_NAME} — {CAT_BY_KEY[key][1]}")
        self.app = app
        self.key = key
        _k, title, color, _e = CAT_BY_KEY[key]
        setup_transparent(self)
        self._save_id = 0

        css = Gtk.CssProvider()
        css.load_from_data(
            f".theme-padrao .fence-header.cat-{key} {{ border-bottom: 2px solid {color}; "
            f"background-image: linear-gradient(to bottom, alpha({color}, 0.22), alpha({color}, 0.04)); }}\n"
            f".fence.theme-contorno.cat-{key} {{ border: 2px solid alpha({color}, 0.75); "
            f"background-color: alpha({color}, 0.10); }}\n"
            f".theme-contorno .cat-{key} .fence-title {{ color: mix({color}, white, 0.45); }}".encode()
        )
        Gtk.StyleContext.add_provider_for_screen(self.get_screen(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)

        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.get_style_context().add_class("fence")
        frame.get_style_context().add_class(f"cat-{key}")
        self.frame = frame
        self.add(frame)

        header_ev = Gtk.EventBox()
        header = Gtk.Box(spacing=8)
        header.get_style_context().add_class("fence-header")
        header.get_style_context().add_class(f"cat-{key}")
        self.toggle_lbl = Gtk.Label()
        self.toggle_lbl.get_style_context().add_class("fence-toggle")
        title_lbl = Gtk.Label(label=title, xalign=0)
        title_lbl.get_style_context().add_class("fence-title")
        self.title_lbl, self.title = title_lbl, title
        self.count_lbl = Gtk.Label()
        self.count_lbl.get_style_context().add_class("fence-count")
        header.pack_start(self.toggle_lbl, False, False, 0)
        header.pack_start(title_lbl, True, True, 0)
        header.pack_end(self.count_lbl, False, False, 0)
        header_ev.add(header)
        header_ev.set_size_request(-1, HEADER_H)
        header_ev.connect("button-press-event", self.on_header_press)
        self.mover = WindowDragger(header_ev, self, "move", "grab")
        frame.pack_start(header_ev, False, False, 0)

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.flow = Gtk.FlowBox()
        self.flow.set_valign(Gtk.Align.START)
        self.flow.set_homogeneous(True)
        self.flow.set_max_children_per_line(30)
        self.flow.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flow.set_activate_on_single_click(False)
        self.flow.connect("child-activated", lambda _f, child: child.item.open())
        self.flow.set_sort_func(lambda a, b: (a.item.sort_key > b.item.sort_key) - (a.item.sort_key < b.item.sort_key))
        self.scroll.add(self.flow)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        body.pack_start(self.scroll, True, True, 0)
        grip_ev = Gtk.EventBox()
        grip = Gtk.Label(label="◢", xalign=1)
        grip.get_style_context().add_class("grip")
        grip_ev.add(grip)
        grip_ev.connect("button-press-event", self.on_grip_press)
        self.resizer = WindowDragger(grip_ev, self, "resize", "se-resize")
        body.pack_end(grip_ev, False, False, 0)
        self.body = body
        frame.pack_start(body, True, True, 0)

        # Soltar arquivos numa caixa = mover para a área de trabalho.
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.MOVE | Gdk.DragAction.COPY)
        self.drag_dest_add_uri_targets()
        self.connect("drag-data-received", self.on_drop)

        self.connect("configure-event", self.on_configure)
        # Botão direito em qualquer área vazia da caixa abre o menu de configurações.
        self.connect("button-press-event", lambda _w, ev: ev.button == 3 and (self.app.popup_main_menu(ev) or True))
        frame.show_all()
        self.apply_theme(app.cfg["theme"])
        self.apply_geometry()

    def apply_theme(self, theme):
        ctx = self.frame.get_style_context()
        for t in THEMES:
            ctx.remove_class(f"theme-{t}")
        ctx.add_class(f"theme-{theme}")
        # GTK3 não tem text-transform: o caixa-alta do estilo compacto é feito aqui.
        self.title_lbl.set_text(self.title.upper() if theme == "compacto" else self.title)
        self.title_lbl.set_xalign(0.5 if theme == "vidro" else 0)

    # ---- geometria ----
    def geom(self):
        return self.app.cfg["boxes"].setdefault(self.key, {})

    def apply_geometry(self):
        g = self.geom()
        self.move(g.get("x", 40), g.get("y", 40))
        self.collapsed = g.get("collapsed", False)
        self.body.set_visible(not self.collapsed)
        self.toggle_lbl.set_text("▸" if self.collapsed else "▾")
        h = HEADER_H if self.collapsed else g.get("h", 220)
        self.set_size_request(160, HEADER_H)
        self.resize(g.get("w", 340), h)

    def on_configure(self, _w, ev):
        g = self.geom()
        g["x"], g["y"] = ev.x, ev.y
        g["w"] = ev.width
        if not self.collapsed:
            g["h"] = ev.height
        self.app.schedule_save()
        return False

    def on_header_press(self, _w, ev):
        if ev.button == 1 and ev.type == Gdk.EventType._2BUTTON_PRESS:
            self.toggle_collapse()
        elif ev.button == 1 and ev.type == Gdk.EventType.BUTTON_PRESS:
            self.mover.begin(ev)
        elif ev.button == 3:
            self.app.popup_main_menu(ev)
        return True

    def on_grip_press(self, _w, ev):
        if ev.button == 1:
            self.resizer.begin(ev)
        return True

    def toggle_collapse(self):
        g = self.geom()
        g["collapsed"] = not self.collapsed
        self.apply_geometry()
        self.app.schedule_save()

    # ---- conteúdo ----
    def set_items(self, items):
        for child in self.flow.get_children():
            child.destroy()
        for it in items:
            self.flow.add(self.make_tile(it))
        self.flow.show_all()
        self.count_lbl.set_text(str(len(items)))

    def make_tile(self, item):
        child = Gtk.FlowBoxChild()
        child.item = item
        ev = Gtk.EventBox()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        img = Gtk.Image.new_from_pixbuf(item.pixbuf())
        lbl = Gtk.Label(label=item.display_name)
        lbl.set_line_wrap(True)
        lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        lbl.set_lines(2)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        lbl.set_max_width_chars(11)
        lbl.set_width_chars(11)
        lbl.set_justify(Gtk.Justification.CENTER)
        lbl.get_style_context().add_class("item-label")
        box.pack_start(img, False, False, 0)
        box.pack_start(lbl, False, False, 0)
        ev.add(box)
        ev.set_tooltip_text(item.display_name)
        ev.connect("button-press-event", self.on_item_press, child)

        ev.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.COPY | Gdk.DragAction.MOVE)
        ev.drag_source_add_uri_targets()
        ev.connect("drag-begin", lambda w, ctx: Gtk.drag_set_icon_pixbuf(ctx, item.pixbuf(), 0, 0))
        ev.connect("drag-data-get", lambda w, ctx, data, info, t: data.set_uris([item.gfile.get_uri()]))
        child.add(ev)
        return child

    def on_item_press(self, _w, ev, child):
        if ev.button == 3:
            self.flow.select_child(child)
            self.item_menu(child.item).popup_at_pointer(ev)
            return True
        return False

    def item_menu(self, item):
        menu = Gtk.Menu()

        def add(label, cb):
            mi = Gtk.MenuItem(label=label)
            mi.connect("activate", lambda _m: cb())
            menu.append(mi)

        add("Abrir", item.open)
        add("Mostrar no Gerenciador de Arquivos", lambda: show_in_files(item.gfile))
        add("Renomear…", lambda: self.app.rename_item(item))
        add("Copiar caminho", lambda: Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(item.path, -1))

        sub = Gtk.Menu()
        for key, title, _c, _e in CATEGORIES:
            if key != item.category:
                mi = Gtk.MenuItem(label=title)
                mi.connect("activate", lambda _m, k=key: self.app.assign_box(item.name, k))
                sub.append(mi)
        if item.name in self.app.cfg["overrides"]:
            sub.append(Gtk.SeparatorMenuItem())
            mi = Gtk.MenuItem(label="Voltar para a caixa automática")
            mi.connect("activate", lambda _m: self.app.assign_box(item.name, None))
            sub.append(mi)
        mover = Gtk.MenuItem(label="Mover para a caixa")
        mover.set_submenu(sub)
        menu.append(mover)
        menu.append(Gtk.SeparatorMenuItem())
        add("Mover para a lixeira", lambda: self.app.trash_item(item))
        menu.show_all()
        menu.attach_to_widget(self, None)
        return menu

    def on_drop(self, _w, ctx, _x, _y, data, _info, time):
        dest_dir = Gio.File.new_for_path(desktop_dir())
        for uri in data.get_uris() or []:
            src = Gio.File.new_for_uri(uri)
            parent = src.get_parent()
            if parent and parent.equal(dest_dir):
                self.app.assign_box(src.get_basename(), self.key)  # já está no desktop: só troca de caixa
                continue
            target = dest_dir.get_child(src.get_basename())
            if target.query_exists(None):
                show_error(f"Já existe “{src.get_basename()}” na área de trabalho.")
                continue
            try:
                src.move(target, Gio.FileCopyFlags.NONE, None, None, None)
            except GLib.Error as e:
                show_error(f"Não foi possível mover “{src.get_basename()}”.", e.message)
        Gtk.drag_finish(ctx, True, False, time)


def show_in_files(gfile):
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    try:
        bus.call_sync("org.freedesktop.FileManager1", "/org/freedesktop/FileManager1",
                      "org.freedesktop.FileManager1", "ShowItems",
                      GLib.Variant("(ass)", ([gfile.get_uri()], "")), None,
                      Gio.DBusCallFlags.NONE, 3000, None)
    except GLib.Error:
        parent = gfile.get_parent()
        if parent:
            Gio.AppInfo.launch_default_for_uri(parent.get_uri(), None)


def spawn(*argv):
    try:
        subprocess.Popen(argv, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as e:
        show_error(f"Não foi possível abrir “{argv[0]}”.", str(e))


def notify(title, body, sound="complete"):
    spawn("notify-send", "-a", APP_NAME, "-i", "alarm-symbolic", title, body)
    spawn("canberra-gtk-play", "-i", sound)


class SysStats:
    """CPU (delta de /proc/stat), memória e disco da pasta pessoal."""

    def __init__(self):
        self.prev = self._cpu_times()

    @staticmethod
    def _cpu_times():
        with open("/proc/stat") as f:
            vals = list(map(int, f.readline().split()[1:]))
        idle = vals[3] + vals[4]
        return sum(vals), idle

    def cpu(self):
        total, idle = self._cpu_times()
        pt, pi = self.prev
        self.prev = (total, idle)
        dt = total - pt
        return 0.0 if dt <= 0 else 1 - (idle - pi) / dt

    @staticmethod
    def mem():
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":", 1)
                info[k] = int(v.split()[0])
        total = info["MemTotal"]
        used = total - info.get("MemAvailable", info["MemFree"])
        return used / total, used / 1048576, total / 1048576

    @staticmethod
    def disk():
        st = os.statvfs(os.path.expanduser("~"))
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        return 1 - free / total, free / 1e9


class GadgetPanel(Gtk.Box):
    """Utilitários abaixo do relógio: uso do sistema, atalhos rápidos, timer de foco e nota."""

    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.stats = SysStats()
        self.timer_end = None
        self._note_id = 0

        sep = Gtk.Box()
        sep.get_style_context().add_class("gadget-sep")
        self.pack_start(sep, False, False, 0)

        # --- clima ---
        self.weather = WeatherWidget(app)
        self.pack_start(self.weather, False, False, 0)
        self.pack_start(self.section("SISTEMA"), False, False, 0)

        # --- uso do sistema ---
        grid = Gtk.Grid(column_spacing=10, row_spacing=5)
        self.bars = {}
        for row, (key, label) in enumerate([("cpu", "CPU"), ("mem", "Memória"), ("disk", "Disco")]):
            lbl = Gtk.Label(label=label, xalign=0)
            lbl.get_style_context().add_class("stat-label")
            bar = Gtk.ProgressBar(hexpand=True, valign=Gtk.Align.CENTER)
            val = Gtk.Label(xalign=1, width_chars=14)
            val.get_style_context().add_class("stat-value")
            grid.attach(lbl, 0, row, 1, 1)
            grid.attach(bar, 1, row, 1, 1)
            grid.attach(val, 2, row, 1, 1)
            self.bars[key] = (bar, val)
        self.pack_start(grid, False, False, 0)

        # --- atalhos ---
        self.pack_start(self.section("ATALHOS"), False, False, 0)
        buttons = Gtk.Grid(column_homogeneous=True, row_spacing=2, column_spacing=2)
        self.btn = {}
        defs = [
            ("organize", "view-grid-symbolic", "Reorganizar", self.app.auto_layout),
            ("shot", "camera-photo-symbolic", "Captura", self.screenshot),
            ("calc", "accessories-calculator-symbolic", "Calculadora", lambda: spawn("gnome-calculator")),
            ("term", "utilities-terminal-symbolic", "Terminal", lambda: spawn("gnome-terminal")),
            ("down", "folder-download-symbolic", "Downloads", self.open_downloads),
            ("trash", "user-trash-symbolic", "Lixeira", lambda: spawn("nautilus", "trash:///")),
            ("lock", "system-lock-screen-symbolic", "Bloquear", self.lock_screen),
            ("dnd", "notifications-disabled-symbolic", "Não perturbe", self.toggle_dnd),
            ("timer", "alarm-symbolic", "Foco", self.toggle_timer),
            ("collapse", "go-up-symbolic", "Recolher", self.toggle_collapse_all),
            ("monitor", "utilities-system-monitor-symbolic", "Monitor", lambda: spawn("gnome-system-monitor")),
            ("note", "document-new-symbolic", "Nova nota", lambda: self.app.new_note()),
        ]
        for i, (key, icon, label, cb) in enumerate(defs):
            b = self.make_button(icon, label, cb)
            self.btn[key] = b
            buttons.attach(b, i % 4, i // 4, 1, 1)
        self.btn["timer"].connect("button-press-event", self.on_timer_press)
        self.btn["timer"].set_tooltip_text("Clique para iniciar/parar · botão direito escolhe a duração")
        self.btn["shot"].set_tooltip_text("Abre a ferramenta de captura de tela (tecla Print)")
        self.btn["organize"].set_tooltip_text("Reorganiza as caixas automaticamente")
        self.pack_start(buttons, False, False, 0)


        self.dnd_settings = Gio.Settings.new("org.gnome.desktop.notifications")
        self.dnd_settings.connect("changed::show-banners", lambda *_a: self.sync_dnd())
        self.sync_dnd()
        self.update_stats()
        GLib.timeout_add_seconds(2, self.update_stats)

    @staticmethod
    def section(text):
        lbl = Gtk.Label(label=text, xalign=0)
        lbl.get_style_context().add_class("gadget-section")
        lbl.set_margin_top(10)
        return lbl

    @staticmethod
    def make_button(icon, label, cb):
        b = Gtk.Button(relief=Gtk.ReliefStyle.NONE)
        b.get_style_context().add_class("gadget-btn")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        b.icon = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.LARGE_TOOLBAR)
        b.lbl = Gtk.Label(label=label)
        box.pack_start(b.icon, False, False, 0)
        box.pack_start(b.lbl, False, False, 0)
        b.add(box)
        b.connect("clicked", lambda _b: cb())
        return b

    # ---- sistema ----
    def set_bar(self, key, frac, text):
        bar, val = self.bars[key]
        bar.set_fraction(min(max(frac, 0), 1))
        ctx = bar.get_style_context()
        ctx.remove_class("warn")
        ctx.remove_class("crit")
        if frac >= 0.9:
            ctx.add_class("crit")
        elif frac >= 0.75:
            ctx.add_class("warn")
        val.set_text(text)

    def update_stats(self):
        cpu = self.stats.cpu()
        self.set_bar("cpu", cpu, f"{cpu * 100:.0f}%")
        frac, used, total = self.stats.mem()
        self.set_bar("mem", frac, f"{used:.1f} / {total:.0f} GB")
        frac, free = self.stats.disk()
        self.set_bar("disk", frac, f"{free:.0f} GB livres")
        try:
            n = Gio.File.new_for_uri("trash:///").query_info(
                "trash::item-count", Gio.FileQueryInfoFlags.NONE, None).get_attribute_uint32("trash::item-count")
            self.btn["trash"].lbl.set_text(f"Lixeira ({n})" if n else "Lixeira")
        except GLib.Error:
            pass
        collapsed = bool(self.app.fences) and all(f.collapsed for f in self.app.fences.values())
        self.btn["collapse"].lbl.set_text("Expandir" if collapsed else "Recolher")
        self.btn["collapse"].icon.set_from_icon_name("go-down-symbolic" if collapsed else "go-up-symbolic",
                                                     Gtk.IconSize.LARGE_TOOLBAR)
        return True

    # ---- ações ----
    def screenshot(self):
        # Simula a tecla Print (abre a interface de captura do GNOME) depois que o clique terminar.
        GLib.timeout_add(200, lambda: spawn("xdotool", "key", "Print") or False)

    def open_downloads(self):
        path = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) or os.path.expanduser("~")
        Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(path).get_uri(), None)

    def lock_screen(self):
        try:
            Gio.bus_get_sync(Gio.BusType.SESSION, None).call_sync(
                "org.gnome.ScreenSaver", "/org/gnome/ScreenSaver", "org.gnome.ScreenSaver", "Lock",
                None, None, Gio.DBusCallFlags.NONE, 3000, None)
        except GLib.Error:
            spawn("loginctl", "lock-session")

    def toggle_dnd(self):
        self.dnd_settings.set_boolean("show-banners", not self.dnd_settings.get_boolean("show-banners"))

    def sync_dnd(self):
        on = not self.dnd_settings.get_boolean("show-banners")
        ctx = self.btn["dnd"].get_style_context()
        (ctx.add_class if on else ctx.remove_class)("on")
        self.btn["dnd"].set_tooltip_text("Notificações silenciadas" if on else "Silenciar notificações")

    def toggle_collapse_all(self):
        fences = self.app.fences.values()
        self.app.set_collapsed_all(not (fences and all(f.collapsed for f in fences)))
        self.update_stats()

    # ---- timer de foco ----
    def on_timer_press(self, _w, ev):
        if ev.button != 3:
            return False
        menu = Gtk.Menu()
        for m in (5, 15, 25, 45, 60):
            mi = Gtk.CheckMenuItem(label=f"{m} minutos")
            mi.set_draw_as_radio(True)
            mi.set_active(m == self.app.cfg["timer_min"])
            mi.connect("activate", lambda _m, m=m: self.start_timer(m))
            menu.append(mi)
        menu.show_all()
        menu.attach_to_widget(self, None)
        menu.popup_at_pointer(ev)
        self._timer_menu = menu
        return True

    def toggle_timer(self):
        if self.timer_end:
            self.stop_timer()
        else:
            self.start_timer(self.app.cfg["timer_min"])

    def start_timer(self, minutes):
        self.app.cfg["timer_min"] = minutes
        self.app.schedule_save()
        self.timer_end = GLib.get_monotonic_time() + minutes * 60 * 1_000_000
        self.btn["timer"].get_style_context().add_class("on")
        if not getattr(self, "_timer_id", 0):
            self._timer_id = GLib.timeout_add(500, self.timer_tick)
        self.timer_tick()

    def stop_timer(self, done=False):
        self.timer_end = None
        self.btn["timer"].get_style_context().remove_class("on")
        self.btn["timer"].lbl.set_text("Foco")
        if getattr(self, "_timer_id", 0):
            GLib.source_remove(self._timer_id)
            self._timer_id = 0
        if done:
            notify("Tempo de foco concluído", f"{self.app.cfg['timer_min']} minutos — hora de uma pausa.",
                   "alarm-clock-elapsed")

    def timer_tick(self):
        if not self.timer_end:
            return False
        left = (self.timer_end - GLib.get_monotonic_time()) // 1_000_000
        if left <= 0:
            self._timer_id = 0
            self.stop_timer(done=True)
            return False
        self.btn["timer"].lbl.set_text(f"{left // 60:02d}:{left % 60:02d}")
        return True



def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux) ordo-desktop",
                                               "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = r.read()
    return gzip.decompress(data) if data[:2] == b"\x1f\x8b" else data


def http_json(url):
    return json.loads(http_get(url))


def run_async(work, done):
    """Roda work() numa thread e entrega o resultado (ou a exceção) a done() na thread do GTK."""
    def target():
        try:
            res, err = work(), None
        except Exception as e:  # rede fora, timeout, formato inesperado
            res, err = None, e
        GLib.idle_add(lambda: done(res, err) and False)
    threading.Thread(target=target, daemon=True).start()


def fmt_num(v, dec=2):
    """Número no formato brasileiro: 169.186,42"""
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def ago(dt):
    mins = int((datetime.now(timezone.utc) - dt).total_seconds() // 60)
    if mins < 1:
        return "agora"
    if mins < 60:
        return f"há {mins} min"
    if mins < 24 * 60:
        return f"há {mins // 60} h"
    return dt.astimezone().strftime("%d/%m %H:%M")


class WeatherWidget(Gtk.EventBox):
    """Tempo atual + próximos dias via Open-Meteo (gratuito, sem chave)."""

    REFRESH_S = 20 * 60

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.set_tooltip_text("Clique para atualizar · botão direito para trocar a cidade")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        top = Gtk.Box(spacing=12)
        self.icon = Gtk.Image.new_from_icon_name("weather-few-clouds-symbolic", Gtk.IconSize.DIALOG)
        self.icon.set_pixel_size(52)
        self.icon.get_style_context().add_class("wx-icon")
        self.temp = Gtk.Label(label="--°")
        self.temp.get_style_context().add_class("wx-temp")
        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, spacing=1)
        self.desc = Gtk.Label(label="Carregando clima…", xalign=0)
        self.desc.get_style_context().add_class("wx-desc")
        self.line1 = Gtk.Label(xalign=0)
        self.line2 = Gtk.Label(xalign=0)
        for lbl in (self.line1, self.line2):
            lbl.get_style_context().add_class("wx-info")
            lbl.set_ellipsize(Pango.EllipsizeMode.END)
        info.pack_start(self.desc, False, False, 0)
        info.pack_start(self.line1, False, False, 0)
        info.pack_start(self.line2, False, False, 0)
        self.line3 = Gtk.Label(xalign=0)
        self.line3.get_style_context().add_class("wx-info")
        info.pack_start(self.line3, False, False, 0)
        top.pack_start(self.icon, False, False, 0)
        top.pack_start(self.temp, False, False, 0)
        top.pack_start(info, True, True, 0)
        box.pack_start(top, False, False, 0)
        self.days = Gtk.Box(homogeneous=True)
        box.pack_start(self.days, False, False, 0)
        self.add(box)
        self.connect("button-press-event", self.on_press)
        self.fetching = False
        self.refresh()
        GLib.timeout_add_seconds(self.REFRESH_S, lambda: self.refresh() or True)

    def on_press(self, _w, ev):
        if ev.button == 1:
            self.refresh()
        elif ev.button == 3:
            CityDialog(self.app, self.refresh).present()
        return True

    def refresh(self):
        if self.fetching:
            return
        city = self.app.cfg["weather_city"]
        if not city:
            self.desc.set_text("Defina sua cidade")
            self.line1.set_text("Botão direito aqui para escolher")
            return
        self.fetching = True
        url = ("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
            "latitude": city["lat"], "longitude": city["lon"], "timezone": "auto", "forecast_days": 5,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,is_day,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        }))

        def work():
            try:
                data, err = http_json(url), None
            except Exception as e:  # rede fora, timeout, JSON inválido
                data, err = None, e
            GLib.idle_add(self.show, data, err)

        threading.Thread(target=work, daemon=True).start()

    def show(self, data, err):
        self.fetching = False
        city = self.app.cfg["weather_city"]
        if err or not data:
            self.desc.set_text("Clima indisponível")
            self.line1.set_text("Sem conexão — tento de novo em 20 min")
            return False
        cur, daily = data["current"], data["daily"]
        desc, day_icon, night_icon = WEATHER_CODES.get(cur["weather_code"], ("—", "weather-overcast-symbolic", None))
        self.icon.set_from_icon_name(day_icon if cur["is_day"] else (night_icon or day_icon), Gtk.IconSize.DIALOG)
        self.icon.set_pixel_size(52)
        self.temp.set_text(f"{round(cur['temperature_2m'])}°")
        self.desc.set_text(desc)
        rain = daily["precipitation_probability_max"][0]
        self.line1.set_text(f"{city['name']} · sensação {round(cur['apparent_temperature'])}°")
        self.line2.set_text(f"Máx {round(daily['temperature_2m_max'][0])}° · mín {round(daily['temperature_2m_min'][0])}°"
                            + (f" · chuva {rain}%" if rain is not None else ""))
        self.line3.set_text(f"Umidade {cur['relative_humidity_2m']}% · vento {round(cur['wind_speed_10m'])} km/h")
        self.set_tooltip_text(f"Atualizado às {time.strftime('%H:%M')} · clique para atualizar"
                              " · botão direito para trocar a cidade")
        for child in self.days.get_children():
            child.destroy()
        for i in range(1, min(5, len(daily["time"]))):
            d = GLib.DateTime.new_local(*map(int, daily["time"][i].split("-")), 12, 0, 0)
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            name = Gtk.Label(label=d.format("%a").rstrip(".").capitalize())
            name.get_style_context().add_class("wx-day")
            ic = Gtk.Image.new_from_icon_name(
                WEATHER_CODES.get(daily["weather_code"][i], (None, "weather-overcast-symbolic"))[1],
                Gtk.IconSize.LARGE_TOOLBAR)
            ic.get_style_context().add_class("wx-icon")
            temps = Gtk.Box(spacing=3, halign=Gtk.Align.CENTER)
            mx = Gtk.Label(label=f"{round(daily['temperature_2m_max'][i])}°")
            mx.get_style_context().add_class("wx-day-temp")
            mn = Gtk.Label(label=f"{round(daily['temperature_2m_min'][i])}°")
            mn.get_style_context().add_class("wx-day-min")
            temps.pack_start(mx, False, False, 0)
            temps.pack_start(mn, False, False, 0)
            for w in (name, ic, temps):
                col.pack_start(w, False, False, 0)
            col.set_tooltip_text(WEATHER_CODES.get(daily["weather_code"][i], ("",))[0])
            self.days.pack_start(col, True, True, 0)
        self.days.show_all()
        return False


class CityDialog(Gtk.Dialog):
    """Busca a cidade no geocoding do Open-Meteo."""

    def __init__(self, app, on_done):
        super().__init__(title="Cidade do clima", modal=True)
        self.app, self.on_done = app, on_done
        self.set_default_size(380, 320)
        self.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        area = self.get_content_area()
        area.set_border_width(12)
        area.set_spacing(8)
        self.entry = Gtk.SearchEntry(placeholder_text="Digite a cidade e tecle Enter")
        self.entry.connect("activate", self.search)
        self.list = Gtk.ListBox()
        self.list.connect("row-activated", self.pick)
        sc = Gtk.ScrolledWindow(vexpand=True)
        sc.add(self.list)
        area.pack_start(self.entry, False, False, 0)
        area.pack_start(sc, True, True, 0)
        self.connect("response", lambda d, r: d.destroy())
        self.show_all()

    def search(self, _e):
        q = self.entry.get_text().strip()
        if not q:
            return
        url = "https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode(
            {"name": q, "count": 10, "language": "pt"})

        def work():
            try:
                res = http_json(url).get("results", [])
            except Exception:
                res = None
            GLib.idle_add(self.fill, res)

        threading.Thread(target=work, daemon=True).start()

    def fill(self, results):
        for row in self.list.get_children():
            row.destroy()
        if not results:
            self.list.add(Gtk.Label(label="Nada encontrado." if results is not None else "Sem conexão.", margin=8))
        for r in results or []:
            row = Gtk.ListBoxRow()
            row.city = {"name": r["name"], "admin1": r.get("admin1", ""), "lat": r["latitude"], "lon": r["longitude"]}
            row.add(Gtk.Label(label=", ".join(x for x in (r["name"], r.get("admin1"), r.get("country")) if x),
                              xalign=0, margin=8))
            self.list.add(row)
        self.list.show_all()
        return False

    def pick(self, _l, row):
        if getattr(row, "city", None):
            self.app.cfg["weather_city"] = row.city
            self.app.schedule_save()
            self.on_done()
            self.destroy()


class StickyNote(Gtk.Window):
    """Nota adesiva colorida, fixa na área de trabalho."""

    def __init__(self, app, data):
        super().__init__(title=f"{APP_NAME} — Nota")
        self.app, self.data = app, data
        setup_transparent(self)
        self.frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.frame.get_style_context().add_class("sticky")
        self.frame.get_style_context().add_class(f"note-{data['id']}")
        self.add(self.frame)
        self.css = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(self.get_screen(), self.css,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2)

        head_ev = Gtk.EventBox()
        head = Gtk.Box(spacing=2)
        head.get_style_context().add_class("sticky-head")
        self.date_lbl = Gtk.Label(label=data.get("created", ""), xalign=0)
        self.date_lbl.get_style_context().add_class("sticky-date")
        head.pack_start(self.date_lbl, True, True, 0)
        for icon, tip, cb in (("list-add-symbolic", "Nova nota", lambda: self.app.new_note(near=self)),
                              ("applications-graphics-symbolic", "Cor", self.color_menu),
                              ("window-close-symbolic", "Apagar nota", self.delete)):
            b = Gtk.Button(relief=Gtk.ReliefStyle.NONE, tooltip_text=tip)
            b.add(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU))
            b.get_style_context().add_class("sticky-btn")
            b.connect("clicked", lambda _b, cb=cb: cb())
            head.pack_start(b, False, False, 0)
        head_ev.add(head)
        head_ev.connect("button-press-event", self.on_head_press)
        self.mover = WindowDragger(head_ev, self, "move", "grab")
        self.frame.pack_start(head_ev, False, False, 0)

        self.title = Gtk.Entry(text=data.get("title", ""), placeholder_text="Título", has_frame=False)
        self.title.get_style_context().add_class("sticky-title")
        self.title.connect("changed", lambda e: self.store("title", e.get_text()))
        self.frame.pack_start(self.title, False, False, 0)

        self.text = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.text.get_style_context().add_class("sticky-text")
        buf = self.text.get_buffer()
        buf.set_text(data.get("text", ""))
        buf.connect("changed", lambda b: self.store("text", b.get_text(b.get_start_iter(), b.get_end_iter(), False)))
        sc = Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sc.add(self.text)
        self.frame.pack_start(sc, True, True, 0)

        grip_ev = Gtk.EventBox()
        grip = Gtk.Label(label="◢", xalign=1)
        grip.get_style_context().add_class("grip")
        grip_ev.add(grip)
        grip_ev.connect("button-press-event", lambda _w, ev: ev.button == 1 and self.resizer.begin(ev) or True)
        self.resizer = WindowDragger(grip_ev, self, "resize", "se-resize")
        self.frame.pack_end(grip_ev, False, False, 0)

        self.apply_color()
        self.set_size_request(180, 140)
        self.move(data["x"], data["y"])
        self.resize(data.get("w", 260), data.get("h", 220))
        self.connect("configure-event", self.on_configure)
        self.frame.show_all()

    def store(self, key, value):
        self.data[key] = value
        self.app.schedule_save()

    def apply_color(self):
        bg, head = NOTE_COLORS.get(self.data.get("color"), NOTE_COLORS["amarelo"])
        nid = self.data["id"]
        self.css.load_from_data(f".note-{nid} {{ background-color: {bg}; }} "
                                f".note-{nid} .sticky-head {{ background-color: {head}; }}".encode())

    def color_menu(self):
        menu = Gtk.Menu()
        for key, name in NOTE_COLOR_NAMES.items():
            mi = Gtk.MenuItem(label=name)
            mi.connect("activate", lambda _m, k=key: (self.store("color", k), self.apply_color()))
            menu.append(mi)
        menu.show_all()
        menu.attach_to_widget(self, None)
        menu.popup_at_pointer(None)
        self._menu = menu

    def on_head_press(self, _w, ev):
        if ev.button == 1 and ev.type == Gdk.EventType.BUTTON_PRESS:
            self.mover.begin(ev)
        elif ev.button == 3:
            self.app.popup_main_menu(ev)
        return True

    def on_configure(self, _w, ev):
        self.data.update(x=ev.x, y=ev.y, w=ev.width, h=ev.height)
        self.app.schedule_save()
        return False

    def delete(self):
        if self.data.get("text", "").strip() or self.data.get("title", "").strip():
            dlg = Gtk.MessageDialog(message_type=Gtk.MessageType.QUESTION, buttons=Gtk.ButtonsType.YES_NO,
                                    text="Apagar esta nota?")
            dlg.format_secondary_text("O conteúdo da nota será perdido.")
            ok = dlg.run() == Gtk.ResponseType.YES
            dlg.destroy()
            if not ok:
                return
        self.app.remove_note(self)


class InfoCard(Gtk.Window):
    """Card solto na área de trabalho (mercado, notícias): arrastável, posição salva."""

    WIDTH = 380

    def __init__(self, app, key, title):
        super().__init__(title=f"{APP_NAME} — {title}")
        self.app, self.key = app, key
        setup_transparent(self)
        ev = Gtk.EventBox()
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.box.get_style_context().add_class("clock-card")
        self.box.set_size_request(self.WIDTH, -1)
        head = Gtk.Box(spacing=8)
        t = Gtk.Label(label=title.upper(), xalign=0)
        t.get_style_context().add_class("card-title")
        self.meta = Gtk.Label(xalign=1)
        self.meta.get_style_context().add_class("card-meta")
        head.pack_start(t, True, True, 0)
        head.pack_end(self.meta, False, False, 0)
        self.box.pack_start(head, False, False, 0)
        ev.add(self.box)
        ev.connect("button-press-event", self.on_press)
        self.mover = WindowDragger(ev, self, "move", "grab")
        self.add(ev)
        ev.show_all()
        g = self.app.cfg["cards"].get(key)
        if g:
            self.move(g["x"], g["y"])
        self.connect("configure-event", self.on_configure)
        self.loading = False

    def on_press(self, _w, ev):
        if ev.button == 1 and ev.type == Gdk.EventType.BUTTON_PRESS:
            self.mover.begin(ev)
        elif ev.button == 3:
            menu = self.card_menu()
            menu.append(Gtk.SeparatorMenuItem())
            for mi in self.app.build_menu().get_children():  # menu geral logo abaixo
                mi.get_parent().remove(mi)
                menu.append(mi)
            menu.show_all()
            menu.attach_to_widget(self, None)
            menu.popup_at_pointer(ev)
            self._menu = menu
        return True

    def card_menu(self):
        menu = Gtk.Menu()
        mi = Gtk.MenuItem(label="Atualizar agora")
        mi.connect("activate", lambda _m: self.refresh())
        menu.append(mi)
        return menu

    def on_configure(self, _w, ev):
        self.app.cfg["cards"][self.key] = {"x": ev.x, "y": ev.y}
        self.app.schedule_save()
        return False

    def refresh(self):
        raise NotImplementedError


class Sparkline(Gtk.DrawingArea):
    def __init__(self, points, up):
        super().__init__()
        self.points, self.up = [p for p in points if p is not None], up
        self.set_size_request(64, 20)
        self.set_valign(Gtk.Align.CENTER)
        self.connect("draw", self.on_draw)

    def on_draw(self, _w, cr):
        pts = self.points
        if len(pts) < 2:
            return
        w, h = self.get_allocated_width(), self.get_allocated_height()
        lo, hi = min(pts), max(pts)
        span = (hi - lo) or 1
        cr.set_line_width(1.6)
        cr.set_source_rgba(*((0.37, 0.88, 0.63, 1) if self.up else (1, 0.54, 0.54, 1)))
        for i, v in enumerate(pts):
            x = i * (w - 2) / (len(pts) - 1) + 1
            y = h - 2 - (v - lo) / span * (h - 4)
            (cr.move_to if i == 0 else cr.line_to)(x, y)
        cr.stroke()


class MarketCard(InfoCard):
    """Índices, moedas e ações (Yahoo Finance) + Selic/CDI/IPCA (Banco Central)."""

    REFRESH_S = 5 * 60

    def __init__(self, app):
        super().__init__(app, "market", "Mercado")
        self.grid = Gtk.Grid(column_spacing=10, row_spacing=7)
        self.grid.set_margin_top(6)
        self.box.pack_start(self.grid, False, False, 0)
        sep = Gtk.Box()
        sep.get_style_context().add_class("gadget-sep")
        self.box.pack_start(sep, False, False, 0)
        self.ind = Gtk.Box(homogeneous=True)
        self.box.pack_start(self.ind, False, False, 0)
        src = Gtk.Label(label="Fontes: Yahoo Finance · Banco Central · atraso de até 15 min", xalign=0)
        src.get_style_context().add_class("card-meta")
        src.set_margin_top(6)
        self.box.pack_start(src, False, False, 0)
        self.box.show_all()
        self.meta.set_text("carregando…")
        self.refresh()
        GLib.timeout_add_seconds(self.REFRESH_S, lambda: self.refresh() or True)

    def card_menu(self):
        menu = super().card_menu()
        mi = Gtk.MenuItem(label="Editar ativos…")
        mi.connect("activate", lambda _m: self.edit_assets())
        menu.append(mi)
        return menu

    def refresh(self):
        if self.loading:
            return
        self.loading = True
        assets = [list(a) for a in self.app.cfg["market_assets"]]

        def work():
            quotes = []
            for sym, name, kind in assets:
                try:
                    quotes.append((name, sym, kind, *self.fetch_quote(sym)))
                except Exception:
                    quotes.append((name, sym, kind, None, None, []))
            inds = []
            for code, name in BCB_SERIES:
                try:
                    v = http_json(f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados/ultimos/1?formato=json")
                    inds.append((name, float(v[0]["valor"])))
                except Exception:
                    inds.append((name, None))
            return quotes, inds

        run_async(work, self.show_data)

    @staticmethod
    def fetch_quote(sym):
        """(preço, fechamento anterior, pontos do gráfico do dia)."""
        if sym.endswith("-BRL"):
            # O Yahoo não cota cripto em reais; a AwesomeAPI (pública, brasileira) cota.
            hist = http_json(f"https://economia.awesomeapi.com.br/json/daily/{urllib.parse.quote(sym)}/24")
            last = float(hist[0]["bid"])
            prev = last / (1 + float(hist[0]["pctChange"]) / 100)
            return last, prev, [float(h["bid"]) for h in reversed(hist)]
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range=1d&interval=15m"
        r = http_json(url)["chart"]["result"][0]
        m = r["meta"]
        return m.get("regularMarketPrice"), m.get("chartPreviousClose"), r["indicators"]["quote"][0].get("close") or []

    def show_data(self, res, err):
        self.loading = False
        if err or not res:
            self.meta.set_text("sem conexão")
            return
        quotes, inds = res
        for c in self.grid.get_children():
            c.destroy()
        for row, (name, sym, kind, price, prev, closes) in enumerate(quotes):
            names = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            n = Gtk.Label(label=name, xalign=0)
            n.get_style_context().add_class("mk-name")
            sub = Gtk.Label(label=sym.replace(".SA", "").replace("=X", ""), xalign=0)
            sub.get_style_context().add_class("mk-sub")
            names.pack_start(n, False, False, 0)
            names.pack_start(sub, False, False, 0)
            names.set_hexpand(True)
            self.grid.attach(names, 0, row, 1, 1)
            if price is None:
                na = Gtk.Label(label="indisponível", xalign=1)
                na.get_style_context().add_class("mk-sub")
                self.grid.attach(na, 1, row, 3, 1)
                continue
            chg = (price / prev - 1) * 100 if prev else 0.0
            up = chg >= 0
            self.grid.attach(Sparkline(closes, up), 1, row, 1, 1)
            val = Gtk.Label(label=(fmt_num(price, 0) if kind == "pts" else f"R$ {fmt_num(price)}"
                                   if kind == "brl" else fmt_num(price)), xalign=1)
            val.get_style_context().add_class("mk-val")
            self.grid.attach(val, 2, row, 1, 1)
            pill = Gtk.Label(label=f"{'+' if chg > 0 else ''}{fmt_num(chg)}%", xalign=0.5, width_chars=7)
            pill.get_style_context().add_class("mk-chg")
            pill.get_style_context().add_class("mk-up" if chg > 0.004 else "mk-down" if chg < -0.004 else "mk-flat")
            pill.set_valign(Gtk.Align.CENTER)
            self.grid.attach(pill, 3, row, 1, 1)
        for c in self.ind.get_children():
            c.destroy()
        for name, v in inds:
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            a = Gtk.Label(label=name)
            a.get_style_context().add_class("mk-ind")
            b = Gtk.Label(label=f"{fmt_num(v)}%" if v is not None else "—")
            b.get_style_context().add_class("mk-ind-val")
            col.pack_start(a, False, False, 0)
            col.pack_start(b, False, False, 0)
            self.ind.pack_start(col, True, True, 0)
        self.box.show_all()
        self.meta.set_text(f"atualizado {time.strftime('%H:%M')}")
        self.resize(1, 1)

    def edit_assets(self):
        dlg = Gtk.Dialog(title="Ativos do card de mercado", modal=True)
        dlg.add_buttons("Restaurar padrão", 1, "Cancelar", Gtk.ResponseType.CANCEL, "Salvar", Gtk.ResponseType.OK)
        dlg.set_default_size(460, 420)
        area = dlg.get_content_area()
        area.set_border_width(12)
        area.set_spacing(8)
        help_ = Gtk.Label(xalign=0, wrap=True, label=(
            "Um ativo por linha, no formato  SÍMBOLO = Nome.\n"
            "Ações da B3: PETR4, VALE3, BBAS3… (o .SA é colocado sozinho). "
            "Índices: ^BVSP, ^GSPC. Moedas: BRL=X (dólar), EURBRL=X. Cripto: BTC-BRL, ETH-BRL."))
        area.pack_start(help_, False, False, 0)
        view = Gtk.TextView(monospace=True)
        view.get_buffer().set_text("\n".join(f"{s} = {n}" for s, n, _k in self.app.cfg["market_assets"]))
        sc = Gtk.ScrolledWindow(vexpand=True)
        sc.add(view)
        area.pack_start(sc, True, True, 0)
        dlg.show_all()
        resp = dlg.run()
        if resp == 1:
            self.app.cfg["market_assets"] = [list(a) for a in DEFAULT_ASSETS]
        elif resp == Gtk.ResponseType.OK:
            buf = view.get_buffer()
            assets = []
            for line in buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False).splitlines():
                if not line.strip():
                    continue
                sym, _, name = line.partition("=")
                sym = sym.strip().upper()
                if re.fullmatch(r"[A-Z]{4}\d{1,2}F?", sym):
                    sym += ".SA"
                kind = "pts" if sym.startswith("^") else "brl" if sym.endswith((".SA", "BRL=X", "-BRL")) or sym == "BRL=X" \
                    else "num"
                assets.append([sym, name.strip() or sym.replace(".SA", ""), kind])
            if assets:
                self.app.cfg["market_assets"] = assets
        dlg.destroy()
        if resp in (1, Gtk.ResponseType.OK):
            self.app.schedule_save()
            self.refresh()


class NewsCard(InfoCard):
    """Manchetes dos feeds RSS escolhidos, mais recentes primeiro."""

    REFRESH_S = 15 * 60
    MAX_ITEMS = 7
    PER_SOURCE = 3  # para uma fonte muito ativa não ocupar o card inteiro

    def __init__(self, app):
        super().__init__(app, "news", "Notícias")
        self.list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        self.list.set_margin_top(4)
        self.box.pack_start(self.list, False, False, 0)
        self.box.show_all()
        self.meta.set_text("carregando…")
        self.refresh()
        GLib.timeout_add_seconds(self.REFRESH_S, lambda: self.refresh() or True)

    def card_menu(self):
        menu = super().card_menu()
        menu.append(Gtk.SeparatorMenuItem())
        for key, (name, _url) in NEWS_FEEDS.items():
            mi = Gtk.CheckMenuItem(label=name)
            mi.set_active(key in self.app.cfg["news_sources"])
            mi.connect("toggled", lambda m, k=key: self.toggle_source(k, m.get_active()))
            menu.append(mi)
        return menu

    def toggle_source(self, key, on):
        srcs = [k for k in self.app.cfg["news_sources"] if k != key] + ([key] if on else [])
        self.app.cfg["news_sources"] = [k for k in NEWS_FEEDS if k in srcs]
        self.app.schedule_save()
        self.refresh()

    @staticmethod
    def parse_date(text):
        if not text:
            return None
        try:
            dt = parsedate_to_datetime(text)
            # RFC 822 com fuso "-0000" (ex.: Valor) vem sem fuso, mas o horário é UTC.
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pass
        try:
            dt = datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
        return dt if dt.tzinfo else dt.astimezone()  # ISO sem fuso: horário local

    def refresh(self):
        if self.loading:
            return
        self.loading = True
        sources = list(self.app.cfg["news_sources"])

        def work():
            items = []
            for key in sources:
                name, url = NEWS_FEEDS[key]
                try:
                    root = ET.fromstring(http_get(url))
                except Exception:
                    continue
                feed = []
                for it in root.iter("item"):
                    title = (it.findtext("title") or "").strip()
                    link = (it.findtext("link") or "").strip()
                    if title and link.startswith("http"):
                        feed.append((self.parse_date(it.findtext("pubDate")), name, title, link))
                feed.sort(key=lambda x: x[0] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
                items += feed[: self.PER_SOURCE]
            items.sort(key=lambda x: x[0] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
            return items[: self.MAX_ITEMS]

        run_async(work, self.show_items)

    def show_items(self, items, err):
        self.loading = False
        for c in self.list.get_children():
            c.destroy()
        if not self.app.cfg["news_sources"]:
            self.meta.set_text("")
            self.add_info("Nenhuma fonte escolhida — botão direito para escolher.")
        elif err or not items:
            self.meta.set_text("sem conexão")
            self.add_info("Não foi possível carregar as notícias agora.")
        else:
            for dt, src, title, link in items:
                ev = Gtk.EventBox()
                row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                row.get_style_context().add_class("news-row")
                t = Gtk.Label(label=title, xalign=0, wrap=True, max_width_chars=48, lines=2,
                              ellipsize=Pango.EllipsizeMode.END)
                t.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
                t.get_style_context().add_class("news-title")
                meta = Gtk.Box(spacing=6)
                s = Gtk.Label(label=src.upper())
                s.get_style_context().add_class("news-src")
                when = Gtk.Label(label=ago(dt) if dt else "")
                when.get_style_context().add_class("news-meta")
                meta.pack_start(s, False, False, 0)
                meta.pack_start(when, False, False, 0)
                row.pack_start(t, False, False, 0)
                row.pack_start(meta, False, False, 0)
                ev.add(row)
                ev.set_tooltip_text(f"{title}\n\nClique para abrir no navegador")
                ev.connect("button-press-event", self.on_item_press, link)
                ev.connect("realize", lambda w: w.get_window().set_cursor(
                    Gdk.Cursor.new_from_name(w.get_display(), "pointer")))
                self.list.pack_start(ev, False, False, 0)
            self.meta.set_text(f"atualizado {time.strftime('%H:%M')}")
        self.list.show_all()
        self.resize(1, 1)

    def add_info(self, text):
        lbl = Gtk.Label(label=text, xalign=0, wrap=True)
        lbl.get_style_context().add_class("news-meta")
        lbl.set_margin_top(8)
        lbl.set_margin_bottom(8)
        self.list.pack_start(lbl, False, False, 0)

    def on_item_press(self, _w, ev, link):
        if ev.button == 1 and ev.type == Gdk.EventType.BUTTON_PRESS:
            try:
                Gio.AppInfo.launch_default_for_uri(link, None)
            except GLib.Error:
                webbrowser.open(link)
            return True
        return False  # botão direito sobe para o menu do card


class ClockCard(Gtk.Window):
    def __init__(self, app):
        super().__init__(title=f"{APP_NAME} — Relógio")
        self.app = app
        setup_transparent(self)

        ev = Gtk.EventBox()
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        card.get_style_context().add_class("clock-card")
        row = Gtk.Box(spacing=6)
        row.set_halign(Gtk.Align.CENTER)
        self.time_lbl = Gtk.Label()
        self.time_lbl.get_style_context().add_class("clock-time")
        self.sec_lbl = Gtk.Label(valign=Gtk.Align.END)
        self.sec_lbl.set_margin_bottom(12)
        self.sec_lbl.get_style_context().add_class("clock-sec")
        row.pack_start(self.time_lbl, False, False, 0)
        row.pack_start(self.sec_lbl, False, False, 0)
        self.date_lbl = Gtk.Label()
        self.date_lbl.get_style_context().add_class("clock-date")
        self.extra_lbl = Gtk.Label()
        self.extra_lbl.get_style_context().add_class("clock-extra")
        card.pack_start(row, False, False, 0)
        card.pack_start(self.date_lbl, False, False, 0)
        card.pack_start(self.extra_lbl, False, False, 4)
        self.card = card
        self.gadgets = None
        self.set_gadgets(self.app.cfg["show_gadgets"])
        ev.add(card)
        ev.connect("button-press-event", self.on_press)
        self.mover = WindowDragger(ev, self, "move", "grab")
        self.add(ev)
        ev.show_all()

        g = self.app.cfg["clock"]
        if "x" in g:
            self.move(g["x"], g["y"])
        self.connect("configure-event", self.on_configure)
        self.tick()
        GLib.timeout_add(1000 - GLib.DateTime.new_now_local().get_microsecond() // 1000, self.align_tick)

    def set_gadgets(self, show):
        if show and not self.gadgets:
            self.gadgets = GadgetPanel(self.app)
            self.card.pack_start(self.gadgets, False, False, 0)
            self.gadgets.show_all()
        elif not show and self.gadgets:
            self.gadgets.destroy()
            self.gadgets = None
            self.resize(1, 1)

    def align_tick(self):
        self.tick()
        GLib.timeout_add_seconds(1, self.tick)
        return False

    def tick(self):
        now = GLib.DateTime.new_now_local()
        self.time_lbl.set_text(now.format("%H:%M"))
        self.sec_lbl.set_visible(self.app.cfg["show_seconds"])
        self.sec_lbl.set_text(now.format("%S"))
        date = now.format("%A, %d de %B de %Y")
        self.date_lbl.set_text(date[:1].upper() + date[1:])
        hour = now.get_hour()
        greet = "Bom dia" if 5 <= hour < 12 else "Boa tarde" if 12 <= hour < 18 else "Boa noite"
        user = GLib.get_real_name().split(" ")[0] if GLib.get_real_name() not in ("", "Unknown") else ""
        self.extra_lbl.set_text(f"{greet}{', ' + user if user else ''} · semana {now.get_week_of_year()}"
                                f" · {self.app.item_count} itens na área de trabalho")
        return True

    def on_press(self, _w, ev):
        if ev.button == 1 and ev.type == Gdk.EventType.BUTTON_PRESS:
            self.mover.begin(ev)
        elif ev.button == 3:
            self.app.popup_main_menu(ev)
        return True

    def on_configure(self, _w, ev):
        self.app.cfg["clock"].update(x=ev.x, y=ev.y)
        self.app.schedule_save()
        return False


class OrganizerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.cfg = load_config()
        self.fences = {}
        self.clock = None
        self.item_count = 0
        self.notes = []
        self._save_id = 0
        self._refresh_id = 0
        self.visible = True

    # ---- ciclo de vida ----
    def do_startup(self):
        Gtk.Application.do_startup(self)
        css = Gtk.CssProvider()
        css.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.hold()  # janelas tipo DESKTOP não contam como "principal"
        # Logout/kill também devolvem os ícones nativos, não só o menu "Sair".
        for sig in (2, 15, 1):  # SIGINT, SIGTERM, SIGHUP
            GLib.unix_signal_add(GLib.PRIORITY_HIGH, sig, lambda: self.quit_app() or False)
        self.monitor = Gio.File.new_for_path(desktop_dir()).monitor_directory(Gio.FileMonitorFlags.WATCH_MOVES, None)
        self.monitor.connect("changed", lambda *_a: self.schedule_refresh())
        if self.cfg["hide_native"]:
            self.apply_hide_native(True)
        if self.cfg["show_clock"]:
            self.toggle_clock(True)
        self.market = self.news = None
        self.toggle_market(self.cfg["show_market"])
        self.toggle_news(self.cfg["show_news"])
        if self.cfg["note"].strip() and not self.cfg["notes"]:  # migra a antiga "nota rápida"
            self.new_note(text=self.cfg["note"], show=False)
            self.cfg["note"] = ""
        for data in self.cfg["notes"]:
            self.show_note(data)
        first_run = not self.cfg["boxes"]
        self.refresh()
        # Iniciar com o sistema vem ligado por padrão; reescrever o arquivo também
        # o (re)aponta para o executável atual, ex.: após instalar o .deb.
        self.set_autostart(self.cfg["autostart"])
        if first_run:
            self.auto_layout()

    def do_activate(self):
        self.set_all_visible(True)

    def quit_app(self):
        try:
            self.save_now()
        except OSError as e:  # nunca deixar de devolver os ícones nativos por falha ao salvar
            print(f"ordo-desktop: não foi possível salvar a configuração: {e}", file=sys.stderr)
        self.restore_native_icons()  # devolve os ícones nativos ao sair
        self.release()
        self.quit()

    # ---- persistência ----
    def schedule_save(self):
        if self._save_id:
            GLib.source_remove(self._save_id)
        self._save_id = GLib.timeout_add(600, self.save_now)

    def save_now(self):
        self._save_id = 0
        save_config(self.cfg)
        return False

    # ---- conteúdo ----
    def schedule_refresh(self):
        if self._refresh_id:
            GLib.source_remove(self._refresh_id)
        self._refresh_id = GLib.timeout_add(350, self.refresh)

    def refresh(self):
        self._refresh_id = 0
        groups = {}
        items = scan_desktop(self.cfg["show_hidden"])
        self.item_count = len(items)
        overrides = self.cfg["overrides"]
        for it in items:
            if overrides.get(it.name) in CAT_BY_KEY:
                it.category = overrides[it.name]
            groups.setdefault(it.category, []).append(it)
        for key, *_ in CATEGORIES:
            members = sorted(groups.get(key, []), key=lambda i: i.sort_key)
            fence = self.fences.get(key)
            if members:
                if not fence:
                    fence = self.fences[key] = Fence(self, key)
                    self.add_window(fence)
                    if key not in self.cfg["boxes"] or "x" not in self.cfg["boxes"][key]:
                        self.place_new(fence)
                    if self.visible:
                        fence.show()
                fence.set_items(members)
            elif fence:
                fence.destroy()
                del self.fences[key]
        if self.clock:
            self.clock.tick()
        return False

    def auto_layout(self):
        """Distribui as caixas em colunas, da esquerda para a direita, abaixo/ao lado do relógio."""
        wa = workarea()
        margin, gap, col_w = 24, 16, 340
        x, y = wa.x + margin, wa.y + margin
        bottom = wa.y + wa.height - margin
        for key, *_ in CATEGORIES:
            fence = self.fences.get(key)
            if not fence:
                continue
            n = len(fence.flow.get_children())
            per_row = max(1, (col_w - 16) // 80)
            rows = min(max(1, -(-n // per_row)), 4)
            h = HEADER_H + 22 + rows * 92
            if y + h > bottom and y > wa.y + margin:
                x += col_w + gap
                y = wa.y + margin
            g = fence.geom()
            g.update(x=x, y=y, w=col_w, h=h, collapsed=False)
            fence.apply_geometry()
            y += h + gap
        if self.clock:
            self.clock.realize()
            w = max(self.clock.get_allocated_width(), 380)
            self.clock.move(wa.x + wa.width - w - margin, wa.y + margin)
        self.schedule_save()

    def place_new(self, fence):
        wa = workarea()
        g = fence.geom()
        g.update(x=wa.x + wa.width // 2 - 170, y=wa.y + wa.height // 2 - 110, w=340, h=220)
        fence.apply_geometry()

    # ---- notas ----
    def show_note(self, data):
        note = StickyNote(self, data)
        self.add_window(note)
        self.notes.append(note)
        if self.visible:
            note.show()
        return note

    def new_note(self, near=None, text="", show=True):
        wa = workarea()
        if near:
            x, y = near.get_position()
            x, y = x + 28, y + 28
        else:
            x, y = wa.x + wa.width // 2 - 130 + 24 * (len(self.cfg["notes"]) % 6), wa.y + wa.height // 3
        colors = list(NOTE_COLORS)
        data = {"id": int(time.time() * 1000) % 10**10, "title": "", "text": text,
                "color": colors[len(self.cfg["notes"]) % len(colors)],
                "created": GLib.DateTime.new_now_local().format("%d/%m/%Y"),
                "x": x, "y": y, "w": 260, "h": 220}
        self.cfg["notes"].append(data)
        self.schedule_save()
        if not show:
            return
        note = self.show_note(data)
        note.present()
        note.title.grab_focus()

    def remove_note(self, note):
        self.cfg["notes"] = [n for n in self.cfg["notes"] if n is not note.data]
        self.notes.remove(note)
        note.destroy()
        self.schedule_save()

    # ---- ações ----
    def assign_box(self, name, key):
        """Fixa um item numa caixa escolhida (None = volta à categoria automática)."""
        auto = categorize(name, os.path.isdir(os.path.join(desktop_dir(), name)))
        if key is None or key == auto:
            self.cfg["overrides"].pop(name, None)
        else:
            self.cfg["overrides"][name] = key
        self.schedule_save()
        self.schedule_refresh()

    def trash_item(self, item):
        try:
            item.gfile.trash(None)
        except GLib.Error as e:
            show_error(f"Não foi possível mover “{item.display_name}” para a lixeira.", e.message)

    def rename_item(self, item):
        dlg = Gtk.Dialog(title="Renomear", flags=Gtk.DialogFlags.MODAL)
        dlg.add_buttons("Cancelar", Gtk.ResponseType.CANCEL, "Renomear", Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.OK)
        entry = Gtk.Entry(text=item.name, activates_default=True, width_chars=40)
        box = dlg.get_content_area()
        box.set_border_width(12)
        box.add(entry)
        dlg.show_all()
        stem = item.name.rsplit(".", 1)[0] if "." in item.name and not item.is_dir else item.name
        entry.select_region(0, len(stem))
        if dlg.run() == Gtk.ResponseType.OK:
            new = entry.get_text().strip()
            if new and new != item.name:
                try:
                    item.gfile.set_display_name(new, None)
                    if item.name in self.cfg["overrides"]:  # caixa escolhida acompanha o novo nome
                        self.cfg["overrides"][new] = self.cfg["overrides"].pop(item.name)
                        self.schedule_save()
                except GLib.Error as e:
                    show_error("Não foi possível renomear.", e.message)
        dlg.destroy()

    def set_all_visible(self, visible):
        self.visible = visible
        for f in self.fences.values():
            f.set_visible(visible)
        if self.clock:
            self.clock.set_visible(visible)
        for n in self.notes:
            n.set_visible(visible)
        for card in (self.market, self.news):
            if card:
                card.set_visible(visible)

    def toggle_clock(self, show):
        self.cfg["show_clock"] = show
        if show and not self.clock:
            self.clock = ClockCard(self)
            self.add_window(self.clock)
            if "x" not in self.cfg["clock"]:
                self.clock.realize()
                wa = workarea()
                self.clock.move(wa.x + wa.width - 420, wa.y + 24)
            if self.visible:
                self.clock.show()
        elif not show and self.clock:
            self.clock.destroy()
            self.clock = None
        self.schedule_save()

    def _place_card(self, card, x_from_right, below_clock):
        if card.key in self.cfg["cards"]:
            return
        wa = workarea()
        y = wa.y + 24
        if below_clock and self.clock:
            self.clock.realize()
            cx, cy = self.clock.get_position()
            y = cy + self.clock.get_preferred_height()[1] + 16
        card.move(wa.x + wa.width - x_from_right, y)

    def toggle_market(self, show):
        self.cfg["show_market"] = show
        if show and not self.market:
            self.market = MarketCard(self)
            self.add_window(self.market)
            self._place_card(self.market, 840, False)
            if self.visible:
                self.market.show()
        elif not show and self.market:
            self.market.destroy()
            self.market = None
        self.schedule_save()

    def toggle_news(self, show):
        self.cfg["show_news"] = show
        if show and not self.news:
            self.news = NewsCard(self)
            self.add_window(self.news)
            if "news" not in self.cfg["cards"]:
                wa = workarea()
                # Abaixo do card de mercado (que ainda está carregando, então a altura é estimada).
                self.news.move(wa.x + wa.width - 840, wa.y + 24 + (470 if self.market else 0))
            if self.visible:
                self.news.show()
        elif not show and self.news:
            self.news.destroy()
            self.news = None
        self.schedule_save()

    def apply_hide_native(self, hide):
        self.cfg["hide_native"] = hide
        if hide:
            exts = active_native_icon_exts()
            self.cfg["native_disabled"] = sorted(set(self.cfg["native_disabled"]) | set(exts))
            self.save_now()  # grava antes de desligar: se o app travar, a próxima saída religa
            set_extensions(exts, False)
        else:
            self.restore_native_icons()
        self.schedule_save()

    def restore_native_icons(self):
        if self.cfg["native_disabled"]:
            set_extensions(self.cfg["native_disabled"], True)
            self.cfg["native_disabled"] = []
            try:
                self.save_now()
            except OSError:
                pass

    def set_autostart(self, enable):
        self.cfg["autostart"] = enable
        self.schedule_save()
        if os.path.exists(OLD_AUTOSTART_FILE):
            os.remove(OLD_AUTOSTART_FILE)
        if enable:
            os.makedirs(os.path.dirname(AUTOSTART_FILE), exist_ok=True)
            exe = os.path.realpath(sys.argv[0])
            cmd = "ordo-desktop" if exe.startswith("/usr/") else f"python3 '{exe}'"
            with open(AUTOSTART_FILE, "w", encoding="utf-8") as f:
                f.write("[Desktop Entry]\nType=Application\n"
                        f"Name={APP_NAME}\nExec={cmd}\nIcon=ordo-desktop\n"
                        "X-GNOME-Autostart-enabled=true\nX-GNOME-Autostart-Delay=3\n")
        elif os.path.exists(AUTOSTART_FILE):
            os.remove(AUTOSTART_FILE)

    # ---- menus ----
    def build_menu(self):
        menu = Gtk.Menu()

        def item(label, cb):
            mi = Gtk.MenuItem(label=label)
            mi.connect("activate", lambda _m: cb())
            menu.append(mi)
            return mi

        def check(label, active, cb):
            mi = Gtk.CheckMenuItem(label=label)
            mi.set_active(active)
            mi.connect("toggled", lambda m: cb(m.get_active()))
            menu.append(mi)
            return mi

        item("Reorganizar automaticamente", self.auto_layout)
        item("Nova nota", self.new_note)
        item("Recolher todas", lambda: self.set_collapsed_all(True))
        item("Expandir todas", lambda: self.set_collapsed_all(False))
        item("Abrir pasta da Área de Trabalho",
             lambda: Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(desktop_dir()).get_uri(), None))
        menu.append(Gtk.SeparatorMenuItem())
        theme_item = Gtk.MenuItem(label="Estilo das caixas")
        theme_menu = Gtk.Menu()
        group = None
        for key, name in THEMES.items():
            mi = Gtk.RadioMenuItem.new_with_label_from_widget(group, name)
            group = group or mi
            mi.set_active(key == self.cfg["theme"])
            mi.connect("toggled", lambda m, k=key: m.get_active() and self.set_theme(k))
            theme_menu.append(mi)
        theme_item.set_submenu(theme_menu)
        menu.append(theme_item)
        menu.append(Gtk.SeparatorMenuItem())
        check("Mostrar relógio", self.cfg["show_clock"], self.toggle_clock)
        check("Mostrar segundos", self.cfg["show_seconds"], self.set_seconds)
        check("Mostrar gadgets abaixo do relógio", self.cfg["show_gadgets"], self.set_gadgets)
        check("Mostrar mercado financeiro", self.cfg["show_market"], self.toggle_market)
        check("Mostrar notícias", self.cfg["show_news"], self.toggle_news)
        check("Ocultar ícones nativos do Zorin", self.cfg["hide_native"], self.apply_hide_native)
        check("Mostrar arquivos ocultos", self.cfg["show_hidden"], self.set_show_hidden)
        check("Iniciar com o sistema", self.cfg["autostart"], self.set_autostart)
        menu.append(Gtk.SeparatorMenuItem())
        item("Sair", self.quit_app)
        menu.show_all()
        return menu

    def popup_main_menu(self, ev):
        menu = self.build_menu()
        menu.popup_at_pointer(ev)
        self._popup = menu

    def set_theme(self, theme):
        if theme == self.cfg["theme"]:
            return
        self.cfg["theme"] = theme
        for f in self.fences.values():
            f.apply_theme(theme)
        self.schedule_save()

    def set_gadgets(self, on):
        self.cfg["show_gadgets"] = on
        if self.clock:
            self.clock.set_gadgets(on)
        self.schedule_save()

    def set_seconds(self, on):
        self.cfg["show_seconds"] = on
        if self.clock:
            self.clock.tick()
            self.clock.resize(1, 1)
        self.schedule_save()

    def set_show_hidden(self, on):
        self.cfg["show_hidden"] = on
        self.refresh()
        self.schedule_save()

    def set_collapsed_all(self, collapsed):
        for f in self.fences.values():
            f.geom()["collapsed"] = collapsed
            f.apply_geometry()
        self.schedule_save()


def main():
    GLib.set_prgname("ordo-desktop")
    GLib.set_application_name(APP_NAME)
    Gtk.Window.set_default_icon_name("ordo-desktop")
    app = OrganizerApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
