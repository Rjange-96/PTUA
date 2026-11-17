# v9.19 — génère deux garanties PDF (texte réel) pour tests/t39.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
def mk(path,lines):
  c=canvas.Canvas(path,pagesize=A4);y=800
  for l in lines:
    if y<60:c.showPage();y=800
    c.setFont('Helvetica',10);c.drawString(40,y,l);y-=16
  c.save()
mk('/tmp/gar_ok.pdf',[
 'NSIA BANQUE COTE D IVOIRE',
 'GARANTIE DE BONNE EXECUTION - Garantie n° GBE-2026-0451',
 'Beneficiaire : l Autorite contractante, Maitre d ouvrage',
 'Marche n° 2026-0001 - Construction de l ouvrage de la traversee d Adjame, Abidjan',
 'Donneur d ordre : SOGEA SATOM COTE D IVOIRE',
 'Montant de la garantie : 40.000.000 FCFA (quarante millions de francs CFA)',
 'Nous nous engageons de maniere irrevocable et inconditionnelle a payer le montant garanti a premiere demande,',
 'sans discussion ni justification, et renoncons au benefice de discussion et de division.',
 'La presente garantie prend fin a la date du proces-verbal de reception provisoire des travaux,',
 'ou par mainlevee donnee au beneficiaire. Valable jusqu au 31/12/2027.',
 'Garantie etablie conformement au modele du Dossier d Appel d Offres (DAO). Droit ivoirien, OHADA.',
 'Fait a Abidjan, le 25/01/2026. Signature et cachet de la banque.'])
mk('/tmp/gar_ko.pdf',[
 'CORIS BANK INTERNATIONAL',
 'Garantie bancaire - ref. n° CB-77-2026',
 'Pour le compte de BATIMAX SARL',
 'Montant : 20.000.000 FCFA',
 'La banque se porte caution simple de l entreprise.',
 'Le paiement sera effectue sous reserve de la production de justificatifs par le beneficiaire.',
 'Cette garantie est liberee a la reception definitive des travaux. Valable jusqu au 01/06/2026.',
 'Exclusions :',
 'les dommages resultant de la force majeure.',
 'Fait a Abidjan, le 15/03/2026.'])
print('ok')
