import json,hashlib
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
DB={};errs=[]
def handle(route):
  req=route.request;fn=req.url.split('/rpc/')[1];a=json.loads(req.post_data or '{}')
  h=hashlib.sha256(a.get('p_auth','').encode()).hexdigest();row=DB.get(a['p_id']);ok=row and row['h']==h
  if fn=='ptua_get':out=[{'ver':row['ver'],'blob':row['blob']}] if ok else []
  elif a['p_ver']==0:
    out=-1 if row else 1
    if not row: DB[a['p_id']]={'h':h,'ver':1,'blob':a['p_blob']}
  elif ok and row['ver']==a['p_ver']: row['ver']+=1;row['blob']=a['p_blob'];out=row['ver']
  else: out=-1
  route.fulfill(status=200,content_type='application/json',body=json.dumps(out))
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  def dev(mob=True):
    c=b.new_context(viewport={'width':393 if mob else 1280,'height':852},is_mobile=mob,has_touch=mob);pg=c.new_page();pg.set_default_timeout(8000)
    pg.route('https://iofbwpzhptctyelmylkz.supabase.co/**',handle);pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
    pg.goto('http://localhost:8765/');pg.wait_for_timeout(2300);return pg
  def enc(pg,c):
    pg.fill('#cd input[name=a]',c);pg.fill('#cd input[name=b]',c);pg.click('#cd .pri');pg.wait_for_timeout(3000)
  pc=dev(False)
  pc.evaluate("db.marches.push({id:'m1',titulaire:'SOGEA SATOM',num:'2024-0153',montant:'850000000'});save();go('assurances')");pc.wait_for_timeout(300)
  P('onglet présent :',pc.evaluate("$('#nav').textContent.includes('Assurances')"))
  pc.click('#v button.pri');pc.wait_for_timeout(300)
  pc.select_option('#df select[name=marche]','m1');pc.select_option('#df select[name=type]','Tous risques chantier (TRC)')
  pc.fill('#df input[name=assureur]','NSIA Assurances');pc.fill('#df input[name=police]','TRC-2026-0042');pc.fill('#df input[name=montant]','850000000');pc.fill('#df input[name=prime]','4250000')
  pc.fill('#df input[name=effet]','2026-01-08');pc.fill('#df input[name=echeance]','2026-12-01');pc.click('#dlg .pri');pc.wait_for_timeout(500)
  P('assurance enregistrée :',pc.evaluate("db.assurances.map(a=>a.assureur+' / '+a.police+' / '+a.statut).join()"))
  P('alerte « 19 j restants » :',pc.evaluate("$('#tb').textContent.includes('j restants')"),'| bannière :',pc.evaluate("$('#al').textContent.includes('assurance(s) à renouveler')"))
  pc.screenshot(path='/tmp/as1.png')
  pc.evaluate("go('dash')");pc.wait_for_timeout(300)
  P('tableau de bord + échéancier :',pc.evaluate("document.body.innerText.includes('Assurances à renouveler')&&document.body.innerText.includes('Échéance d’assurance')"))
  pc.evaluate("window._f=null;dl=(n,t)=>{window._f=t};setTimeout(icsExp,0)");pc.wait_for_timeout(300);pc.click('#cd .pri');pc.wait_for_timeout(300);pc.click('#cd .pri');pc.wait_for_timeout(200)
  P('calendrier :',pc.evaluate("(window._f||'').includes('Échéance assurance')"))
  gq=pc.evaluate("gq='TRC-2026';go('search')");pc.wait_for_timeout(300);P('recherche :',pc.evaluate("$('#sr').textContent.includes('Assurances (1)')"))
  pc.evaluate("tab='assurances';expC=expC;let o='';const s=dl;dl=(n,t)=>window._c=t;expC();dl=s");P('CSV :',pc.evaluate("(window._c||'').split('\\n')[0].includes('Compagnie')"))
  # synchro vers iPhone
  pc.evaluate("setTimeout(syStart,0)");pc.wait_for_timeout(600);enc(pc,'Test#Motdepasse2026');pc.click('#cd button[data-i="0"]');pc.wait_for_timeout(2500);k=pc.evaluate("SY.code");pc.click('#cd .pri')
  ph=dev();ph.evaluate("setTimeout(syStart,0)");ph.wait_for_timeout(600);enc(ph,'Test#Autre2026xx');ph.click('#cd button[data-i="2"]');ph.wait_for_timeout(300);ph.fill('#syc',k);ph.click('#cd .pri');ph.wait_for_timeout(3500)
  P('iPhone reçoit l’assurance :',ph.evaluate("db.assurances.map(a=>a.police).join()"))
  ph.evaluate("go('assurances')");ph.wait_for_timeout(400);ph.screenshot(path='/tmp/as2.png')
  ph.evaluate("confirm=()=>true;del('marches','m1')");ph.wait_for_timeout(4000);pc.evaluate("syncNow()");pc.wait_for_timeout(2500)
  P('suppression du marché -> assurance supprimée partout :',ph.evaluate("db.assurances.length")==0 and pc.evaluate("db.assurances.length")==0)
  P('erreurs :',errs);b.close()
