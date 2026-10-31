<p align="center">
  <img src="ordo-desktop.svg" width="96" alt="Ordo Desktop logo">
</p>

<h1 align="center">Ordo Desktop</h1>

<p align="center">
  Desktop organizer for <b>Windows</b> and <b>Linux</b>: auto-sorting boxes by file type,
  clock, weather, sticky notes and quick shortcuts.
</p>

<p align="center">
  <a href="https://github.com/luizsant/OrdoDesktop/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/luizsant/OrdoDesktop"></a>
  <a href="LICENSE.md"><img alt="PolyForm Noncommercial license" src="https://img.shields.io/badge/license-PolyForm%20Noncommercial-blue"></a>
</p>

<p align="center">
  <b>English</b> · <a href="README.pt-BR.md">Português</a>
</p>

![Ordo Desktop in action](docs/screenshot.png)

Inspired by 360 Total Security's "Desktop Organizer" and Stardock Fences, Ordo groups everything
on your Desktop into boxes by category and keeps them up to date in real time.
**It never moves, renames or deletes your files**: it only organizes how they are displayed.

> Available in **English, Portuguese and Spanish** — it follows your system language, or pick one
> in Settings → Idioma/Language/Idioma.

## Features

- **Automatic boxes**: Apps, Folders, PDFs, Documents, Spreadsheets, Presentations, Images,
  Videos, Audio, Archives, Installers and Other. A box only shows up when it has items.
- **Your way**: drag boxes by their title, resize them from the ◢ corner, collapse them with a
  double-click and drag a file into another box (your choice is remembered). Edges are
  **magnetic**: they snap to other boxes and cards with an even 16 px gap.
- **4 box styles**: Default, Light glass, Colored outline and Compact black — the market and news
  cards follow the chosen style.
