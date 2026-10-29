"""O que muda entre Linux e Windows: pastas, abrir arquivos, início automático e ícones nativos.

A interface só fala com estas funções; cada uma escolhe o caminho do sistema em que está rodando.
"""
import configparser
import json
import os
import re
import subprocess
import sys

IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

# Extensões do GNOME que desenham os ícones nativos (Zorin, Ubuntu, DING GTK4, antiga).
GNOME_ICON_EXTS = ["zorin-desktop-icons@zorinos.com", "ding@rastersoft.com",
                   "gtk4-ding@smedius.gitlab.com", "desktop-icons@csoriano"]


# ---------------------------------------------------------------------------
# Pastas
# ---------------------------------------------------------------------------
def config_dir():
    if IS_WINDOWS:
        return os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "OrdoDesktop")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "ordo-desktop")


def desktop_dir():
    if IS_WINDOWS:
        return _windows_known_folder("{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}") or os.path.expanduser("~/Desktop")
    # Linux: o nome da pasta depende do idioma ("Área de trabalho", "Escritorio"…) e vem do user-dirs.dirs.
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    try:
        with open(os.path.join(base, "user-dirs.dirs"), encoding="utf-8") as f:
            for line in f:
                m = re.match(r'\s*XDG_DESKTOP_DIR="(.*)"', line)
                if m:
                    return os.path.expandvars(m.group(1).replace("$HOME", os.path.expanduser("~")))
    except OSError:
        pass
    return os.path.expanduser("~/Desktop")


def downloads_dir():
    if IS_WINDOWS:
        return _windows_known_folder("{374DE290-123F-4565-9164-39C4925E467B}") or os.path.expanduser("~/Downloads")
    return os.path.expanduser("~/Downloads")


def _windows_known_folder(guid):
    """Caminho real da pasta (inclui a Área de Trabalho redirecionada para o OneDrive)."""
    import ctypes
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [("d1", wintypes.DWORD), ("d2", wintypes.WORD), ("d3", wintypes.WORD), ("d4", ctypes.c_ubyte * 8)]

    g = GUID()
    ctypes.windll.ole32.CLSIDFromString(ctypes.c_wchar_p(guid), ctypes.byref(g))
    path = ctypes.c_wchar_p()
    if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(g), 0, None, ctypes.byref(path)) != 0:
        return None
    try:
        return path.value
    finally:
        ctypes.windll.ole32.CoTaskMemFree(path)


# ---------------------------------------------------------------------------
# Itens da área de trabalho
# ---------------------------------------------------------------------------
def shortcut_info(path):
    """(nome para exibir, nome do ícone do tema ou None) de um atalho; None se não for atalho."""
    low = path.lower()
    if low.endswith((".lnk", ".url")):
        return os.path.splitext(os.path.basename(path))[0], None
    if low.endswith(".desktop"):
        kf = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            kf.read(path, encoding="utf-8")
            entry = kf["Desktop Entry"]
        except (configparser.Error, KeyError, OSError):
            return None
        loc = (os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or "").split(".")[0]  # ex.: pt_BR
        name = entry.get(f"Name[{loc}]") or entry.get(f"Name[{loc[:2]}]")
        if not name and entry.get("Name"):
            name = entry["Name"]
            domain = entry.get("X-GNOME-Gettext-Domain") or entry.get("X-Ubuntu-Gettext-Domain")
            if domain:  # o GNOME traduz esses nomes pelo catálogo do sistema, não pelo arquivo
                import gettext
                name = gettext.translation(domain, fallback=True).gettext(name)
        name = name or os.path.basename(path)
        return name, entry.get("Icon")
    return None


