#!/bin/bash
# Gera ordo-desktop_<versão>_amd64.deb com a base Qt (PySide6 embutido, usa o python3 do sistema).
# O Ubuntu/Debian não empacotam o PySide6, por isso ele vai dentro do .deb, só com os módulos usados.
set -e
VER="${1:-2.0.1}"            # versão: argumento (usado pelo CI com a tag) ou padrão
PYSIDE="6.9.3"               # manylinux_2_28: roda em Ubuntu 20.04+, Debian 11+, Mint 20+, Zorin 16+
cd "$(dirname "$0")"
B=build/ordo-desktop_${VER}_amd64
LIB=$B/usr/lib/ordo-desktop
rm -rf build && mkdir -p $B/DEBIAN $B/usr/bin $LIB/vendor $B/usr/share/applications build/wheels

# PySide6 + shiboken6 (wheels abi3: servem para qualquer Python 3.9+)
python3 -m pip download -q --no-deps --only-binary=:all: --platform manylinux_2_28_x86_64 --python-version 3.9 \
  -d build/wheels "PySide6-Essentials==$PYSIDE" "shiboken6==$PYSIDE"
python3 -m pip install -q --no-deps --no-compile --target $LIB/vendor build/wheels/*.whl
Q=$LIB/vendor/PySide6
# Só o que o Ordo usa: Core, Gui, Widgets, Network, Svg (+ plugin xcb, imagens e ícones)
KEEP_PY="QtCore|QtGui|QtWidgets|QtNetwork|QtSvg"
find $Q -maxdepth 1 -name 'Qt*.abi3.so' | grep -Ev "/($KEEP_PY)\.abi3\.so$" | xargs rm -f
find $Q -maxdepth 1 -name 'Qt*.pyi' -delete
rm -rf $Q/Qt/qml $Q/Qt/metatypes $Q/Qt/libexec $Q/include $Q/typesystems $Q/glue $Q/scripts $Q/doc \
       $Q/assistant $Q/designer $Q/linguist $Q/lrelease $Q/lupdate $Q/qmlformat $Q/qmllint $Q/qmlls $Q/qsb \
       $Q/balsam $Q/balsamui $Q/svgtoqml $Q/pyside6-* $Q/libpyside6qml* 2>/dev/null || true
KEEP_LIB="Core|Gui|Widgets|Network|Svg|DBus|XcbQpa|OpenGL|WaylandClient"
for f in $Q/Qt/lib/libQt6*.so*; do
  name=$(basename "$f" | sed -E 's/^libQt6([A-Za-z]+)\.so.*/\1/')
  echo "$name" | grep -Eqx "$KEEP_LIB" || rm -f "$f"
done
rm -rf $Q/Qt/plugins/{qmltooling,sqldrivers,designer,egldeviceintegrations,wayland-*,networkinformation,tls/libqopensslbackend.so.disabled} \
       $Q/Qt/plugins/platforms/{libqeglfs.so,libqlinuxfb.so,libqminimalegl.so,libqvnc.so,libqvkkhrdisplay.so,libqoffscreen.so} 2>/dev/null || true
find $Q/Qt/translations -type f ! -name 'qtbase_pt_BR.qm' ! -name 'qtbase_es.qm' ! -name 'qtbase_en.qm' -delete
find $LIB -name '__pycache__' -prune -exec rm -rf {} +

# O app
cp -r ordo $LIB/ordo
find $LIB/ordo -name '__pycache__' -prune -exec rm -rf {} +
install -m644 ordo-desktop.svg $LIB/ordo-desktop.svg
cat > $B/usr/bin/ordo-desktop <<'SH'
#!/bin/sh
# Ordo Desktop: python3 do sistema + PySide6 embutido em /usr/lib/ordo-desktop/vendor
export PYTHONPATH="/usr/lib/ordo-desktop:/usr/lib/ordo-desktop/vendor${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m ordo "$@"
SH
chmod 755 $B/usr/bin/ordo-desktop

install -Dm644 LICENSE.md $B/usr/share/doc/ordo-desktop/copyright
# Ícone: SVG + PNGs para os lugares que não usam o escalável (renderizados com o próprio Qt embutido)
install -Dm644 ordo-desktop.svg $B/usr/share/icons/hicolor/scalable/apps/ordo-desktop.svg
PYTHONPATH=$LIB/vendor QT_QPA_PLATFORM=minimal python3 - "$B" <<'PY'
import os, sys
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
app = QGuiApplication([])
svg = QSvgRenderer("ordo-desktop.svg")
for sz in (16, 24, 32, 48, 64, 128, 256):
    img = QImage(sz, sz, QImage.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    svg.render(p)
    p.end()
    d = os.path.join(sys.argv[1], f"usr/share/icons/hicolor/{sz}x{sz}/apps")
    os.makedirs(d, exist_ok=True)
    img.save(os.path.join(d, "ordo-desktop.png"))
PY
find $LIB -name '__pycache__' -prune -exec rm -rf {} +

cat > $B/usr/share/applications/ordo-desktop.desktop <<D
[Desktop Entry]
Type=Application
Name=Ordo Desktop
Comment=Organiza automaticamente a área de trabalho em caixas, com relógio, clima, notas e gadgets
Comment[en]=Automatically organizes your desktop into boxes, with clock, weather, notes and gadgets
Comment[es]=Organiza automáticamente el escritorio en cajas, con reloj, tiempo, notas y gadgets
Exec=ordo-desktop
Icon=ordo-desktop
Categories=Utility;Qt;
Keywords=desktop;organizar;organizador;organizer;fences;relógio;clock;clima;weather;notas;notes;
StartupWMClass=ordo-desktop
D
SIZE=$(du -sk $B | cut -f1)
cat > $B/DEBIAN/control <<C
Package: ordo-desktop
Version: $VER
Architecture: amd64
Maintainer: Luiz Santiago <luizsant@gmail.com>
Installed-Size: $SIZE
Depends: python3 (>= 3.9), libxcb-cursor0, libxkbcommon-x11-0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1,
 libxcb-randr0, libxcb-render-util0, libxcb-shape0, libxcb-xinerama0, libxcb-xkb1, libegl1, libgl1,
 libfontconfig1, libdbus-1-3
Recommends: xdotool, libnotify-bin, gnome-screenshot | gnome-shell
Conflicts: organizador-desktop
Replaces: organizador-desktop
Section: utils
Priority: optional
Homepage: https://github.com/luizsant/OrdoDesktop
Description: Ordo Desktop — organizador de área de trabalho
 Agrupa arquivos, pastas, documentos e atalhos da área de trabalho em caixas
 por categoria, atualizando em tempo real, com card de relógio, clima, notas
 adesivas, mercado financeiro, notícias e gadgets.
C
# Atualização: fecha a versão aberta com segurança (devolve os ícones nativos) antes de trocar os arquivos.
cat > $B/DEBIAN/prerm <<'SH'
#!/bin/sh
for u in $(ps -eo user=,args= | awk '/[o]rdo-desktop|[-]m ordo$/ {print $1}' | sort -u); do
  su -s /bin/sh "$u" -c "PYTHONPATH=/usr/lib/ordo-desktop:/usr/lib/ordo-desktop/vendor python3 -m ordo --quit" \
    >/dev/null 2>&1 || true
done
exit 0
SH
chmod 755 $B/DEBIAN/prerm
dpkg-deb --build --root-owner-group -Zxz $B >/dev/null
mv build/*.deb . && rm -rf build
ls -la *.deb
