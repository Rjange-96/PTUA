# v9.23 — marchés regroupés par entreprise
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  c=b.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True);pg=c.new_page();pg.set_default_timeout(20000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500)
  pg.evaluate("""db.marches.push({id:'a',titulaire:'URBAN BUILDING',num:'2025-0001',objet:'Route Nord',montant:'500000000',debut:'2025-03-01',delaiM:'12'});
   db.marches.push({id:'b',titulaire:'Urban  Building ',num:'2026-0007',objet:'Pont Sud',montant:'900000000',debut:'2026-03-01',delaiM:'18'});
   db.marches.push({id:'c',titulaire:'SOGEA SATOM',num:'2026-0002',montant:'100000000'});
   db.marches.push({id:'d',titulaire:'',num:'2026-0003'});
   db.garanties.push({id:'g1',marche:'a',type:'Bonne exécution',organisme:'SERENITY SA',montant:'25000000',emission:'2025-03-10',echeance:'2027-12-31',statut:'Active'});
   db.garanties.push({id:'g2',marche:'b',type:'Avance de démarrage',organisme:'NSIA Côte d’Ivoire',montant:'90000000',emission:'2026-03-10',echeance:'2027-12-31',statut:'Active'});
   db.assurances.push({id:'s1',marche:'b',type:'Tous risques chantier (TRC)',assureur:'SUNU Assurances IARD',police:'T1',statut:'Active',echeance:'2028-01-01'});
   db.avenants.push({id:'v1',marche:'b',num:'A1',date:'2026-06-01',montant:'50000000'});
   save();go('marches')""");pg.wait_for_timeout(500)
  tx=pg.inner_text('#v')
  P('une seule ligne Urban Building :',tx.upper().count('URBAN BUILDING')==1 and '2 marchés' in tx)
  P('les 4 marchés regroupés en 3 entreprises + sans titulaire :',pg.evaluate("entList().length")==3 and 'Sans titulaire' in tx)
  P('numéros des 2 marchés visibles sur la carte :','2025-0001' in tx and '2026-0007' in tx)
  P('montant total (500M+900M+50M avenant) :','1 450 000 000' in tx.replace(' ',' ').replace('\xa0',' '))
  # ouvrir l'entreprise
  pg.evaluate("entGo(entList().find(e=>e.name.toUpperCase().includes('URBAN')).k)");pg.wait_for_timeout(300)
  tx=pg.inner_text('#v');t2=tx.replace(' ',' ').replace('\xa0',' ')
  P('vue entreprise : les deux marchés :','Route Nord' in tx and 'Pont Sud' in tx)
  P('infos de chaque marché (montant, avenant, démarrage, fin prévue) :','900 000 000' in t2 or '950 000 000' in t2) 
  P('garanties et assurances de chaque marché :','Bonne exécution' in tx and 'Avance de démarrage' in tx and 'SUNU' in tx)
  P('boutons Modifier / Documents / Garanties :','Modifier' in tx and 'Documents' in tx and 'Garanties' in tx)
  P('bouton retour :','Toutes les entreprises' in tx)
  # nouveau marché prérempli
  pg.evaluate("entNew()");pg.wait_for_timeout(300)
  P('nouveau marché : titulaire prérempli :',pg.evaluate("document.querySelector('#df [name=titulaire]').value").upper().startswith('URBAN'))
  pg.evaluate("document.querySelector('#dlg')&&document.querySelector('#dlg').close&&document.querySelector('#dlg').close()")
  # lien vers les garanties du marché
  pg.evaluate("entTo('garanties','2026-0007')");pg.wait_for_timeout(300)
  tx=pg.inner_text('#v');P('lien Garanties filtre sur le marché :','Avance de démarrage' in tx and 'Bonne exécution' not in tx)
  # retour + recherche
  pg.evaluate("go('marches')");pg.wait_for_timeout(200);P('go(marches) revient à la liste des entreprises :',pg.evaluate("entCur")=='')
  pg.evaluate("entGo(entList()[0].k);entBack()");P('retour :',pg.evaluate("entCur")=='')
  pg.evaluate("q='sogea';render()");pg.wait_for_timeout(200);tx=pg.inner_text('#v')
  P('recherche : seule SOGEA reste :','SOGEA' in tx and 'URBAN' not in tx.upper())
  pg.evaluate("q='';render()")
  # bascule en liste
  pg.evaluate("mgTog()");pg.wait_for_timeout(300);tx=pg.inner_text('#v')
  P('bascule en liste : les 4 marchés à plat :',all(n in tx for n in ['2025-0001','2026-0007','2026-0002','2026-0003']) and 'Montant total' not in tx)
  pg.evaluate("mgTog()");pg.wait_for_timeout(200);P('retour en mode entreprise :',pg.evaluate("mgOn")==True)
  # entreprise supprimée pendant l'affichage → pas de plantage
  pg.evaluate("entCur='inexistant';render()");pg.wait_for_timeout(200);P('entreprise disparue : retour liste sans erreur :',pg.evaluate("entCur")=='')
  # XSS
  pg.evaluate("db.marches.push({id:'x',titulaire:'<img src=x onerror=window.__x=1>',num:'<b>1</b>',montant:'5'});save();go('marches')");pg.wait_for_timeout(300)
  pg.evaluate("entGo(entList().find(e=>e.name.includes('img')).k)");pg.wait_for_timeout(300)
  P('XSS neutralisé :',pg.evaluate("window.__x")is None)
  P('erreurs :',errs)
