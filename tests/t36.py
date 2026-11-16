# v9.15 — corbeille (suppression récupérable) et réception (réserves, levée, réception définitive)
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[];bad=0
def ck(n,c):
  global bad
  P(('OK  ' if c else 'ÉCHEC ')+n)
  if not c:bad+=1
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  c=b.new_context(viewport={'width':1280,'height':800});pg=c.new_page();pg.set_default_timeout(15000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and 'ERR_' not in m.text and 'Failed to load' not in m.text and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500);pg.evaluate("localStorage.clear()");pg.reload();pg.wait_for_timeout(2500)
  K="'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='"
  pg.evaluate("""async()=>{
   db.marches.push({id:'m1',num:'M-001',titulaire:'ACME',objet:'Route',montant:1000000,debut:'2026-01-01',delaiM:6,reception:'2026-08-01',garmois:12,_u:1});
   db.garanties.push({id:'g1',marche:'m1',type:'Bonne exécution',statut:'Active',montant:50000,_u:1});
   db.os.push({id:'o1',marche:'m1',num:'OS1',type:'Démarrage',date:'2026-01-01',_u:1});
   db.assurances.push({id:'a1',marche:'m1',type:'Responsabilité civile (RC)',statut:'Active',_u:1,files:[{id:'fx1',n:'police.pdf',t:'application/pdf',s:3,d:1,k:'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='}]});
   db.reunions.push({id:'r1',objet:'Réunion chantier',marche:'m1',date:'2026-02-01',_u:1});
   await fPut('fx1',new Uint8Array([1,2,3]));save();render()}""")
  # --- corbeille
  pg.evaluate("del('marches','m1')");pg.wait_for_timeout(200)
  ck('suppression : marché et éléments liés sortis des listes',pg.evaluate("db.marches.length==0&&db.garanties.length==0&&db.os.length==0&&db.assurances.length==0"))
  ck('suppression : une entrée en corbeille avec 4 éléments',pg.evaluate("db.trash.length==1&&trItems(db.trash[0])==4"))
  ck('suppression : réunion conservée mais détachée',pg.evaluate("db.reunions.length==1&&db.reunions[0].marche==''"))
  ck('suppression : tombstones de synchronisation posés',pg.evaluate("['m1','g1','o1','a1'].every(i=>db.del[i])"))
  ck('suppression : pièce jointe conservée (pas d’effacement)',pg.evaluate("!db.fdel||!db.fdel['fx1']")and pg.evaluate("fGet('fx1').then(v=>!!v)"))
  pg.evaluate("go('sauv')");pg.wait_for_timeout(300)
  ck('page Sauvegarde : carte Corbeille (1) avec Restaurer',pg.evaluate("document.body.innerText.includes('Corbeille (1)')&&document.body.innerText.includes('Restaurer')"))
  ck('sanitisation : la corbeille survit à sanDB',pg.evaluate("(()=>{const q=sanDB(JSON.parse(JSON.stringify(db)));return q.trash.length==1&&trItems(q.trash[0])==4&&q.trash[0].d.assurances[0].files.length==1})()"))
  # fusion de synchronisation pendant que c'est supprimé : l'ancienne copie distante ne ressuscite pas l'élément
  ck('synchro : la suppression l’emporte sur une ancienne copie distante',pg.evaluate("(()=>{const R={marches:[{id:'m1',num:'M-001',_u:1}],garanties:[],os:[],avenants:[],assurances:[],reunions:[],reserves:[],del:{},fdel:{},journal:[],tpl:[]};return mergeDB(syData(),R).marches.length==0})()"))
  pg.evaluate("trRest(db.trash[0].id)");pg.wait_for_timeout(300)
  ck('restauration : tout est revenu',pg.evaluate("db.marches.length==1&&db.garanties.length==1&&db.os.length==1&&db.assurances.length==1&&db.trash.length==0"))
  ck('restauration : réunion rattachée de nouveau',pg.evaluate("db.reunions[0].marche=='m1'"))
  ck('restauration : tombstones retirés, _u renouvelé',pg.evaluate("!db.del['m1']&&!db.del['g1']&&db.marches[0]._u>1000"))
  ck('restauration : la pièce jointe est toujours lisible',pg.evaluate("fGet('fx1').then(v=>!!v)"))
  ck('synchro : après restauration, une copie distante qui garde l’ancienne suppression ne l’efface pas',pg.evaluate("(()=>{const R={marches:[],garanties:[],os:[],avenants:[],assurances:[],reunions:[],reserves:[],del:{m1:Date.now()-5000},fdel:{},journal:[],tpl:[]};return mergeDB(syData(),R).marches.length==1})()"))
  # suppression d'une seule garantie, restauration
  pg.evaluate("del('garanties','g1')");pg.wait_for_timeout(200)
  ck('garantie seule : en corbeille',pg.evaluate("db.garanties.length==0&&db.trash.length==1&&trItems(db.trash[0])==1"))
  pg.evaluate("trRest(db.trash[0].id)");ck('garantie seule : restaurée',pg.evaluate("db.garanties.length==1&&db.garanties[0].id=='g1'"))
  # suppression définitive
  pg.evaluate("del('assurances','a1')");pg.evaluate("trDel(db.trash[0].id)");pg.wait_for_timeout(400)
  ck('suppression définitive : corbeille vide et pièce jointe effacée',pg.evaluate("db.trash.length==0&&!!db.fdel['fx1']")and pg.evaluate("fGet('fx1').then(v=>!v)"))
  # purge automatique après 30 jours
  pg.evaluate("del('os','o1')");pg.evaluate("db.trash[0].t=Date.now()-31*864e5");pg.evaluate("render()");pg.wait_for_timeout(300)
  ck('purge automatique après 30 jours',pg.evaluate("db.trash.length==0&&db.os.length==0"))
  pg.evaluate("del('os','x_inexistant')") if False else None
  pg.evaluate("del('garanties','g1')");pg.evaluate("trEmpty()");ck('vider la corbeille',pg.evaluate("db.trash.length==0"))
  # --- réception
  pg.evaluate("""()=>{const d=x=>{const t=new Date(Date.now()+x*864e5);return t.toISOString().slice(0,10)};
   db.garanties.length=0;db.marches[0].reception=d(-350);db.marches[0].fin_garantie='';
   db.reserves.push({id:'s1',marche:'m1',type:'Réception provisoire',objet:'Fissures du mur de soutènement',date:d(-40),delai:30,statut:'Ouverte',_u:1});
   db.reserves.push({id:'s2',marche:'m1',type:'Réception provisoire',objet:'Signalisation',date:d(-5),delai:20,statut:'Ouverte',_u:1});
   db.reserves.push({id:'s3',marche:'m1',type:'Réception provisoire',objet:'Peinture',date:d(-60),delai:30,levee:d(-35),statut:'Levée',_u:1});
   save();render()}""")
  ck('réserve en retard détectée (statut rouge)',pg.evaluate("badgeR(db.reserves[0]).includes('En retard')&&badgeR(db.reserves[0]).includes(' r\"')"))
  ck('réserve dans les délais : jours restants',pg.evaluate("badgeR(db.reserves[1]).includes('15 j pour lever')"))
  ck('réserve levée : badge vert avec date',pg.evaluate("badgeR(db.reserves[2]).includes('Levée le')"))
  ck('resLate : 1 réserve en retard',pg.evaluate("resLate('m1').length==1"))
  ck('réception définitive attendue : prévue dans ~15 j (12 mois après la provisoire)',pg.evaluate("(()=>{const x=recDef(db.marches[0]);return x&&x.j>=13&&x.j<=17})()"))
  ck('pas de réception définitive attendue si déjà renseignée',pg.evaluate("(()=>{const m={...db.marches[0],fin_garantie:'2026-01-01'};return recDef(m)==null})()"))
  ck('alertes de réception : 3 éléments (réserve en retard, réserve proche, réception définitive)',pg.evaluate("recAl().length==3"))
  pg.evaluate("go('dash')");pg.wait_for_timeout(300)
  ck('tableau de bord : carte Réception et réserves',pg.evaluate("document.body.innerText.includes('Réception et réserves')&&document.body.innerText.includes('Fissures du mur')"))
  ck('bandeau : alerte de réception',pg.evaluate("document.querySelector('#al').innerText.includes('échéance(s) de réception')"))
  ck('échéancier : levée de réserve et réception définitive',pg.evaluate("document.body.innerText.includes('Levée de réserve attendue')&&document.body.innerText.includes('Réception définitive attendue')"))
  pg.evaluate("go('reserves')");pg.wait_for_timeout(300)
  ck('onglet Réserves : 3 lignes et colonne Levée',pg.evaluate("document.querySelectorAll('#tb tr').length==4&&document.querySelector('#tb').innerText.includes('Levée')"))
  pg.evaluate("edit('reserves')");pg.wait_for_timeout(200)
  ck('formulaire réserve : champs attendus',pg.evaluate("['marche','type','objet','date','delai','levee','statut'].every(n=>!!document.querySelector('#df [name=\"'+n+'\"]'))"))
  pg.evaluate("$('#dlg').close()")
  ck('formulaire marché : délai de garantie et réception définitive',pg.evaluate("(edit('marches','m1'),['garmois','fin_garantie'].every(n=>!!document.querySelector('#df [name=\"'+n+'\"]')))"))
  pg.evaluate("$('#dlg').close()")
  ck('courrier : 3 modèles pour une réserve',pg.evaluate("lettres('reserves',db.reserves[0]).map(t=>t.f).join()=='reserve_notification,reserve_relance,reserve_levee'"))
  ck('courrier : relance cite la réserve et le délai expiré',pg.evaluate("(()=>{const t=lettres('reserves',db.reserves[0])[1].t;return t.includes('Fissures du mur')&&t.includes('a expiré')})()"))
  ck('conformité : réserve en retard signalée',pg.evaluate("cfGar(db.marches[0]).some(x=>x[0]=='warn'&&x[1].includes('Réserve non levée'))"))
  ck('suppression du marché : réserves emportées puis restaurées',pg.evaluate("(()=>{del('marches','m1');const a=db.reserves.length==0&&trItems(db.trash[0])>=4;trRest(db.trash[0].id);return a&&db.reserves.length==3})()"))
  ck('sanDB : les réserves sont rattachées à leur marché',pg.evaluate("(()=>{const q=sanDB(JSON.parse(JSON.stringify(db)));return q.reserves.length==3&&q.reserves.every(r=>q.marches.some(m=>m.id==r.marche))})()"))
  ck('syData contient les réserves (synchronisées)',pg.evaluate("syData().reserves.length==3"))
  ck('aucune erreur JavaScript',not errs)
  if errs:P(errs[:5])
  b.close()
P('ÉCHECS :',bad)
raise SystemExit(1 if bad else 0)
