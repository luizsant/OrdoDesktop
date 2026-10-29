"""Gera ordo.ico (16 a 256 px) a partir do logo SVG, para o executável e o instalador."""
import io
import os
import sys

from PIL import Image
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

root = os.path.join(os.path.dirname(__file__), "..", "..")
app = QGuiApplication(sys.argv)
svg = QSvgRenderer(os.path.join(root, "ordo-desktop.svg"))
img = QImage(256, 256, QImage.Format_ARGB32)
img.fill(0)
p = QPainter(img)
svg.render(p)
p.end()
buf = QBuffer()
buf.open(QIODevice.WriteOnly)
img.save(buf, "PNG")
Image.open(io.BytesIO(buf.data().data())).save(os.path.join(os.path.dirname(__file__), "ordo.ico"),
                                              sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128),
                                                     (256, 256)])
print("ordo.ico gerado")
