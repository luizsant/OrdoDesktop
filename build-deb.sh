#!/bin/bash
# Gera ordo-desktop_<versão>_all.deb
set -e
VER="${1:-1.10.1}"  # versão: argumento (usado pelo CI com a tag) ou padrão
cd "$(dirname "$0")"
B=build/ordo-desktop_${VER}_all
rm -rf build && mkdir -p $B/DEBIAN $B/usr/bin $B/usr/share/ordo-desktop $B/usr/share/applications
install -m755 ordo_desktop.py $B/usr/share/ordo-desktop/ordo_desktop.py
install -Dm644 LICENSE.md $B/usr/share/doc/ordo-desktop/copyright
# Ícone: SVG + PNGs para os lugares que não usam o escalável
install -Dm644 ordo-desktop.svg $B/usr/share/icons/hicolor/scalable/apps/ordo-desktop.svg
for SZ in 16 24 32 48 64 128 256; do
  mkdir -p $B/usr/share/icons/hicolor/${SZ}x${SZ}/apps
  python3 -c "import gi; gi.require_version('GdkPixbuf','2.0'); from gi.repository import GdkPixbuf as P; P.Pixbuf.new_from_file_at_size('ordo-desktop.svg',$SZ,$SZ).savev('$B/usr/share/icons/hicolor/${SZ}x${SZ}/apps/ordo-desktop.png','png',[],[])"
done
ln -s ../share/ordo-desktop/ordo_desktop.py $B/usr/bin/ordo-desktop
cat > $B/usr/share/applications/ordo-desktop.desktop <<D
[Desktop Entry]
Type=Application
Name=Ordo Desktop
Comment=Organiza automaticamente a área de trabalho em caixas, com relógio, clima, notas e gadgets
Exec=ordo-desktop
Icon=ordo-desktop
Categories=Utility;GTK;
Keywords=desktop;organizar;organizador;fences;relógio;clima;notas;área de trabalho;
D
cat > $B/DEBIAN/control <<C
Package: ordo-desktop
Version: $VER
Architecture: all
Maintainer: Luiz Santiago <luizsant@gmail.com>
Depends: python3, python3-gi, gir1.2-gtk-3.0
Recommends: xdotool, libnotify-bin, gnome-screenshot | gnome-shell
Conflicts: organizador-desktop
Replaces: organizador-desktop
Section: utils
Priority: optional
Description: Ordo Desktop — organizador de área de trabalho para Zorin OS
 Agrupa arquivos, pastas, documentos e atalhos da área de trabalho em caixas
 por categoria, atualizando em tempo real, com card de relógio, clima, notas
 adesivas e gadgets.
C
dpkg-deb --build --root-owner-group $B >/dev/null
mv build/*.deb . && rm -rf build
ls -la *.deb
