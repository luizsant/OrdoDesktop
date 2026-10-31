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


# ---------------------------------------------------------------------------
# Textos dos gadgets (versão 2.1)
# ---------------------------------------------------------------------------
TR["en"].update({
    "Gadgets": "Gadgets", "Agenda e prazos": "Calendar and deadlines", "Tarefas": "To-do",
    "Mercado financeiro": "Market", "Favoritos": "Favorites", "Tocando agora": "Now playing",
    "Relógios mundiais": "World clocks", "Conversor": "Converter", "Área de transferência": "Clipboard",
    "Imagem do dia": "Image of the day", "Rede": "Network", "Bateria": "Battery", "Temperatura": "Temperature",
    "Remover": "Remove", "Descrição": "Description", "Quando": "When", "O quê": "What",
    # agenda
    "PRAZOS": "DEADLINES", "LEMBRETES": "REMINDERS", "+ Prazo": "+ Deadline", "+ Lembrete": "+ Reminder",
    "Prazo": "Deadline", "Lembrete": "Reminder", "Vencimento": "Due date", "Prazos vencendo": "Deadlines due",
    "Nenhum prazo. Use “+ Prazo” para calcular um.": "No deadlines. Use “+ Deadline” to calculate one.",
    "Nenhum lembrete.": "No reminders.", "vencido": "overdue", "vence hoje": "due today",
    "falta 1 dia útil": "1 business day left", "faltam {n} dias úteis": "{n} business days left",
    "vence {d}": "due {d}", "avisado": "notified", "Voltar para hoje": "Back to today",
    "Novo lembrete em {d}": "New reminder on {d}", "Prazo a partir de {d}": "Deadline starting {d}",
    "Feriados considerados": "Holidays counted", "Feriados nacionais": "National holidays (Brazil)",
    "Feriados forenses (Carnaval, Semana Santa, Corpus Christi, 8/12)":
        "Court holidays (Carnival, Holy Week, Corpus Christi, Dec 8)",
    "Feriados do Pará": "Pará state holidays", "Feriados de Belém": "Belém city holidays",
    "Suspensão de 20/12 a 20/01 (art. 220 do CPC)": "Court recess Dec 20 – Jan 20 (CPC art. 220)",
    "Suspensão de prazos (20/12 a 20/01)": "Deadlines suspended (Dec 20 – Jan 20)",
    "Feriados extras do meu tribunal…": "My court's extra holidays…",
    "Feriados extras do meu tribunal": "My court's extra holidays",
    "Um por linha: AAAA-MM-DD = Nome (só naquele ano) ou MM-DD = Nome (todo ano).":
        "One per line: YYYY-MM-DD = Name (that year only) or MM-DD = Name (every year).",
    "Audiência, reunião, ligar para…": "Hearing, meeting, call…",
    "Contestação, recurso, processo…": "Answer, appeal, case number…",
    "Intimação / publicação": "Service / publication date", "dias úteis": "business days",
    "dias corridos": "calendar days", "Não contou: {lista}": "Not counted: {lista}",
    "Conta a partir do primeiro dia útil seguinte (art. 224 do CPC). Confira os feriados do seu tribunal no menu "
    "do card (botão direito → Feriados considerados).":
        "Counting starts on the next business day (Brazilian CPC art. 224). Check your court's holidays in the "
        "card menu (right-click → Holidays counted).",
    "Confraternização Universal": "New Year's Day", "Sexta-feira Santa": "Good Friday", "Tiradentes": "Tiradentes",
    "Dia do Trabalho": "Labour Day", "Independência": "Independence Day",
    "Nossa Senhora Aparecida": "Our Lady of Aparecida", "Finados": "All Souls' Day",
    "Proclamação da República": "Republic Day", "Consciência Negra": "Black Consciousness Day", "Natal": "Christmas",
    "Carnaval (segunda)": "Carnival (Monday)", "Carnaval (terça)": "Carnival (Tuesday)",
    "Quinta-feira Santa": "Holy Thursday", "Corpus Christi": "Corpus Christi", "Dia da Justiça": "Justice Day",
    "Adesão do Pará à Independência": "Pará's adhesion to Independence", "Aniversário de Belém": "Belém Anniversary",
    # tarefas, favoritos, área de transferência
    "Nova tarefa — Enter para adicionar": "New task — press Enter to add", "{n} pendentes": "{n} pending",
    "Nada por aqui. Escreva acima e tecle Enter.": "Nothing here. Type above and press Enter.",
    "Limpar concluídas": "Clear completed", "Remover dos favoritos": "Remove from favorites",
    "Adicionar pasta…": "Add folder…", "Adicionar arquivo…": "Add file…", "Adicionar aplicativo…": "Add app…",
    "Adicionar pasta": "Add folder", "Adicionar arquivo": "Add file", "Adicionar aplicativo": "Add app",
    "Arraste para cá pastas, arquivos ou aplicativos (o original continua onde está), ou use o botão direito → "
    "Adicionar.": "Drag folders, files or apps here (the original stays where it is), or right-click → Add.",
    "não fica salvo": "not saved", "copiado!": "copied!", "Limpar histórico": "Clear history",
    "O histórico fica só na memória e some ao fechar o Ordo.": "History is kept in memory only and is cleared when "
                                                               "Ordo closes.",
    "O que você copiar aparece aqui.": "Whatever you copy shows up here.",
    # relógios, conversor, música, imagem
    "mesmo horário": "same time", "amanhã": "tomorrow", "ontem": "yesterday", "Escolher cidades…": "Choose cities…",
    "Um fuso por linha (ex.: America/Belem, Europe/Paris). Escolha abaixo para acrescentar.":
        "One time zone per line (e.g. America/New_York, Europe/Paris). Pick below to add.",
    "MOEDAS": "CURRENCIES", "UNIDADES": "UNITS", "Inverter": "Swap", "Comprimento": "Length", "Massa": "Mass",
    "Área": "Area", "Volume": "Volume", "Dados": "Data",
    "Nada tocando": "Nothing playing", "tocando": "playing", "pausado": "paused",
    "Toque algo no Spotify, no navegador ou em outro player.": "Play something in Spotify, your browser or another "
                                                               "player.",
    "Usar como papel de parede": "Set as wallpaper", "Trocar o papel de parede todo dia": "Change wallpaper daily",
    "Restaurar papel de parede original": "Restore original wallpaper",
})
TR["es"].update({
    "Gadgets": "Gadgets", "Agenda e prazos": "Agenda y plazos", "Tarefas": "Tareas",
    "Mercado financeiro": "Mercado", "Favoritos": "Favoritos", "Tocando agora": "Reproduciendo",
    "Relógios mundiais": "Relojes mundiales", "Conversor": "Conversor", "Área de transferência": "Portapapeles",
    "Imagem do dia": "Imagen del día", "Rede": "Red", "Bateria": "Batería", "Temperatura": "Temperatura",
    "Remover": "Quitar", "Descrição": "Descripción", "Quando": "Cuándo", "O quê": "Qué",
    "PRAZOS": "PLAZOS", "LEMBRETES": "RECORDATORIOS", "+ Prazo": "+ Plazo", "+ Lembrete": "+ Recordatorio",
    "Prazo": "Plazo", "Lembrete": "Recordatorio", "Vencimento": "Vencimiento", "Prazos vencendo": "Plazos que vencen",
    "Nenhum prazo. Use “+ Prazo” para calcular um.": "Ningún plazo. Usa «+ Plazo» para calcular uno.",
    "Nenhum lembrete.": "Ningún recordatorio.", "vencido": "vencido", "vence hoje": "vence hoy",
    "falta 1 dia útil": "falta 1 día hábil", "faltam {n} dias úteis": "faltan {n} días hábiles",
    "vence {d}": "vence {d}", "avisado": "avisado", "Voltar para hoje": "Volver a hoy",
    "Novo lembrete em {d}": "Nuevo recordatorio el {d}", "Prazo a partir de {d}": "Plazo desde el {d}",
    "Feriados considerados": "Feriados considerados", "Feriados nacionais": "Feriados nacionales (Brasil)",
    "Feriados forenses (Carnaval, Semana Santa, Corpus Christi, 8/12)":
        "Feriados judiciales (Carnaval, Semana Santa, Corpus Christi, 8/12)",
    "Feriados do Pará": "Feriados de Pará", "Feriados de Belém": "Feriados de Belém",
    "Suspensão de 20/12 a 20/01 (art. 220 do CPC)": "Suspensión del 20/12 al 20/01 (art. 220 del CPC)",
    "Suspensão de prazos (20/12 a 20/01)": "Plazos suspendidos (20/12 al 20/01)",
    "Feriados extras do meu tribunal…": "Feriados extra de mi tribunal…",
    "Feriados extras do meu tribunal": "Feriados extra de mi tribunal",
    "Um por linha: AAAA-MM-DD = Nome (só naquele ano) ou MM-DD = Nome (todo ano).":
        "Uno por línea: AAAA-MM-DD = Nombre (solo ese año) o MM-DD = Nombre (todos los años).",
    "Audiência, reunião, ligar para…": "Audiencia, reunión, llamar a…",
    "Contestação, recurso, processo…": "Contestación, recurso, expediente…",
    "Intimação / publicação": "Notificación / publicación", "dias úteis": "días hábiles",
    "dias corridos": "días corridos", "Não contou: {lista}": "No contó: {lista}",
    "Conta a partir do primeiro dia útil seguinte (art. 224 do CPC). Confira os feriados do seu tribunal no menu "
    "do card (botão direito → Feriados considerados).":
        "Cuenta desde el primer día hábil siguiente (art. 224 del CPC de Brasil). Revisa los feriados de tu tribunal "
        "en el menú de la tarjeta (clic derecho → Feriados considerados).",
    "Confraternização Universal": "Año Nuevo", "Sexta-feira Santa": "Viernes Santo", "Tiradentes": "Tiradentes",
    "Dia do Trabalho": "Día del Trabajo", "Independência": "Independencia",
    "Nossa Senhora Aparecida": "Nuestra Señora Aparecida", "Finados": "Día de Difuntos",
    "Proclamação da República": "Proclamación de la República", "Consciência Negra": "Día de la Conciencia Negra",
    "Natal": "Navidad", "Carnaval (segunda)": "Carnaval (lunes)", "Carnaval (terça)": "Carnaval (martes)",
    "Quinta-feira Santa": "Jueves Santo", "Corpus Christi": "Corpus Christi", "Dia da Justiça": "Día de la Justicia",
    "Adesão do Pará à Independência": "Adhesión de Pará a la Independencia",
    "Aniversário de Belém": "Aniversario de Belém",
    "Nova tarefa — Enter para adicionar": "Nueva tarea — Intro para añadir", "{n} pendentes": "{n} pendientes",
    "Nada por aqui. Escreva acima e tecle Enter.": "Nada por aquí. Escribe arriba y pulsa Intro.",
    "Limpar concluídas": "Borrar completadas", "Remover dos favoritos": "Quitar de favoritos",
    "Adicionar pasta…": "Añadir carpeta…", "Adicionar arquivo…": "Añadir archivo…",
    "Adicionar aplicativo…": "Añadir aplicación…", "Adicionar pasta": "Añadir carpeta",
    "Adicionar arquivo": "Añadir archivo", "Adicionar aplicativo": "Añadir aplicación",
    "Arraste para cá pastas, arquivos ou aplicativos (o original continua onde está), ou use o botão direito → "
    "Adicionar.": "Arrastra aquí carpetas, archivos o aplicaciones (el original queda donde está), o usa clic "
                  "derecho → Añadir.",
    "não fica salvo": "no se guarda", "copiado!": "¡copiado!", "Limpar histórico": "Borrar historial",
    "O histórico fica só na memória e some ao fechar o Ordo.": "El historial queda solo en la memoria y se borra al "
                                                               "cerrar Ordo.",
    "O que você copiar aparece aqui.": "Lo que copies aparece aquí.",
    "mesmo horário": "misma hora", "amanhã": "mañana", "ontem": "ayer", "Escolher cidades…": "Elegir ciudades…",
    "Um fuso por linha (ex.: America/Belem, Europe/Paris). Escolha abaixo para acrescentar.":
        "Un huso por línea (ej.: Europe/Madrid, America/Buenos_Aires). Elige abajo para añadir.",
    "MOEDAS": "MONEDAS", "UNIDADES": "UNIDADES", "Inverter": "Invertir", "Comprimento": "Longitud", "Massa": "Masa",
    "Área": "Área", "Volume": "Volumen", "Dados": "Datos",
    "Nada tocando": "Nada sonando", "tocando": "sonando", "pausado": "en pausa",
    "Toque algo no Spotify, no navegador ou em outro player.": "Reproduce algo en Spotify, en el navegador o en otro "
                                                               "reproductor.",
    "Usar como papel de parede": "Usar como fondo de pantalla",
    "Trocar o papel de parede todo dia": "Cambiar el fondo de pantalla cada día",
    "Restaurar papel de parede original": "Restaurar el fondo de pantalla original",
})
