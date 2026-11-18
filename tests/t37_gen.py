# v9.16 — génère un scan (JPEG) et un PDF « image seule » (sans texte) d'une attestation d'assurance pour tests/t37.py
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
random.seed(3)
F='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
L=[('NSIA ASSURANCES COTE D IVOIRE',1),('ATTESTATION D ASSURANCE TOUS RISQUES CHANTIER',1),('',0),
 ('Police numero TRC-2026-00451',0),('Assure : SOGEA SATOM COTE D IVOIRE',0),('Marche numero 2026-0001 - Traversee Adjame',0),
 ('Periode de garantie : du 01/03/2026 au 31/12/2028',0),('Capital assure : 1.200.000.000 FCFA',0),('Franchise : 2.000.000 FCFA par sinistre',0),
 ('Garanties : dommages materiels aux travaux, responsabilite civile',0),('dommages causes aux tiers, dommages corporels des travailleurs.',0),
 ('Toute resiliation sera notifiee avec un preavis de trente jours.',0)]
im=Image.new('L',(1500,1000),255);d=ImageDraw.Draw(im);y=50
for t,b in L:
  d.text((60,y),t,font=ImageFont.truetype(FB if b else F,38 if b else 34),fill=20);y+=72
im=im.rotate(0.6,fillcolor=255).filter(ImageFilter.GaussianBlur(0.6))
px=im.load()
for _ in range(3000):px[random.randrange(1500),random.randrange(1000)]=random.randrange(120,255)
im=im.convert('RGB');im.save('/tmp/scan_att.jpg',quality=82)
c=canvas.Canvas('/tmp/scan_att.pdf',pagesize=A4);c.drawImage('/tmp/scan_att.jpg',20,300,width=555,height=370);c.save()
print('ok')
