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


def desktop_dirs():
    """Pastas cujo conteúdo aparece na área de trabalho. No Windows, a pública também
    (atalhos instalados "para todos os usuários" ficam em C:\\Users\\Public\\Desktop)."""
    dirs = [desktop_dir()]
    if IS_WINDOWS:
        public = _windows_known_folder("{C4AA340D-F20F-4863-AFEF-F87EF2E6BA25}")
        if public and os.path.isdir(public) and os.path.normcase(public) != os.path.normcase(dirs[0]):
            dirs.append(public)
    return dirs


def is_hidden(path):
    name = os.path.basename(path)
    if name.startswith(".") or name.endswith("~") or name.lower() == "desktop.ini":
        return True
    if IS_WINDOWS:
        import ctypes
        attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
        return attrs != -1 and bool(attrs & (0x2 | 0x4))  # FILE_ATTRIBUTE_HIDDEN | SYSTEM
    return False


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


# ---------------------------------------------------------------------------
# Uso do sistema (gadgets do relógio)
# ---------------------------------------------------------------------------
class Stats:
    """CPU (variação desde a última leitura), memória e disco da pasta pessoal."""

    def __init__(self):
        self.prev = self._cpu_times()

    @staticmethod
    def _cpu_times():
        """(total, ocioso) acumulados desde o boot."""
        if IS_WINDOWS:
            import ctypes
            from ctypes import wintypes
            idle, kernel, user = wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME()
            ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user))
            ft = lambda f: (f.dwHighDateTime << 32) | f.dwLowDateTime  # noqa: E731
            return ft(kernel) + ft(user), ft(idle)  # o tempo de kernel já inclui o ocioso
        with open("/proc/stat") as f:
            vals = list(map(int, f.readline().split()[1:]))
        return sum(vals), vals[3] + vals[4]

    def cpu(self):
        total, idle = self._cpu_times()
        pt, pi = self.prev
        self.prev = (total, idle)
        dt = total - pt
        return 0.0 if dt <= 0 else max(0.0, min(1.0, 1 - (idle - pi) / dt))

    @staticmethod
    def mem():
        """(fração usada, GB usados, GB totais)."""
        if IS_WINDOWS:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

            m = MEMORYSTATUSEX(dwLength=ctypes.sizeof(MEMORYSTATUSEX))
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            total, used = m.ullTotalPhys, m.ullTotalPhys - m.ullAvailPhys
            return used / total, used / 2**30, total / 2**30
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":", 1)
                info[k] = int(v.split()[0])
        total = info["MemTotal"]
        used = total - info.get("MemAvailable", info["MemFree"])
        return used / total, used / 2**20, total / 2**20

    @staticmethod
    def disk():
        """(fração usada, GB livres) do disco da pasta pessoal."""
        import shutil
        u = shutil.disk_usage(os.path.expanduser("~"))
        return u.used / u.total, u.free / 1e9


# ---------------------------------------------------------------------------
# Atalhos dos gadgets
# ---------------------------------------------------------------------------
def spawn(*argv):
    flags = 0x08000000 if IS_WINDOWS else 0  # CREATE_NO_WINDOW: sem janela de console piscando
    kw = {"creationflags": flags} if IS_WINDOWS else {"start_new_session": True}
    subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)


def screenshot():
    if IS_WINDOWS:
        os.startfile("ms-screenclip:")  # Ferramenta de Captura (recorte)
    else:
        spawn("xdotool", "key", "Print")  # abre a interface de captura do GNOME


def calculator():
    spawn("calc.exe") if IS_WINDOWS else spawn("gnome-calculator")


def terminal():
    if IS_WINDOWS:
        import shutil
        spawn("wt.exe") if shutil.which("wt.exe") else spawn("cmd.exe", "/c", "start", "cmd.exe")
    else:
        import shutil
        spawn(next((t for t in ("gnome-terminal", "x-terminal-emulator", "konsole", "xterm") if shutil.which(t)),
                   "gnome-terminal"))


def system_monitor():
    spawn("taskmgr.exe") if IS_WINDOWS else spawn("gnome-system-monitor")


