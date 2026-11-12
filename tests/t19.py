import json,hashlib
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
DB={};errs=[];alerts=[]
def handle(route):
  req=route.request;fn=req.url.split('/rpc/')[1];a=json.loads(req.post_data or '{}')
  h=hashlib.sha256(a.get('p_auth','').encode()).hexdigest();row=DB.get(a['p_id']);ok=row and row['h']==h
  if fn=='ptua_get':out=[{'ver':row['ver'],'blob':row['blob'],'updated_at':'2026-11-12T19:00:00Z'}] if ok else []
  elif a.get('p_ver')==0:
    out=-1 if row else 1
    if not row: DB[a['p_id']]={'h':h,'ver':1,'blob':a['p_blob']}
  elif ok and row['ver']==a.get('p_ver'): row['ver']+=1;row['blob']=a['p_blob'];out=row['ver']
  else: out=True
  route.fulfill(status=200,content_type='application/json',body=json.dumps(out))
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  c=b.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True);pg=c.new_page();pg.set_default_timeout(15000)
  pg.route('https://iofbwpzhptctyelmylkz.supabase.co/**',handle);pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:(alerts.append(d.message[:80]),d.accept()))
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500)
  pg.evaluate("setTimeout(syStart,0)");pg.wait_for_timeout(600);pg.fill('#cd input[name=a]','Test#Motdepasse2026');pg.fill('#cd input[name=b]','Test#Motdepasse2026');pg.click('#cd .pri');pg.wait_for_timeout(3000)
  pg.click('#cd button[data-i="0"]');pg.wait_for_timeout(3500);pg.click('#cd .pri');pg.wait_for_timeout(500)
  pg.evaluate("db.marches.push({id:'m1',titulaire:'SECRET-TITULAIRE-XYZ',num:'2024-0153'});save()");pg.wait_for_timeout(3500)
  pg.evaluate("go('act')");pg.wait_for_timeout(1800)
  t=pg.evaluate("$('#actb').innerText")
  P('onglet présent :',pg.evaluate("!!$('#actb')"),'| requêtes listées :',pg.evaluate("document.querySelectorAll('#actb tr').length-1"))
  P('ptua_get visible :','rpc/ptua_get' in t,'| ptua_put visible :','rpc/ptua_put' in t)
  P('contenu des données absent :','SECRET-TITULAIRE' not in t and 'p_blob' not in t and 'Ptua#Abidjan' not in t)
  P('serveurs ✅ :',pg.evaluate("Object.keys(MON.hosts)"),'| alerte inattendu :','inattendu' in t)
  n0=pg.evaluate("MON.net.length");pg.wait_for_timeout(50000);P('mise à jour en direct (+requêtes en 50 s) :',pg.evaluate("MON.net.length")-n0,'| rythme :',pg.evaluate("$('#actb').innerText.match(/toutes les \\d+ s/)?.[0]"))
  pg.screenshot(path='/tmp/g1.png',full_page=True)
  # serveur inattendu
  pg.evaluate("fetch('https://evil.example.com/x').catch(()=>{})");pg.wait_for_timeout(1500);P('alerte serveur inattendu :','evil.example.com' in pg.evaluate("$('#actb').innerText"))
  # injection via chemin
  pg.evaluate("MON.net.push({at:Date.now(),m:'GET',host:'<img src=x onerror=window.__x=1>',path:'<script>',bl:0,st:200,ms:1,rl:0});MON.hosts['<img src=x onerror=window.__x=1>']=1");pg.wait_for_timeout(1500);P('injection neutralisée :',pg.evaluate("window.__x===undefined"))
  pg.evaluate("lock()");pg.wait_for_timeout(500);P('verrouillage visible dans événements :',pg.evaluate("MON.ev.some(e=>e.k=='lock')"))
  pg.fill('#pin','faux');pg.press('#pin','Enter');pg.wait_for_timeout(1500);P('échec code journalisé :',pg.evaluate("MON.ev.some(e=>e.k=='echec')"))
  P('erreurs :',[e for e in errs if 'evil' not in e and 'ERR_' not in e])
  b.close()
