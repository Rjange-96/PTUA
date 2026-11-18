# Génère les fichiers de test de t31 dans /tmp/claude-0/tpl
from docx import Document
from reportlab.pdfgen import canvas
import zipfile,os
D='/tmp/claude-0/tpl';os.makedirs(D,exist_ok=True);os.chdir(D)
d=Document();d.sections[0].header.paragraphs[0].text='Abidjan, le {{date_du_jour}}'
p=d.add_paragraph();r=p.add_run('Objet : mainlevée — marché n° ');r.bold=True;p.add_run('{{numero_');p.add_run('marche}}')
d.add_paragraph('Titulaire : {{titulaire}}');t=d.add_table(rows=1,cols=2);t.cell(0,0).text='Garant';t.cell(0,1).text='{{organisme}} — {{montant_garantie}}'
d.add_paragraph('Type : {{type_garantie}} · échéance {{date_echeance}} · champ inconnu {{inconnu}}');d.add_paragraph('Mot en gras conservé').runs[0].bold=True;d.save('modele.docx')
z=zipfile.ZipFile('faux.docx','w');z.writestr('a.txt','x');z.close()
z=zipfile.ZipFile('bombe.docx','w',zipfile.ZIP_DEFLATED);z.writestr('word/document.xml',b'0'*60_000_000);z.close()
open('ancien.doc','wb').write(b'\xd0\xcf\x11\xe0'+b'0'*100)
c=canvas.Canvas('modele.pdf');c.setFont('Helvetica',12);c.drawString(72,760,'Marche : {{numero_marche}}');c.drawString(72,740,'Titulaire : {{titulaire}}');c.drawString(72,720,'Date : {{date_du_jour}}');c.save()