def open_trash():
    if IS_WINDOWS:
        spawn("explorer.exe", "shell:RecycleBinFolder")
    else:
        spawn("gio", "open", "trash:///")


def trash_count():
    if IS_WINDOWS:
        import ctypes

        class SHQUERYRBINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_ulong), ("i64Size", ctypes.c_longlong), ("i64NumItems", ctypes.c_longlong)]

        info = SHQUERYRBINFO(cbSize=ctypes.sizeof(SHQUERYRBINFO))
        if ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info)) == 0:
            return int(info.i64NumItems)
        return 0
    try:
        out = subprocess.run(["gio", "info", "-a", "trash::item-count", "trash:///"], capture_output=True,
                             text=True, timeout=5).stdout
        m = re.search(r"item-count:\s*(\d+)", out)
        return int(m.group(1)) if m else 0
    except (OSError, subprocess.SubprocessError):
        return 0


def lock_screen():
    if IS_WINDOWS:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return
    r = subprocess.run(["gdbus", "call", "--session", "--dest", "org.gnome.ScreenSaver", "--object-path",
                        "/org/gnome/ScreenSaver", "--method", "org.gnome.ScreenSaver.Lock"], capture_output=True)
    if r.returncode != 0:
        spawn("loginctl", "lock-session")


def dnd_state():
    """True/False no GNOME; None quando o sistema não permite ligar pelo app (Windows)."""
    if IS_WINDOWS:
        return None
    try:
        out = subprocess.run(["gsettings", "get", "org.gnome.desktop.notifications", "show-banners"],
                             capture_output=True, text=True, timeout=5).stdout.strip()
        return out == "false"
    except (OSError, subprocess.SubprocessError):
        return None


def toggle_dnd():
    if IS_WINDOWS:
        os.startfile("ms-settings:notifications")  # o Windows não deixa outro app ligar o "Não incomodar"
        return
    on = dnd_state()
    subprocess.run(["gsettings", "set", "org.gnome.desktop.notifications", "show-banners",
                    "true" if on else "false"], timeout=5, check=False)


def play_alarm():
    if IS_WINDOWS:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    else:
        spawn("canberra-gtk-play", "-i", "alarm-clock-elapsed")


# ---------------------------------------------------------------------------
# Windows: manter as janelas do Ordo no nível da área de trabalho
# ---------------------------------------------------------------------------
def pin_to_desktop(hwnd):
    """Faz a janela "pertencer" à área de trabalho (Progman): fica sempre logo acima dela, abaixo dos
    programas, e continua visível quando o usuário usa Win+D / "Mostrar área de trabalho"."""
    import ctypes
    user32 = ctypes.windll.user32
    progman = user32.FindWindowW("Progman", None)
    if not progman:
        return False
    set_long = user32.SetWindowLongPtrW
    set_long.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
    set_long.restype = ctypes.c_void_p
    set_long(hwnd, -8, progman)  # GWLP_HWNDPARENT = dono da janela
    send_to_bottom(hwnd)
    return True


def send_to_bottom(hwnd):
    import ctypes
    SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE = 0x1, 0x2, 0x10
    ctypes.windll.user32.SetWindowPos(ctypes.c_void_p(hwnd), ctypes.c_void_p(1), 0, 0, 0, 0,
                                      SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)  # 1 = HWND_BOTTOM


def keep_at_bottom(message):
    """Trata WM_WINDOWPOSCHANGING para a janela nunca subir acima dos programas ao ser clicada."""
    import ctypes
    from ctypes import wintypes
    msg = wintypes.MSG.from_address(int(message))
    if msg.message != 0x0046:  # WM_WINDOWPOSCHANGING
        return

    class WINDOWPOS(ctypes.Structure):
        _fields_ = [("hwnd", wintypes.HWND), ("hwndInsertAfter", wintypes.HWND), ("x", ctypes.c_int),
                    ("y", ctypes.c_int), ("cx", ctypes.c_int), ("cy", ctypes.c_int), ("flags", wintypes.UINT)]

    pos = WINDOWPOS.from_address(msg.lParam)
    if not pos.flags & 0x4:  # sem SWP_NOZORDER: alguém está mudando a ordem → manda para o fundo
        pos.hwndInsertAfter = 1  # HWND_BOTTOM
