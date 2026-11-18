# v9.19 — analyseur de garanties : conformité d'une garantie reçue aux exigences du marché (préparer avec python3 tests/t39_gen.py)
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  c=b.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True);pg=c.new_page();pg.set_default_timeout(20000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500)
  pg.evaluate("""db.marches.push({id:'m1',titulaire:'SOGEA SATOM <img src=x onerror=window.__x=1>',num:'2026-0001',objet:'Traversée d’Adjamé',montant:'1000000000',debut:'2026-03-01',delaiM:'18',notif:'2026-01-10'});
   db.garanties.push({id:'g1',marche:'m1',type:'Bonne exécution',organisme:'NSIA Banque',montant:'40000000',emission:'2026-01-25',echeance:'2027-12-31',statut:'Active'});
   db.garanties.push({id:'g2',marche:'m1',type:'Bonne exécution',organisme:'Coris Bank',montant:'20000000',emission:'2026-03-15',echeance:'2026-06-01',statut:'Active'});
   db.garanties.push({id:'g3',marche:'m1',type:'Avance de démarrage',organisme:'SGBCI',montant:'100000000',emission:'2026-02-20',statut:'Active'});
   db.garanties.push({id:'g4',marche:'m1',type:'Bonne exécution',statut:'Active'});
   save();go('conf')""");pg.wait_for_timeout(600)
  P('section visible :','Analyser une garantie reçue' in pg.inner_text('#v') and 'Exigences de garantie de ce marché' in pg.inner_text('#v'))
  # pièces jointes
  for gid,f in [('g1','/tmp/gar_ok.pdf'),('g2','/tmp/gar_ko.pdf'),('g4','/tmp/gar_ok.pdf')]:
    pg.evaluate(f"docs('garanties','{gid}')");pg.wait_for_timeout(300);pg.set_input_files('#ff',f);pg.wait_for_timeout(4000)
  pg.evaluate("$('#cd').close();go('conf')");pg.wait_for_timeout(400)
  P('fichiers joints :',pg.evaluate("db.garanties.map(g=>(g.files||[]).length).join(',')")=='1,1,0,1')
  # g1 : garantie conforme au référentiel (3 à 5 %, remise sous 21 j, validité jusqu'à la réception provisoire)
  pg.evaluate("GAP='g1';render()");pg.evaluate("gaGo('g1')");pg.wait_for_function("GAR.g1!=null",timeout=20000);pg.wait_for_timeout(400)
  R=pg.evaluate("(()=>{const R=GAR.g1;return{v:R.verdict,c:R.cnt,C:R.C.map(c=>c.g+'|'+c.l+'|'+c.v+'|'+c.co),det:R.det}})()")
  [P('  ko',x[:160]) for x in R['C'] if '|ko|' in x]
  P('g1 aucun non conforme :',R['c']['ko']==0)
  P('g1 valeurs lues :',R['det'].get('organisme')=='NSIA Banque' and R['det'].get('montant')==40000000 and R['det'].get('emission')=='2026-01-25' and R['det'].get('echeance')=='2027-12-31' and R['det'].get('ref')=='GBE-2026-0451')
  f=lambda R,l:[x for x in R['C'] if x.startswith(l)]
  P('g1 montant 4 % conforme :',any(x.split('|')[2]=='ok' and '4' in x.split('|')[3] for x in f(R,'Montants|Montant de la garantie')))
  P('g1 remise dans le délai :',any('|ok|' in x for x in f(R,'Délais|Délai de remise')))
  P('g1 durée suffisante :',any('|ok|' in x for x in f(R,'Délais|Durée de validité')))
  P('g1 clauses lues :',all(any(x.startswith('Clauses exigées|'+l) and '|ok|' in x for x in R['C']) for l in ['Bénéficiaire','Garanti (donneur','Marché identifié','Engagement irrévocable','Paiement à première demande','Libération au procès-verbal de réception provisoire','Conformité au modèle']))
  P('g1 reste « à vérifier » tant que agrément / authenticité non confirmés :',R['v']=='chk' and any('|chk|' in x for x in f(R,'Identification|Organisme habilité')) and any('|chk|' in x for x in f(R,'Vérifications|Authenticité')))
  pg.evaluate("gaSetS('g1','ag',true)");pg.evaluate("gaSetS('g1','au',true)");pg.evaluate("gaGo('g1')");pg.wait_for_function("GAR.g1!=null");pg.wait_for_timeout(300)
  P('g1 conforme après confirmations :',pg.evaluate("GAR.g1.verdict")=='ok' and 'CONFORME' in pg.inner_text('#gaR'))
  # g2 : garantie non conforme
  pg.evaluate("GAP='g2';render()");pg.evaluate("gaGo('g2')");pg.wait_for_function("GAR.g2!=null",timeout=20000);pg.wait_for_timeout(400)
  R=pg.evaluate("(()=>{const R=GAR.g2;return{v:R.verdict,c:R.cnt,C:R.C.map(c=>c.g+'|'+c.l+'|'+c.v+'|'+c.co),det:R.det}})()")
  [P('  ko',x[:150]) for x in R['C'] if '|ko|' in x]
  P('g2 verdict NON CONFORME :',R['v']=='ko' and 'NON CONFORME' in pg.inner_text('#gaR'))
  P('g2 montant 2 % trop bas :',any('|ko|' in x for x in f(R,'Montants|Montant de la garantie')))
  P('g2 remise tardive (64 j) :',any('|ko|' in x for x in f(R,'Délais|Délai de remise')))
  P('g2 durée insuffisante :',any('|ko|' in x for x in f(R,'Délais|Durée de validité')))
  P('g2 titulaire non retrouvé :',any('|ko|' in x for x in f(R,'Clauses exigées|Garanti (donneur')))
  P('g2 première demande non retrouvée (caution simple) :',any('|chk|' in x for x in f(R,'Clauses exigées|Paiement à première demande')))
  P('g2 libération à la réception définitive signalée :',any('|chk|' in x and 'autre événement' in x for x in f(R,'Clauses exigées|Libération')))
  P('g2 conditions restrictives et exclusions à lire :',len(f(R,'À lire|Conditions restrictives'))==1 and len(f(R,'À lire|Exclusions'))==1)
  P('g2 valeurs lues (Coris, 20 M, CB-77-2026) :',R['det'].get('organisme')=='Coris Bank International' and R['det'].get('montant')==20000000 and R['det'].get('ref')=='CB-77-2026')
  # décision manuelle
  i=pg.evaluate("GAR.g2.C.findIndex(c=>c.l=='Conformité au modèle (formulaire) du DAO')");pg.evaluate(f"gaOv('g2',{i},'na')");pg.wait_for_timeout(700)
  P('décision manuelle conservée :',pg.evaluate("GAR.g2.C.find(c=>c.l=='Conformité au modèle (formulaire) du DAO').v=='na'&&gaState(db.garanties[1]).ov['Clauses exigées|Conformité au modèle (formulaire) du DAO']=='na'"))
  # courrier de réserves, rapport
  L=pg.evaluate("lettres('garanties',db.garanties[1]).map(t=>t.f)");P('courrier de réserves proposé :','reserves_garantie' in L and 'prorogation_garantie' in L)
  T=pg.evaluate("lettres('garanties',db.garanties[1]).find(t=>t.f=='reserves_garantie').t");P('courrier cite les écarts :','Non-conformités relevées' in T and 'Montant de la garantie' in T and 'Délai de remise' in T)
  pg.evaluate("window.print=()=>{window.__p=document.body.classList.contains('pfs')&&$('#fs').textContent.includes('Analyse de conformité d’une garantie')&&$('#fs').textContent.includes('NON CONFORME')&&$('#fs').textContent.includes('Suites à donner')}");pg.evaluate("gaPrint('g2')");pg.wait_for_timeout(400);P('rapport imprimable :',pg.evaluate("window.__p===true"))
  # g3 : avance — montant de l'avance à renseigner puis comparé
  pg.evaluate("GAP='g3';render()");pg.evaluate("gaGo('g3')");pg.wait_for_function("GAR.g3!=null");pg.wait_for_timeout(300)
  P('g3 avance inconnue : à vérifier :',pg.evaluate("GAR.g3.C.find(c=>c.l=='Montant de la garantie').v")=='chk')
  pg.evaluate("gaSetS('g3','av','150000000')");pg.evaluate("gaGo('g3')");pg.wait_for_function("GAR.g3!=null");pg.wait_for_timeout(300)
  P('g3 garantie < avance : non conforme :',pg.evaluate("GAR.g3.C.find(c=>c.l=='Montant de la garantie').v")=='ko')
  pg.evaluate("gaSetS('g3','av','100000000')");pg.evaluate("gaGo('g3')");pg.wait_for_function("GAR.g3!=null");pg.wait_for_timeout(300)
  P('g3 garantie = avance : conforme :',pg.evaluate("GAR.g3.C.find(c=>c.l=='Montant de la garantie').v")=='ok')
  # g4 : fiche vide, valeurs lues dans le document ; appliquer sans écraser
  pg.evaluate("GAP='g4';render()");pg.evaluate("gaGo('g4')");pg.wait_for_function("GAR.g4!=null");pg.wait_for_timeout(300)
  pg.evaluate("gaApply('g4')");pg.wait_for_timeout(300)
  P('appliqué sans écraser :',pg.evaluate("(()=>{const g=db.garanties[3];return g.organisme=='NSIA Banque'&&g.montant==40000000&&g.emission=='2026-01-25'&&g.echeance=='2027-12-31'&&g.doc=='GBE-2026-0451'})()"))
  pg.evaluate("db.garanties[3].organisme='Autre';gaApply('g4')");P('rien d’écrasé au 2e passage :',pg.evaluate("db.garanties[3].organisme")=='Autre')
  # exigences du CCAP lues depuis un texte collé (le référentiel reste la valeur par défaut)
  pg.evaluate("""gaPxTx('m1',"Article 15 - Garanties. La garantie de bonne exécution est fixée à 5 % du montant du marché ; elle est remise dans un délai de 15 jours ouvrables après la notification d'approbation et reste valable jusqu'à la réception provisoire, sous la forme d'une garantie irrévocable payable à première demande. La retenue de garantie est plafonnée à 5 % du marché et libérée à la réception définitive. La garantie de soumission est de 10 000 000 FCFA. La garantie de restitution d'avance couvre 100 % de l'avance de démarrage.")""")
  pg.evaluate("gaCcap('m1')");pg.wait_for_timeout(300)
  px=pg.evaluate("gaPx(mk('m1')).t")
  P('CCAP lu — bonne exécution :',px['Bonne exécution']['pmin']==5 and px['Bonne exécution']['pmax']==5 and px['Bonne exécution']['em']==21 and px['Bonne exécution']['vf']=='rp' and 'pd' in px['Bonne exécution']['c'] and 'irr' in px['Bonne exécution']['c'])
  P('CCAP lu — retenue / soumission / avance :',px['Retenue de garantie']['pmax']==5 and px['Retenue de garantie']['vf']=='rd' and px['Soumission']['cm']=='f' and px['Soumission']['cv']==10000000 and px['Avance de démarrage']['cm']=='a' and px['Avance de démarrage']['cv']==100)
  pg.evaluate("GAP='g1';gaGo('g1')");pg.wait_for_function("GAR.g1!=null");pg.wait_for_timeout(300)
  P('g1 (4 %) devient non conforme avec un CCAP à 5 % :',pg.evaluate("GAR.g1.C.find(c=>c.l=='Montant de la garantie').v")=='ko' and pg.evaluate("GAR.g1.def")==False)
  pg.evaluate("gaPxReset('m1',0)");pg.wait_for_timeout(200);P('retour au référentiel :',pg.evaluate("gaIsDef(gaPx(mk('m1')),'Bonne exécution')"))
  # texte collé (scan sans texte)
  pg.evaluate("db.garanties.push({id:'g5',marche:'m1',type:'Soumission',organisme:'BOA',montant:'10000000',statut:'Active',echeance:'2027-12-31'});save()")
  pg.evaluate("gaSetTx('g5','Garantie de soumission Bank of Africa. Marche n° 2026-0001. Beneficiaire : Autorite contractante. Garantie irrevocable et inconditionnelle, payable a premiere demande pour le compte de SOGEA SATOM COTE D IVOIRE.')")
  pg.evaluate("gaGo('g5')");pg.wait_for_function("GAR.g5!=null");pg.wait_for_timeout(300)
  R5=pg.evaluate("GAR.g5.C.map(c=>c.l+'|'+c.v)");P('g5 (texte collé) clauses ok :',all(any(x.startswith(l) and x.endswith('|ok') for x in R5) for l in ['Bénéficiaire','Marché identifié','Engagement irrévocable','Paiement à première demande']))
  P('g5 soumission : montant fixé par le DAO, à renseigner :',pg.evaluate("GAR.g5.C.find(c=>c.l=='Montant de la garantie').v")=='ko' or pg.evaluate("GAR.g5.C.find(c=>c.l=='Montant de la garantie').v")=='ok')
  # sans document : rien ne plante, points « à vérifier »
  pg.evaluate("db.garanties.push({id:'g6',marche:'m1',type:'Retenue de garantie',statut:'Active'});save()");pg.evaluate("gaGo('g6')");pg.wait_for_function("GAR.g6!=null");pg.wait_for_timeout(300)
  P('g6 sans document : verdict à vérifier :',pg.evaluate("GAR.g6.verdict")=='chk')
  # type inconnu / garantie terminée
  pg.evaluate("db.garanties.push({id:'g7',marche:'m1',type:'Autre',statut:'Active'});db.garanties.push({id:'g8',marche:'m1',type:'Bonne exécution',organisme:'NSIA Banque',montant:'40000000',statut:'Mainlevée obtenue'});save()")
  pg.evaluate("gaGo('g7')");pg.wait_for_function("GAR.g7!=null");pg.wait_for_timeout(200);P('g7 type inconnu : message :',pg.evaluate("!!GAR.g7.note"))
  pg.evaluate("gaGo('g8')");pg.wait_for_function("GAR.g8!=null");pg.wait_for_timeout(200);P('g8 mainlevée : validité sans objet :',pg.evaluate("GAR.g8.C.find(c=>c.l=='Garantie en cours de validité').v")=='na')
  # liste des garanties : bouton et pastille
  pg.evaluate("go('garanties')");pg.wait_for_timeout(300)
  P('liste : bouton 🔍 et pastille de verdict :',pg.evaluate("document.querySelectorAll('#tb button[title*=\"Analyser cette garantie\"]').length")>=4 and '🔍' in pg.inner_text('#tb'))
  pg.evaluate("gaOpen('g2')");pg.wait_for_timeout(500);P('gaOpen ouvre la conformité sur la bonne garantie :',pg.evaluate("tab=='conf'&&cfm=='m1'&&GAP=='g2'"))
  # sécurité : XSS, sanDB, états corrompus, fusion
  P('XSS :',pg.evaluate("window.__x===undefined"),'| échappé :','<img src=x' not in pg.inner_html('#v'))
  pg.evaluate("gaSetTx('g5','<img src=x onerror=window.__y=1> Marche n° 2026-0001');GAP='g5'");pg.evaluate("gaGo('g5')");pg.wait_for_function("GAR.g5!=null");pg.wait_for_timeout(300)
  P('XSS via texte collé :',pg.evaluate("window.__y===undefined") and '<img src=x' not in pg.inner_html('#v'))
  S=pg.evaluate("(()=>{const d=sanDB(JSON.parse(JSON.stringify(db)));return{gx:d.marches[0].gx.length>10,gan:d.garanties[1].gan.length>10,ganp:d.garanties[1].ganp.length>10,gantx:d.garanties.find(g=>g.id=='g5').gantx.length>5}})()");P('gx/gan/ganp/gantx survivent à sanDB :',all(S.values()))
  pg.evaluate("db.garanties[0].gan='{\"ov\":\"__proto__\",\"v\":\"<b>\"}';db.marches[0].gx='[1,2]'");P('états corrompus tolérés :',pg.evaluate("(()=>{try{gaState(db.garanties[0]);gaPx(db.marches[0]);gaRun(db.garanties[0],db.marches[0],'',{});return true}catch(e){return false}})()"))
  pg.evaluate("db.marches[0].gx=JSON.stringify({t:{'Soumission':{c:'zzz',pmin:'abc',pmax:{},cm:'x',cv:-5,em:1e9,vf:'??',vp:'a'},'Bonne exécution':'texte'}})");P('exigences corrompues : valeurs ramenées à des types sûrs :',pg.evaluate("(()=>{const c=gaNorm(gaCfg(gaPx(db.marches[0]),'Soumission'));return c.pmin==0&&c.pmax==0&&c.cm==''&&c.cv==0&&c.em==365&&c.vf==''&&c.vp==0&&Array.isArray(c.c)&&c.c.length==0})()"))
  pg.evaluate("go('conf')");pg.wait_for_timeout(400);P('page conformité rendue malgré des exigences corrompues :','Analyser une garantie reçue' in pg.inner_text('#v'))
  M=pg.evaluate("(()=>{const L=JSON.parse(JSON.stringify(db)),R=JSON.parse(JSON.stringify(db));R.marches[0].gx='{\"t\":{\"Soumission\":{\"r\":0}}}';R.marches[0]._u=Date.now()+5000;return mergeDB(L,R).marches[0].gx})()");P('fusion sync :','Soumission' in M)
  # journal
  P('journal :',pg.evaluate("db.journal.some(j=>j.m.startsWith('Analyse de conformité de garantie'))"))
  # tous les onglets sans erreur
  for t in ['dash','marches','garanties','assurances','conf','stats','pres','search']:pg.evaluate(f"go('{t}')");pg.wait_for_timeout(150)
  pg.screenshot(path='/tmp/t39.png',full_page=True)
  P('erreurs :',errs);b.close()
