# v9.13 — analyse de conformité d'une assurance reçue par rapport aux exigences du marché (préparer avec python3 tests/t34_gen.py)
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path=__import__('shutil').which('google-chrome'))
  c=b.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True);pg=c.new_page();pg.set_default_timeout(20000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500)
  pg.evaluate("""db.marches.push({id:'m1',titulaire:'SOGEA SATOM <img src=x onerror=window.__x=1>',num:'2026-0001',objet:'Traversée d’Adjamé',montant:'1000000000',debut:'2026-03-01',delaiM:'18'});
   db.assurances.push({id:'a1',marche:'m1',type:'Tous risques chantier (TRC)',assureur:'NSIA',police:'TRC-2026-00451',assure:'SOGEA SATOM CI',montant:'1200000000',effet:'2026-03-01',echeance:'2028-12-31',statut:'Active'});
   db.assurances.push({id:'a2',marche:'m1',type:'Tous risques chantier (TRC)',assureur:'',police:'',assure:'BATIMAX SARL',montant:'300000000',effet:'2026-04-15',echeance:'2026-06-30',statut:'Active'});
   save();go('conf')""");pg.wait_for_timeout(600)
  P('section visible :','Analyser une assurance reçue' in pg.inner_text('#v'))
  # exigences CCAP lues depuis un texte collé
  pg.evaluate("""anPxTx('m1',"Article 12 - Assurances. Le titulaire souscrit une assurance tous risques chantier dès l'ordre de service de démarrage, pour un capital au moins égal à 100 % du montant du marché, valable jusqu'à la réception définitive, avec une franchise maximale de 5 000 000 FCFA, couvrant les événements naturels et le vice de conception, les sous-traitants, avec renonciation à recours contre le maître d'ouvrage. Il souscrit également une responsabilité civile couvrant les dommages corporels et matériels causés aux tiers pendant toute la durée des travaux.")""")
  pg.evaluate("anCcap('m1')");pg.wait_for_timeout(300)
  px=pg.evaluate("anPx(mk('m1')).t")
  P('CCAP lu — TRC :',px['TRC']['cm']=='m' and px['TRC']['cv']==100 and px['TRC']['fm']==5000000 and px['TRC']['vf']=='rd' and px['TRC']['e']==1 and 'en' in px['TRC']['g'] and 'vc' in px['TRC']['g'] and 'st' in px['TRC']['c'] and 'rr' in px['TRC']['c'])
  P('CCAP lu — RC :','RC' in px and px['RC']['vf']=='fin' and 'tm' in px['RC']['g'] and 'tc' in px['RC']['g'])
  # pièces jointes
  pg.evaluate("docs('assurances','a1')");pg.wait_for_timeout(300);pg.set_input_files('#ff','/tmp/att_ok.pdf');pg.wait_for_timeout(4000)
  pg.evaluate("docs('assurances','a2')");pg.wait_for_timeout(300);pg.set_input_files('#ff','/tmp/att_ko.pdf');pg.wait_for_timeout(4000)
  pg.evaluate("$('#cd').close();go('conf')");pg.wait_for_timeout(400)
  P('fichiers joints :',pg.evaluate("db.assurances.map(a=>(a.files||[]).length).join(',')")=='1,1')
  # analyse de la bonne attestation
  pg.evaluate("anPol='a1';render()");pg.evaluate("anGo('a1')");pg.wait_for_function("ANR.a1!=null",timeout=20000);pg.wait_for_timeout(400)
  R=pg.evaluate("(()=>{const R=ANR.a1;return{v:R.verdict,c:R.cnt,C:R.C.map(c=>c.g+'|'+c.l+'|'+c.v),det:R.det}})()")
  [P('  ok',x) for x in R['C'] if x.endswith('|ko')]
  P('a1 verdict :',R['v'],R['c'])
  P('a1 aucun non conforme :',R['c']['ko']==0)
  P('a1 valeurs lues :',R['det'].get('police')=='TRC-2026-00451' and R['det'].get('capital')==1200000000 and R['det'].get('effet')=='2026-03-01' and R['det'].get('echeance')=='2028-12-31' and R['det'].get('franchise')==2000000 and R['det'].get('assureur')=='NSIA Assurances' and R['det'].get('preavis')==30)
  P('a1 n° marché retrouvé :',any(x.startswith('Clauses exigées|Marché ou chantier') and x.endswith('|ok') for x in R['C']))
  P('a1 garanties lues :',all(any(x.startswith('Garanties exigées|'+l) and x.endswith('|ok') for x in R['C']) for l in ['Dommages matériels','Responsabilité civile','Dommages corporels','Vice de conception','Événements naturels']))
  P('a1 sous-traitants / recours / préavis ok :',all(any(x.startswith('Clauses exigées|'+l) and x.endswith('|ok') for x in R['C']) for l in ['Sous-traitants','Renonciation']))
  # franchise relevée -> conforme
  pg.evaluate("anSetS('a1','fr','2000000')");pg.evaluate("anGo('a1')");pg.wait_for_function("ANR.a1!=null");pg.wait_for_timeout(300)
  P('a1 franchise conforme :',pg.evaluate("ANR.a1.C.find(c=>c.l=='Franchise').v")=='ok')
  P('a1 rendu dans la page :','CONFORME' in pg.inner_text('#anR'))
  # analyse de l'attestation non conforme
  pg.evaluate("anPol='a2';render()");pg.evaluate("anGo('a2')");pg.wait_for_function("ANR.a2!=null",timeout=20000);pg.wait_for_timeout(400)
  R=pg.evaluate("(()=>{const R=ANR.a2;return{v:R.verdict,c:R.cnt,C:R.C.map(c=>c.g+'|'+c.l+'|'+c.v+'|'+c.co),det:R.det}})()")
  ko=[x for x in R['C'] if '|ko|' in x];[P('  ko',x[:150]) for x in ko]
  P('a2 verdict NON CONFORME :',R['v']=='ko')
  f=lambda l:[x for x in R['C'] if x.startswith(l)]
  P('a2 assuré ≠ titulaire :',any('|ko|' in x for x in f('Identification|Assuré = titulaire')))
  P('a2 effet après démarrage :',any('|ko|' in x for x in f('Période|Garantie effective')))
  P('a2 durée insuffisante :',any('|ko|' in x for x in f('Période|Durée de validité')))
  P('a2 capital insuffisant :',any('|ko|' in x for x in f('Montants|Capital assuré')))
  P('a2 événements naturels exclus :',any('|ko|' in x and 'exclusion' in x for x in f('Garanties exigées|Événements naturels')))
  P('a2 vice de conception exclu :',any('|ko|' in x for x in f('Garanties exigées|Vice de conception')))
  P('a2 dommages corporels exclus :',any('|ko|' in x for x in f('Garanties exigées|Dommages corporels')))
  P('a2 prime sous réserve :',any('|ko|' in x for x in f('Clauses exigées|Prime payée')))
  P('a2 sous-traitants non retrouvés :',any('|chk|' in x for x in f('Clauses exigées|Sous-traitants')))
  P('a2 compagnie et n° manquants (lus : Allianz, 77-AB-2026) :',R['det'].get('assureur')=='Allianz Côte d’Ivoire' and R['det'].get('police')=='77-AB-2026' and R['det'].get('franchise')==25000000)
  # appliquer les valeurs lues : ne remplit que les champs vides
  pg.evaluate("anApply('a2')");pg.wait_for_timeout(300)
  P('appliqué sans écraser :',pg.evaluate("db.assurances[1].assureur=='Allianz Côte d’Ivoire'&&db.assurances[1].police=='77-AB-2026'&&db.assurances[1].montant=='300000000'&&anState(db.assurances[1]).fr==25000000"))
  pg.evaluate("anGo('a2')");pg.wait_for_function("ANR.a2!=null");pg.wait_for_timeout(300)
  P('a2 franchise trop élevée :',pg.evaluate("ANR.a2.C.find(c=>c.l=='Franchise').v")=='ko')
  # décision manuelle
  i=pg.evaluate("ANR.a2.C.findIndex(c=>c.l=='Sous-traitants couverts')");pg.evaluate(f"anOv('a2',{i},'na')");pg.wait_for_timeout(600)
  P('décision manuelle conservée :',pg.evaluate("ANR.a2.C.find(c=>c.l=='Sous-traitants couverts').v=='na'&&anState(db.assurances[1]).ov['Clauses exigées|Sous-traitants couverts']=='na'"))
  # courrier de réserves et rapport
  L=pg.evaluate("lettres('assurances',db.assurances[1]).map(t=>t.f)");P('courrier de réserves proposé :','reserves_assurance' in L)
  T=pg.evaluate("lettres('assurances',db.assurances[1]).find(t=>t.f=='reserves_assurance').t");P('courrier cite les écarts :','Non-conformités relevées' in T and 'Capital assuré' in T and 'Événements naturels' in T)
  pg.evaluate("window.print=()=>{window.__p=document.body.classList.contains('pfs')&&$('#fs').textContent.includes('NON CONFORME')&&$('#fs').textContent.includes('Suites à donner')}");pg.evaluate("anPrint('a2')");pg.wait_for_timeout(400);P('rapport imprimable :',pg.evaluate("window.__p===true"))
  # texte collé (scan sans texte)
  pg.evaluate("db.assurances.push({id:'a3',marche:'m1',type:'Responsabilité civile (RC)',assureur:'SUNU',police:'RC1',assure:'SOGEA SATOM CI',montant:'50000000',effet:'2026-03-01',echeance:'2027-12-31',statut:'Active'});save()")
  pg.evaluate("anSetTx('a3','Attestation RC police RC1. Marche n° 2026-0001. Garantie : dommages corporels et dommages materiels causes aux tiers, pollution accidentelle.')")
  pg.evaluate("anGo('a3')");pg.wait_for_function("ANR.a3!=null");pg.wait_for_timeout(300)
  R3=pg.evaluate("ANR.a3.C.map(c=>c.l+'|'+c.v)");P('a3 (texte collé) tiers matériels/corporels ok :',all(any(x.startswith(l) and x.endswith('|ok') for x in R3) for l in ['Dommages matériels causés aux tiers','Dommages corporels causés aux tiers']))
  # sans document : rien ne plante, points « à vérifier »
  pg.evaluate("db.assurances.push({id:'a4',marche:'m1',type:'Garantie décennale',assureur:'',police:'',statut:'Active'});save()");pg.evaluate("anGo('a4')");pg.wait_for_function("ANR.a4!=null");pg.wait_for_timeout(300)
  P('a4 sans document : verdict à vérifier :',pg.evaluate("ANR.a4.verdict")=='chk')
  # type « Autre » sans exigence associée
  pg.evaluate("db.assurances.push({id:'a5',marche:'m1',type:'Autre',assureur:'X',police:'Y',statut:'Active'});save()");pg.evaluate("anGo('a5')");pg.wait_for_function("ANR.a5!=null");pg.wait_for_timeout(300)
  P('a5 type Autre : message :',pg.evaluate("!!ANR.a5.note"));pg.evaluate("anSetS('a5','k','AT')");pg.evaluate("anGo('a5')");pg.wait_for_function("ANR.a5!=null");pg.wait_for_timeout(300);P('a5 forcé en AT :',pg.evaluate("ANR.a5.k")=='AT')
  # sécurité : XSS, sanDB, fusion de synchro
  P('XSS :',pg.evaluate("window.__x===undefined"),'| échappé :','<img src=x' not in pg.inner_html('#v'))
  pg.evaluate("anSetTx('a3','<img src=x onerror=window.__y=1>')");pg.evaluate("anGo('a3')");pg.wait_for_function("ANR.a3!=null");pg.wait_for_timeout(300)
  P('XSS via texte collé :',pg.evaluate("window.__y===undefined") and '<img src=x' not in pg.inner_html('#v'))
  S=pg.evaluate("(()=>{const d=sanDB(JSON.parse(JSON.stringify(db)));return{px:d.marches[0].px.length>10,an:d.assurances[1].an.length>10,anp:d.assurances[1].anp.length>10,antx:d.assurances[2].antx.length>5}})()");P('px/an/anp/antx survivent à sanDB :',all(S.values()))
  pg.evaluate("db.assurances[0].an='{\"ov\":\"__proto__\",\"k\":\"<b>\"}';db.marches[0].px='[1,2]'");P('états corrompus tolérés :',pg.evaluate("(()=>{try{anState(db.assurances[0]);anPx(db.marches[0]);anKey(db.assurances[0]);return true}catch(e){return false}})()"))
  M=pg.evaluate("(()=>{const L=JSON.parse(JSON.stringify(db)),R=JSON.parse(JSON.stringify(db));R.marches[0].px='{\"t\":{\"AT\":{\"r\":0}}}';R.marches[0]._u=Date.now()+5000;return mergeDB(L,R).marches[0].px})()");P('fusion sync :','AT' in M)
  # tous les onglets sans erreur
  for t in ['dash','marches','assurances','conf','stats','pres','search']:pg.evaluate(f"go('{t}')");pg.wait_for_timeout(150)
  pg.screenshot(path='/tmp/t34.png',full_page=True)
  P('erreurs :',errs);b.close()
