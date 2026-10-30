"""Idiomas do Ordo. O texto em português é a chave; inglês e espanhol ficam na tabela TR."""
import os
import unicodedata

LANGUAGES = {"auto": "Automático (sistema)", "pt": "Português", "en": "English", "es": "Español"}
LANG = "pt"

TR = {
    "en": {
        # caixas e estilos
        "Aplicativos": "Apps", "Pastas": "Folders", "PDFs": "PDFs", "Documentos": "Documents",
        "Planilhas": "Spreadsheets", "Apresentações": "Presentations", "Imagens": "Images", "Vídeos": "Videos",
        "Áudio": "Audio", "Compactados": "Archives", "Instaladores": "Installers", "Outros": "Other",
        "Padrão (degradê)": "Default (gradient)", "Vidro claro": "Light glass", "Contorno colorido": "Colored outline",
        "Preto compacto": "Compact black",
        "Amarelo": "Yellow", "Lilás": "Lilac", "Azul": "Blue", "Verde": "Green", "Rosa": "Pink", "Cinza": "Gray",
        # itens
        "Abrir": "Open", "Mostrar no Gerenciador de Arquivos": "Show in Files", "Renomear…": "Rename…",
        "Copiar caminho": "Copy path", "Mover para a caixa": "Move to box",
        "Voltar para a caixa automática": "Back to automatic box", "Mover para a lixeira": "Move to trash",
        "Não foi possível abrir “{name}”.": "Couldn't open “{name}”.",
        "Já existe “{name}” na área de trabalho.": "“{name}” already exists on the desktop.",
        "Não foi possível mover “{name}”.": "Couldn't move “{name}”.",
        "Não foi possível mover “{name}” para a lixeira.": "Couldn't move “{name}” to the trash.",
        "Renomear": "Rename", "Cancelar": "Cancel", "Não foi possível renomear.": "Couldn't rename.",
        # gadgets
        "SISTEMA": "SYSTEM", "ATALHOS": "SHORTCUTS", "CPU": "CPU", "Memória": "Memory", "Disco": "Disk",
        "{n} GB livres": "{n} GB free",
        "Reorganizar": "Rearrange", "Captura": "Screenshot", "Calculadora": "Calculator", "Terminal": "Terminal",
        "Downloads": "Downloads", "Lixeira": "Trash", "Lixeira ({n})": "Trash ({n})", "Bloquear": "Lock",
        "Não perturbe": "Do not disturb", "Foco": "Focus", "Recolher": "Collapse", "Expandir": "Expand",
        "Monitor": "Monitor", "Nova nota": "New note",
        "Clique para iniciar/parar · botão direito escolhe a duração":
            "Click to start/stop · right-click to pick the duration",
        "Abre a ferramenta de captura de tela (tecla Print)": "Opens the screenshot tool (Print key)",
        "Reorganiza as caixas automaticamente": "Rearranges the boxes automatically",
        "Notificações silenciadas": "Notifications muted", "Silenciar notificações": "Mute notifications",
        "{n} minutos": "{n} minutes", "Tempo de foco concluído": "Focus time is over",
        "{n} minutos — hora de uma pausa.": "{n} minutes — time for a break.",
        # tempo
        "agora": "now", "há {n} min": "{n} min ago", "há {n} h": "{n} h ago",
        "Clique para atualizar · botão direito para trocar a cidade": "Click to refresh · right-click to change city",
        "Carregando clima…": "Loading weather…", "Defina sua cidade": "Set your city",
        "Botão direito aqui para escolher": "Right-click here to choose", "Clima indisponível": "Weather unavailable",
        "Sem conexão — tento de novo em 20 min": "Offline — retrying in 20 min",
        "{city} · sensação {t}°": "{city} · feels like {t}°", "Máx {hi}° · mín {lo}°": "High {hi}° · low {lo}°",
        " · chuva {p}%": " · rain {p}%", "Umidade {h}% · vento {w} km/h": "Humidity {h}% · wind {w} km/h",
        "Atualizado às {t} · clique para atualizar · botão direito para trocar a cidade":
            "Updated at {t} · click to refresh · right-click to change city",
        "Cidade do clima": "Weather city", "Digite a cidade e tecle Enter": "Type the city and press Enter",
        "Nada encontrado.": "Nothing found.", "Sem conexão.": "Offline.",
        "Céu limpo": "Clear sky", "Predomínio de sol": "Mostly sunny", "Parcialmente nublado": "Partly cloudy",
        "Nublado": "Overcast", "Neblina": "Fog", "Neblina com geada": "Freezing fog", "Garoa fraca": "Light drizzle",
        "Garoa": "Drizzle", "Garoa forte": "Heavy drizzle", "Chuva fraca": "Light rain", "Chuva": "Rain",
        "Chuva forte": "Heavy rain", "Neve fraca": "Light snow", "Neve": "Snow", "Neve forte": "Heavy snow",
        "Pancadas de chuva": "Rain showers", "Pancadas fortes": "Heavy showers", "Trovoadas": "Thunderstorms",
        "Trovoadas com granizo": "Thunderstorms with hail",
        # notas
        "Nota": "Note", "Cor": "Color", "Apagar nota": "Delete note", "Título": "Title",
        "Apagar esta nota?": "Delete this note?", "O conteúdo da nota será perdido.": "The note's content will be lost.",
        # cards
        "Configurações": "Settings", "Ocultar este card": "Hide this card", "Tamanho automático": "Automatic size",
        "Atualizar agora": "Refresh now", "Mercado": "Market", "Notícias": "News", "Relógio": "Clock",
        "Fontes: Yahoo Finance · Banco Central · atraso de até 15 min":
            "Sources: Yahoo Finance · Brazilian Central Bank · up to 15 min delay",
        "Editar ativos…": "Edit assets…", "sem conexão": "offline", "indisponível": "unavailable",
        "carregando…": "loading…", "atualizado {t}": "updated {t}",
        "Ativos do card de mercado": "Market card assets", "Restaurar padrão": "Restore defaults", "Salvar": "Save",
        "Um ativo por linha, no formato  SÍMBOLO = Nome.\nAções da B3: PETR4, VALE3, BBAS3… (o .SA é colocado "
        "sozinho). Índices: ^BVSP, ^GSPC. Moedas: BRL=X (dólar), EURBRL=X. Cripto: BTC-BRL, ETH-BRL.":
            "One asset per line, as  SYMBOL = Name.\nBrazilian stocks: PETR4, VALE3, BBAS3… (.SA is added "
            "automatically). Other stocks: AAPL, MSFT. Indices: ^BVSP, ^GSPC. Currencies: BRL=X (dollar in BRL), "
            "EURUSD=X. Crypto: BTC-USD, BTC-BRL.",
        "Dólar": "Dollar", "Itaú": "Itaú",
        "País": "Country", "Fontes ({c})": "Sources ({c})",
        "Nenhuma fonte escolhida — botão direito para escolher.": "No source selected — right-click to choose.",
        "Não foi possível carregar as notícias agora.": "Couldn't load the news right now.",
        "Clique para abrir no navegador": "Click to open in the browser",
        "NOTÍCIAS · {c}": "NEWS · {c}",
        "Brasil": "Brazil", "Portugal": "Portugal", "Estados Unidos": "United States", "Reino Unido": "United Kingdom",
        "Espanha": "Spain", "Argentina": "Argentina", "Mundo": "World",
        "Estadão (política)": "Estadão (politics)", "Valor (economia)": "Valor (business)",
        "InfoMoney (economia)": "InfoMoney (business)", "Exame (economia)": "Exame (business)",
        "The Guardian (mundo)": "The Guardian (world)", "ONU News (português)": "UN News (Portuguese)",
        # relógio e busca
        "Buscar nas caixas": "Search the boxes", "Nada nas caixas com esse nome.": "Nothing in the boxes by that name.",
        "em {box}": "in {box}", "+ {n} nas caixas destacadas": "+ {n} in the highlighted boxes",
        "Bom dia": "Good morning", "Boa tarde": "Good afternoon", "Boa noite": "Good evening",
        "semana {n}": "week {n}", "{n} itens na área de trabalho": "{n} items on the desktop",
        # menu
        "Reorganizar automaticamente": "Rearrange automatically", "Recolher todas": "Collapse all",
        "Expandir todas": "Expand all", "Abrir pasta da Área de Trabalho": "Open Desktop folder",
        "Estilo das caixas": "Box style", "Idioma": "Language", "Mostrar relógio": "Show clock",
        "Mostrar segundos": "Show seconds", "Mostrar gadgets abaixo do relógio": "Show gadgets below the clock",
        "Mostrar mercado financeiro": "Show market", "Mostrar notícias": "Show news",
        "Ocultar ícones nativos da área de trabalho": "Hide native desktop icons",
        "Mostrar arquivos ocultos": "Show hidden files", "Iniciar com o sistema": "Start with the system",
        "Sair": "Quit", "Automático (sistema)": "Automatic (system)",
    },
    "es": {
        "Aplicativos": "Aplicaciones", "Pastas": "Carpetas", "PDFs": "PDFs", "Documentos": "Documentos",
        "Planilhas": "Hojas de cálculo", "Apresentações": "Presentaciones", "Imagens": "Imágenes", "Vídeos": "Vídeos",
        "Áudio": "Audio", "Compactados": "Comprimidos", "Instaladores": "Instaladores", "Outros": "Otros",
        "Padrão (degradê)": "Predeterminado (degradado)", "Vidro claro": "Cristal claro",
        "Contorno colorido": "Contorno de color", "Preto compacto": "Negro compacto",
        "Amarelo": "Amarillo", "Lilás": "Lila", "Azul": "Azul", "Verde": "Verde", "Rosa": "Rosa", "Cinza": "Gris",
        "Abrir": "Abrir", "Mostrar no Gerenciador de Arquivos": "Mostrar en Archivos", "Renomear…": "Renombrar…",
        "Copiar caminho": "Copiar ruta", "Mover para a caixa": "Mover a la caja",
        "Voltar para a caixa automática": "Volver a la caja automática", "Mover para a lixeira": "Mover a la papelera",
        "Não foi possível abrir “{name}”.": "No se pudo abrir «{name}».",
        "Já existe “{name}” na área de trabalho.": "Ya existe «{name}» en el escritorio.",
        "Não foi possível mover “{name}”.": "No se pudo mover «{name}».",
        "Não foi possível mover “{name}” para a lixeira.": "No se pudo mover «{name}» a la papelera.",
        "Renomear": "Renombrar", "Cancelar": "Cancelar", "Não foi possível renomear.": "No se pudo renombrar.",
        "SISTEMA": "SISTEMA", "ATALHOS": "ACCESOS", "CPU": "CPU", "Memória": "Memoria", "Disco": "Disco",
        "{n} GB livres": "{n} GB libres",
        "Reorganizar": "Reorganizar", "Captura": "Captura", "Calculadora": "Calculadora", "Terminal": "Terminal",
        "Downloads": "Descargas", "Lixeira": "Papelera", "Lixeira ({n})": "Papelera ({n})", "Bloquear": "Bloquear",
        "Não perturbe": "No molestar", "Foco": "Enfoque", "Recolher": "Contraer", "Expandir": "Expandir",
        "Monitor": "Monitor", "Nova nota": "Nueva nota",
        "Clique para iniciar/parar · botão direito escolhe a duração":
            "Clic para iniciar/detener · clic derecho para elegir la duración",
        "Abre a ferramenta de captura de tela (tecla Print)": "Abre la herramienta de captura (tecla Imprimir)",
        "Reorganiza as caixas automaticamente": "Reorganiza las cajas automáticamente",
        "Notificações silenciadas": "Notificaciones silenciadas", "Silenciar notificações": "Silenciar notificaciones",
        "{n} minutos": "{n} minutos", "Tempo de foco concluído": "Tiempo de enfoque terminado",
        "{n} minutos — hora de uma pausa.": "{n} minutos — hora de un descanso.",
        "agora": "ahora", "há {n} min": "hace {n} min", "há {n} h": "hace {n} h",
        "Clique para atualizar · botão direito para trocar a cidade":
            "Clic para actualizar · clic derecho para cambiar la ciudad",
        "Carregando clima…": "Cargando el tiempo…", "Defina sua cidade": "Elige tu ciudad",
        "Botão direito aqui para escolher": "Clic derecho aquí para elegir", "Clima indisponível": "Tiempo no disponible",
        "Sem conexão — tento de novo em 20 min": "Sin conexión — reintento en 20 min",
        "{city} · sensação {t}°": "{city} · sensación {t}°", "Máx {hi}° · mín {lo}°": "Máx {hi}° · mín {lo}°",
        " · chuva {p}%": " · lluvia {p}%", "Umidade {h}% · vento {w} km/h": "Humedad {h}% · viento {w} km/h",
        "Atualizado às {t} · clique para atualizar · botão direito para trocar a cidade":
            "Actualizado a las {t} · clic para actualizar · clic derecho para cambiar la ciudad",
        "Cidade do clima": "Ciudad del tiempo", "Digite a cidade e tecle Enter": "Escribe la ciudad y pulsa Intro",
        "Nada encontrado.": "No se encontró nada.", "Sem conexão.": "Sin conexión.",
        "Céu limpo": "Despejado", "Predomínio de sol": "Mayormente soleado", "Parcialmente nublado": "Parcialmente nublado",
        "Nublado": "Nublado", "Neblina": "Niebla", "Neblina com geada": "Niebla helada", "Garoa fraca": "Llovizna débil",
        "Garoa": "Llovizna", "Garoa forte": "Llovizna intensa", "Chuva fraca": "Lluvia débil", "Chuva": "Lluvia",
        "Chuva forte": "Lluvia intensa", "Neve fraca": "Nevada débil", "Neve": "Nieve", "Neve forte": "Nevada intensa",
        "Pancadas de chuva": "Chubascos", "Pancadas fortes": "Chubascos fuertes", "Trovoadas": "Tormentas",
        "Trovoadas com granizo": "Tormentas con granizo",
        "Nota": "Nota", "Cor": "Color", "Apagar nota": "Borrar nota", "Título": "Título",
        "Apagar esta nota?": "¿Borrar esta nota?", "O conteúdo da nota será perdido.": "Se perderá el contenido de la nota.",
        "Configurações": "Ajustes", "Ocultar este card": "Ocultar esta tarjeta", "Tamanho automático": "Tamaño automático",
        "Atualizar agora": "Actualizar ahora", "Mercado": "Mercado", "Notícias": "Noticias", "Relógio": "Reloj",
        "Fontes: Yahoo Finance · Banco Central · atraso de até 15 min":
            "Fuentes: Yahoo Finance · Banco Central de Brasil · retraso de hasta 15 min",
        "Editar ativos…": "Editar activos…", "sem conexão": "sin conexión", "indisponível": "no disponible",
        "carregando…": "cargando…", "atualizado {t}": "actualizado {t}",
        "Ativos do card de mercado": "Activos de la tarjeta de mercado", "Restaurar padrão": "Restaurar",
        "Salvar": "Guardar",
        "Um ativo por linha, no formato  SÍMBOLO = Nome.\nAções da B3: PETR4, VALE3, BBAS3… (o .SA é colocado "
        "sozinho). Índices: ^BVSP, ^GSPC. Moedas: BRL=X (dólar), EURBRL=X. Cripto: BTC-BRL, ETH-BRL.":
            "Un activo por línea, como  SÍMBOLO = Nombre.\nAcciones de Brasil: PETR4, VALE3… (el .SA se añade solo). "
            "Otras: AAPL, SAN.MC, GGAL.BA. Índices: ^BVSP, ^IBEX, ^MERV. Monedas: EUR=X, ARS=X. "
            "Cripto: BTC-USD, BTC-BRL.",
        "Dólar": "Dólar", "Itaú": "Itaú",
        "País": "País", "Fontes ({c})": "Fuentes ({c})",
        "Nenhuma fonte escolhida — botão direito para escolher.": "Ninguna fuente elegida — clic derecho para elegir.",
        "Não foi possível carregar as notícias agora.": "No se pudieron cargar las noticias ahora.",
        "Clique para abrir no navegador": "Clic para abrir en el navegador",
        "NOTÍCIAS · {c}": "NOTICIAS · {c}",
        "Brasil": "Brasil", "Portugal": "Portugal", "Estados Unidos": "Estados Unidos", "Reino Unido": "Reino Unido",
        "Espanha": "España", "Argentina": "Argentina", "Mundo": "Mundo",
        "Estadão (política)": "Estadão (política)", "Valor (economia)": "Valor (economía)",
        "InfoMoney (economia)": "InfoMoney (economía)", "Exame (economia)": "Exame (economía)",
        "The Guardian (mundo)": "The Guardian (mundo)", "ONU News (português)": "Noticias ONU (portugués)",
        "Buscar nas caixas": "Buscar en las cajas", "Nada nas caixas com esse nome.": "Nada en las cajas con ese nombre.",
        "em {box}": "en {box}", "+ {n} nas caixas destacadas": "+ {n} en las cajas resaltadas",
        "Bom dia": "Buenos días", "Boa tarde": "Buenas tardes", "Boa noite": "Buenas noches",
        "semana {n}": "semana {n}", "{n} itens na área de trabalho": "{n} elementos en el escritorio",
        "Reorganizar automaticamente": "Reorganizar automáticamente", "Recolher todas": "Contraer todas",
        "Expandir todas": "Expandir todas", "Abrir pasta da Área de Trabalho": "Abrir carpeta del Escritorio",
        "Estilo das caixas": "Estilo de las cajas", "Idioma": "Idioma", "Mostrar relógio": "Mostrar reloj",
        "Mostrar segundos": "Mostrar segundos", "Mostrar gadgets abaixo do relógio": "Mostrar gadgets bajo el reloj",
        "Mostrar mercado financeiro": "Mostrar mercado", "Mostrar notícias": "Mostrar noticias",
        "Ocultar ícones nativos da área de trabalho": "Ocultar iconos nativos del escritorio",
        "Mostrar arquivos ocultos": "Mostrar archivos ocultos", "Iniciar com o sistema": "Iniciar con el sistema",
        "Sair": "Salir", "Automático (sistema)": "Automático (sistema)",
    },
}

