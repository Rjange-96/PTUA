# v9.17 — rappels sur le téléphone : dates d'alerte, abonnement (simulé), gestionnaires du service worker
import subprocess,json
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[];bad=0
def ck(n,c):
  global bad
  P(('OK  ' if c else 'ÉCHEC ')+n)
  if not c:bad+=1
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  c=b.new_context(viewport={'width':1100,'height':800},permissions=['notifications']);pg=c.new_page();pg.set_default_timeout(20000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and 'ERR_' not in m.text and 'Failed to load' not in m.text and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500);pg.evaluate("localStorage.clear()");pg.reload();pg.wait_for_timeout(2500)
  pg.evaluate("""()=>{const d=x=>new Date(Date.now()+x*864e5).toISOString().slice(0,10);
   db.marches.push({id:'m1',num:'M-1',titulaire:'ACME SECRET',debut:d(-100),delaiM:6,_u:1});
   db.assurances.push({id:'a1',marche:'m1',type:'Responsabilité civile (RC)',statut:'Active',echeance:d(40),_u:1});
   db.assurances.push({id:'a2',marche:'m1',type:'Décennale',statut:'Expirée',echeance:d(50),_u:1});
   db.garanties.push({id:'g1',marche:'m1',type:'Bonne exécution',statut:'Active',echeance:d(10),montant:123456,_u:1});
   save();go('sauv')}""");pg.wait_for_timeout(500)
  ck('carte Rappels visible avec bouton Activer',pg.evaluate("document.body.innerText.includes('Rappels sur ce téléphone')&&document.body.innerText.includes('Activer les rappels')"))
  due=pg.evaluate("pushDue()")
  now=pg.evaluate("Math.floor(Date.now()/1000)")
  ck('dates d’alerte : dans le futur, triées, sans doublon',due==sorted(set(due)) and all(t>now for t in due) and len(due)>=4)
  ck('assurance expirée : aucune alerte à sa date, assurance active : alerte',pg.evaluate("(()=>{const at=k=>{const g=new Date(Date.now()+k*864e5);return Math.floor(new Date(g.getFullYear(),g.getMonth(),g.getDate(),8).getTime()/1000)},x=pushDue();return !x.includes(at(50))&&!x.includes(at(43))&&x.includes(at(40))})()"))
  ck('garantie à 10 jours : alertes J-7, J-1 et J (J-30 déjà passé)',pg.evaluate("(()=>{const g=new Date(Date.now()+10*864e5),at=k=>Math.floor(new Date(g.getFullYear(),g.getMonth(),g.getDate()-k,8).getTime()/1000),x=pushDue();return [7,1,0].every(k=>x.includes(at(k)))&&!x.includes(at(30))})()"))
  ck('alertes à 08h00 locales',pg.evaluate("pushDue().every(t=>new Date(t*1000).getHours()==8&&new Date(t*1000).getMinutes()==0)"))
  # envoi au serveur (rpc simulé) : ce qui part sur le réseau
  r=pg.evaluate("""async()=>{SY={code:'AAAAAAAAAAAAAAAAAAAAAAAA',ver:0};window.__c=[];window.syKeys=async()=>({id:'a'.repeat(64),auth:'b'.repeat(64)});
    window.rpc=async(fn,a)=>{window.__c.push([fn,a]);return 'ok'};
    await pushSend({endpoint:'https://push.example/abc',toJSON(){return{endpoint:'https://push.example/abc',keys:{p256dh:'k',auth:'a'}}}});
    return JSON.stringify(window.__c)}""")
  ck('envoi : fonction ptua_push_set avec adresse, clés d’abonnement et instants seulement',json.loads(r)[0][0]=='ptua_push_set' and set(json.loads(r)[0][1])=={'p_id','p_auth','p_endpoint','p_sub','p_due'})
  ck('envoi : aucune donnée de marché dans la requête',not any(w in r for w in ['ACME','SECRET','123456','Responsabilité','M-1']))
  ck('envoi réussi : mémorisation locale',pg.evaluate("!!localStorage.getItem('ptua_push')"))
  pg.evaluate("localStorage.removeItem('ptua_push')")
  ref=pg.evaluate("""async()=>{window.rpc=async()=>'limite';try{await pushSend({endpoint:'https://p/x',toJSON(){return{endpoint:'https://p/x',keys:{p256dh:'k',auth:'a'}}}});return 'pas d erreur'}catch(e){return e.message}}""")
  ck('refus du serveur (limite) : message clair et rien mémorisé',('5' in ref) and pg.evaluate("!localStorage.getItem('ptua_push')"))

  # service worker : gestionnaires push et clic
  js=open('sw.js',encoding='utf-8').read()
  test="""
const L={};const shown=[];const clicked=[];
global.self={addEventListener:(k,f)=>{L[k]=f},registration:{showNotification:(t,o)=>{shown.push([t,o]);return Promise.resolve()}},clients:{matchAll:()=>Promise.resolve([]),openWindow:u=>{clicked.push(u);return Promise.resolve()},claim(){}},skipWaiting(){} };
global.location={origin:'https://x'};global.caches={};global.fetch=()=>{};
eval(%s);
let w=[];const ev=(d)=>({data:d,waitUntil:p=>w.push(p)});
L.push(ev({json:()=>({t:'PTUA',b:'Des échéances demandent votre attention.'})}));
L.push(ev({json:()=>{throw new Error('x')}}));
L.push(ev(null));
L.notificationclick({notification:{close(){}},waitUntil:p=>w.push(p)});
Promise.all(w).then(()=>console.log(JSON.stringify({n:shown.length,t:shown[0][0],b:shown[0][1].body,b2:shown[1][1].body,tag:shown[0][1].tag,open:clicked})));
"""%json.dumps(js)
  out=subprocess.run(['node','-e',test],capture_output=True,text=True)
  P(out.stdout.strip() or out.stderr[:300])
  try:o=json.loads(out.stdout.strip().splitlines()[-1])
  except Exception:o={}
  ck('service worker : 3 notifications affichées même sans charge lisible (exigence iOS)',o.get('n')==3 and o.get('t')=='PTUA')
  ck('service worker : texte générique, sans donnée de marché',o.get('b','')=='Des échéances demandent votre attention.' and o.get('b2','')==o.get('b'))
  ck('service worker : un clic ouvre l’application',o.get('open')==['./'])
  ck('aucune erreur JavaScript',not errs)
  if errs:P(errs[:5])
  b.close()
P('ÉCHECS :',bad)
raise SystemExit(1 if bad else 0)