- **Clock card** with the full date and, below it, the gadgets:
  - current weather and 4-day forecast ([Open-Meteo](https://open-meteo.com), no sign-up);
  - CPU, memory and disk usage;
  - shortcuts: rearrange, screenshot, calculator, terminal, Downloads, trash, lock screen,
    do not disturb, focus timer, collapse boxes, system monitor and new note.
- **Market card**: Ibovespa, S&P 500, Nasdaq, dollar, euro, Bitcoin and stocks (Petrobras, Vale,
  Itaú by default — editable), with the day's change and a mini chart, plus Selic, CDI and
  12-month IPCA from the Brazilian Central Bank.
- **News card**: general headlines from well-known outlets, by country — Brazil (Agência Brasil, G1,
  Folha, BBC News Brasil…), Portugal, United States, United Kingdom, Spain, Argentina and World
  (BBC, DW, France 24, Al Jazeera…). Pick the country and the sources; click a headline to open it
  in the browser.
- **Search** in the clock card: type to find items in your boxes (case- and accent-insensitive);
  boxes filter as you type, Enter opens the first result and Esc clears.
- **Sticky notes** in several colors, saved automatically.
- **Gadgets** (turn each one on in Settings → Gadgets):
  - **Calendar and deadlines**: month view with holidays, a deadline calculator in business days following
    the Brazilian Civil Procedure Code (start on the next business day, Dec 20 – Jan 20 recess, optional
    court/state holidays) with a countdown, and timed reminders with on-screen alerts;
  - **To-do list**, **Favorites** (shortcuts to folders, files and apps), **Clipboard history** (memory only),
    **World clocks**, **Converter** (currencies at today's rate and units), **Now playing** (Spotify,
    browser and other players on Linux) and **Image of the day** (Bing, optionally as your wallpaper);
  - in the clock card: network speed, battery and CPU temperature, when available.
- **No tray icon**: everything is configured by right-clicking any box, the clock or a note.
- Starts with your session and hides the native desktop icons while it is running
  (they come back when Ordo closes).

## Installation

Download from [Releases](https://github.com/luizsant/OrdoDesktop/releases/latest):

### Windows 10 and 11

Run `OrdoDesktop-<version>-setup.exe`. It installs for your user only (no administrator rights
needed) and opens Ordo at the end. To uninstall, use **Settings → Apps → Ordo Desktop**.

> The installer isn't code-signed yet, so Windows SmartScreen may show "Windows protected your PC".
> Click **More info → Run anyway**.

### Linux (Ubuntu, Zorin OS, Pop!_OS, Linux Mint, Debian…)

```bash
sudo apt install ./ordo-desktop_*_amd64.deb
```

Then open **Ordo Desktop** from the applications menu. To uninstall: close Ordo (right-click →
**Quit**) and run `sudo apt remove ordo-desktop`.

On first launch Ordo arranges the boxes by itself and starts with your session from then on.
Settings live in `%APPDATA%\OrdoDesktop\` (Windows) or `~/.config/ordo-desktop/` (Linux).

### From source (Windows or Linux)

```bash
git clone https://github.com/luizsant/OrdoDesktop.git
cd OrdoDesktop
python3 -m pip install PySide6
python3 -m ordo
```

## Requirements

- **Windows 10 or 11** (64-bit).
- **Linux** 64-bit with Python 3.9+ (Ubuntu 20.04+, Debian 11+, Mint 20+, Zorin 16+). Tested on
  Zorin OS 18 (GNOME 46). Works best on X11; on Wayland it runs through XWayland. The `.deb` brings
  its own Qt — nothing else to install.
- Optional on Linux: `xdotool` (Screenshot button).

The "hide native desktop icons" option works with Windows Explorer and, on Linux, with Zorin
Desktop Icons, Desktop Icons NG (DING, Ubuntu's default) and Gtk4 Desktop Icons NG.

## Quick guide

| Action | How |
| --- | --- |
| Find an item in the boxes | Type in the search field of the clock card; Enter opens, Esc clears |
| Open the settings | Right-click a box title or empty area, the clock or a note |
| Move a box or the clock | Drag it by the title (or by the clock card) |
| Resize a box | Drag the ◢ corner |
| Collapse/expand a box | Double-click the title |
| Move a file to another box | Drag it into the other box, or right-click → Mover para a caixa ("Move to box") |
| Choose the weather city | Right-click the weather |
| Focus timer duration | Right-click the Foco ("Focus") button |
| Resize the market or news card | Drag its ◢ corner (right-click → Automatic size to undo) |
| Change the language | Right-click → Language |
| Edit the market assets | Right-click the market card → Editar ativos ("Edit assets") |
| Choose news country and sources | Right-click the news card → País ("Country") and the source list |
| Hide the market or news card | Right-click the card → Ocultar este card ("Hide this card") |
| Show it again | Right-click any box → Mostrar mercado financeiro / Mostrar notícias |

## Data sources

All public, free and without sign-up or API keys:

| Data | Source |
| --- | --- |
| Weather | [Open-Meteo](https://open-meteo.com) |
| Image of the day | Bing's daily image |
| Holidays and deadlines | Calculated on your computer (no internet) |
| Indices, stocks and currencies | Yahoo Finance public chart endpoint (unofficial, may be delayed up to 15 min) |
| Crypto in BRL | [AwesomeAPI](https://docs.awesomeapi.com.br) |
| Selic, CDI, IPCA | [Brazilian Central Bank SGS API](https://dadosabertos.bcb.gov.br) (official) |
| News | Public RSS feeds of each outlet; Ordo shows only headlines and links to the original article |

Market data is informational only and not investment advice.

## Contributing

Contributions are very welcome: fixes, new categories, gadgets, styles, translations and support
for other distros. See [CONTRIBUTING.md](CONTRIBUTING.md) (in Portuguese) to set up the
environment, test and open a pull request. Issues and pull requests in English are welcome too.

## License

[PolyForm Noncommercial 1.0.0](LICENSE.md) © 2026 Luiz Santiago.

In short: you may use, copy, study, modify and redistribute Ordo for free, for **noncommercial**
purposes. **Selling Ordo is not allowed**, nor using it, or modified versions of it, for
commercial purposes. When redistributing, keep the `LICENSE.md` file with its copyright notice.
This summary does not replace the license text.
