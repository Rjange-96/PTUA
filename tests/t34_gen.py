# v9.13 — génère deux attestations d'assurance PDF (texte réel) pour tests/t34.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
def mk(path,lines):
  c=canvas.Canvas(path,pagesize=A4);y=800
  for l in lines:
    if y<60:c.showPage();y=800
    c.setFont('Helvetica',10);c.drawString(40,y,l);y-=16
  c.save()
mk('/tmp/att_ok.pdf',[
 'NSIA ASSURANCES - Societe agreee par la Direction des Assurances (Code CIMA)',
 'ATTESTATION D ASSURANCE TOUS RISQUES CHANTIER',
 'Police n° TRC-2026-00451',
 'Souscripteur / Assure : SOGEA SATOM COTE D IVOIRE',
 'Co-assure et beneficiaire : le Maitre d ouvrage, Autorite contractante',
 'Chantier : Marche n° 2026-0001 - Construction de l ouvrage de la traversee d Adjame, Abidjan, Cote d Ivoire',
 'Periode de garantie : du 01/03/2026 au 31/12/2028',
 'Capital assure : 1.200.000.000 FCFA (un milliard deux cents millions)',
 'Franchise : 2.000.000 FCFA par sinistre',
 'Garanties : dommages materiels a l ouvrage et aux travaux, responsabilite civile dommages causes aux tiers,',
 'dommages corporels des travailleurs y compris personnel temporaire, vice de conception, evenements naturels,',
 'periode de maintenance de 12 mois, sous-traitants couverts, renonciation a recours contre le maitre d ouvrage.',
 'Toute resiliation ou suspension sera notifiee au maitre d ouvrage avec un preavis de trente (30) jours.',
 'Prime payee : quittance n° 889 du 25/02/2026.',
 'Exclusions : guerre, risque nucleaire.'])
mk('/tmp/att_ko.pdf',[
 'ALLIANZ COTE D IVOIRE',
 'ATTESTATION D ASSURANCE TOUS RISQUES CHANTIER',
 'Police n° 77-AB-2026',
 'Assure : BATIMAX SARL',
 'Periode de garantie : du 15/04/2026 au 30/06/2026',
 'Capital assure : 300.000.000 FCFA',
 'Franchise : 25.000.000 FCFA par sinistre',
 'Garanties : dommages materiels aux travaux, responsabilite civile dommages aux tiers.',
 'Exclusions :',
 'les evenements naturels (inondation, tempete),',
 'les dommages resultant d un vice de conception,',
 'les dommages corporels des travailleurs.',
 'La presente attestation est delivree sous reserve du paiement de la prime.'])
print('ok')