def open_path(path):
    """Abre arquivo, pasta ou atalho com o programa padrão do sistema."""
    if IS_WINDOWS:
        os.startfile(path)  # noqa: S606 — abre .lnk, .url e qualquer documento como o Explorer
        return
    if path.endswith(".desktop"):
        # gio launch executa o atalho como o próprio GNOME faria (inclusive os não "confiáveis").
        subprocess.Popen(["gio", "launch", path], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    subprocess.Popen(["xdg-open", path], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def show_in_files(path):
    if IS_WINDOWS:
        subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
        return
    try:
        subprocess.run(["gdbus", "call", "--session", "--dest", "org.freedesktop.FileManager1",
                        "--object-path", "/org/freedesktop/FileManager1",
                        "--method", "org.freedesktop.FileManager1.ShowItems",
                        f"['file://{path}']", ""], check=True, timeout=5, capture_output=True)
    except (OSError, subprocess.SubprocessError):
        subprocess.Popen(["xdg-open", os.path.dirname(path)], start_new_session=True)


def move_to_trash(path):
    """Envia para a lixeira (reversível). Retorna mensagem de erro ou None."""
    if IS_WINDOWS:
        import ctypes
        from ctypes import wintypes

        class SHFILEOPSTRUCTW(ctypes.Structure):
            _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT), ("pFrom", wintypes.LPCWSTR),
                        ("pTo", wintypes.LPCWSTR), ("fFlags", ctypes.c_uint16), ("fAnyOperationsAborted", wintypes.BOOL),
                        ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", wintypes.LPCWSTR)]

        FO_DELETE, FOF_ALLOWUNDO, FOF_NOCONFIRMATION, FOF_SILENT = 3, 0x40, 0x10, 0x4
        op = SHFILEOPSTRUCTW(wFunc=FO_DELETE, pFrom=path + "\0\0",
                             fFlags=FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT)
        return None if ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op)) == 0 else "SHFileOperation"
    r = subprocess.run(["gio", "trash", path], capture_output=True, text=True)
    return None if r.returncode == 0 else (r.stderr.strip() or "gio trash")


# ---------------------------------------------------------------------------
# Início automático
# ---------------------------------------------------------------------------
def launch_command():
    """Comando que reabre o Ordo como foi aberto agora (instalado ou pelo código-fonte)."""
    if getattr(sys, "frozen", False):  # executável empacotado (Windows)
        return [sys.executable]
    exe = os.path.realpath(sys.argv[0])
    if not IS_WINDOWS and exe.startswith("/usr/"):
        return ["ordo-desktop"]
    return [sys.executable, exe]


def set_autostart(enable):
    if IS_WINDOWS:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                             winreg.KEY_SET_VALUE)
        with key:
            if enable:
                winreg.SetValueEx(key, "OrdoDesktop", 0, winreg.REG_SZ,
                                  subprocess.list2cmdline(launch_command()))
            else:
                try:
                    winreg.DeleteValue(key, "OrdoDesktop")
                except FileNotFoundError:
                    pass
        return
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    path = os.path.join(base, "autostart", "ordo-desktop.desktop")
    if enable:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        cmd = " ".join(f"'{a}'" if " " in a else a for a in launch_command())
        with open(path, "w", encoding="utf-8") as f:
            f.write("[Desktop Entry]\nType=Application\nName=Ordo Desktop\n"
                    f"Exec={cmd}\nIcon=ordo-desktop\nX-GNOME-Autostart-enabled=true\nX-GNOME-Autostart-Delay=3\n")
    elif os.path.exists(path):
        os.remove(path)


# ---------------------------------------------------------------------------
# Ícones nativos da área de trabalho
# ---------------------------------------------------------------------------
def hide_native_icons():
    """Oculta os ícones nativos. Retorna o que foi desligado, para religar depois (mesmo após travar)."""
    if IS_WINDOWS:
        return ["explorer"] if _explorer_icons(False) else []
    active = []
    for uuid in GNOME_ICON_EXTS:
        try:
            out = subprocess.run(["gnome-extensions", "info", uuid], capture_output=True, text=True, timeout=5).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        if re.search(r":\s*(ACTIVE|ENABLED)\b", out):  # o rótulo é traduzido, o valor não
            active.append(uuid)
    for uuid in active:
        subprocess.run(["gnome-extensions", "disable", uuid], timeout=5, check=False)
    return active


def restore_native_icons(disabled):
    for item in disabled:
        if item == "explorer":
            _explorer_icons(True)
        else:
            subprocess.run(["gnome-extensions", "enable", item], timeout=5, check=False)


def _explorer_icons(show):
    """Mostra/oculta a camada de ícones do Explorer (o mesmo que "Exibir ícones da área de trabalho")."""
    import ctypes
    user32 = ctypes.windll.user32
    progman = user32.FindWindowW("Progman", None)
    defview = user32.FindWindowExW(progman, 0, "SHELLDLL_DefView", None)
    if not defview:  # com papel de parede em apresentação, a camada fica dentro de um WorkerW
        worker = 0
        while not defview:
            worker = user32.FindWindowExW(0, worker, "WorkerW", None)
            if not worker:
                return False
            defview = user32.FindWindowExW(worker, 0, "SHELLDLL_DefView", None)
    listview = user32.FindWindowExW(defview, 0, "SysListView32", None)
    if not listview:
        return False
    user32.ShowWindow(listview, 5 if show else 0)  # SW_SHOW / SW_HIDE
    return True


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None