WEEKDAYS = {"pt": ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"],
            "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "es": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]}
WEEKDAYS_SHORT = {"pt": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"],
                  "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                  "es": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]}
MONTHS = {"pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
                 "outubro", "novembro", "dezembro"],
          "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                 "October", "November", "December"],
          "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
                 "octubre", "noviembre", "diciembre"]}

def _(text, **kw):
    """Traduz um texto da interface (a chave é o português) e preenche os {campos}."""
    out = TR.get(LANG, {}).get(text, text)
    return out.format(**kw) if kw else out


def system_language():
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        code = (os.environ.get(var) or "").split(":")[0][:2].lower()
        if code:
            return code if code in ("pt", "es") else "en"
    try:  # Windows: idioma da interface do usuário
        import ctypes
        import locale
        code = (locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), "") or "")[:2]
        return code if code in ("pt", "es") else "en"
    except (AttributeError, OSError, ImportError):
        return "en"


def set_language(choice):
    global LANG
    LANG = system_language() if choice == "auto" else choice


def long_date(dt):
    """Quinta, 29 de outubro de 2026 / Thursday, October 29, 2026 / Jueves, 29 de octubre de 2026"""
    wd, m = WEEKDAYS[LANG][dt.weekday()], MONTHS[LANG][dt.month - 1]
    if LANG == "en":
        return f"{wd}, {m} {dt.day}, {dt.year}"
    return f"{wd}, {dt.day} de {m} de {dt.year}"


def fmt_num(v, dec=2):
    """Número no formato do idioma: 169.186,42 (pt/es) ou 169,186.42 (en)."""
    s = f"{v:,.{dec}f}"
    return s if LANG == "en" else s.replace(",", "X").replace(".", ",").replace("X", ".")


def fold(text):
    """Minúsculas e sem acentos, para a busca: "Orçamento" combina com "orcamento"."""
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold()) if unicodedata.category(c) != "Mn")
