# v9.2 — onglet Assistant sécurité (agent IA) : accès par clé de synchro, rien d'enregistré, effacement au verrouillage
import json,hashlib
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
DB={};errs=[];AG=[];MODE={'m':'ok'}
def handle(route):
  req=route.request;a=json.loads(req.post_data or '{}')
  if '/functions/v1/agent-cyber' in req.url:
    AG.append(a);row=DB.get(a.get('id'));ok=row and row['h']==hashlib.sha256(a.get('auth','').encode()).hexdigest()
    if not ok:return route.fulfill(status=401,content_type='application/json',body='{"error":"Accès refusé"}')
    if MODE['m']=='quota':return route.fulfill(status=429,content_type='application/json',body='{"error":"Quota gratuit atteint, réessayez dans une minute"}')
    if MODE['m']=='down':return route.abort()
    return route.fulfill(status=200,content_type='application/json',body=json.dumps({'reply':'Réponse <img src=x onerror="window.__x=1"> test','tools_used':['analyze_url','analyze_url']}))
  fn=req.url.split('/rpc/')[1]
  h=hashlib.sha256(a.get('p_auth','').encode()).hexdigest();row=DB.get(a['p_id']);ok=row and row['h']==h
  if fn=='ptua_get':out=[{'ver':row['ver'],'blob':row['blob']}] if ok else []
  elif fn=='ptua_put' and a['p_ver']==0:
    out=-1 if row else 1
    if not row: DB[a['p_id']]={'h':h,'ver':1,'blob':a['p_blob']}
  elif fn=='ptua_put' and ok and row['ver']==a['p_ver']: row['ver']+=1;row['blob']=a['p_blob'];out=row['ver']
  elif fn=='ptua_put': out=-1
  else: out=[]
  route.fulfill(status=200,content_type='application/json',body=json.dumps(out))
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  c=b.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True);pg=c.new_page();pg.set_default_timeout(8000)
  pg.route('https://iofbwpzhptctyelmylkz.supabase.co/**',handle);pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and 'Failed to load resource' not in m.text and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2300)
  P('version et en-tête identiques :',pg.evaluate("APPV"),pg.evaluate("document.querySelector('h1 small').textContent=='v'+APPV"),'| onglet dans la liste :',pg.evaluate("NAV.some(n=>n[0]=='cyber')"),'| icône SVG :',pg.evaluate("!!ic('cyber')"))
  pg.evaluate("go('cyber')");pg.wait_for_timeout(300)
  P('sans synchro : message + pas de saisie :',pg.evaluate("$('#v').textContent.includes('Synchronisation requise')&&!$('#cyi')"))
  pg.evaluate("db.marches.push({id:'m1',titulaire:'SOGEA SATOM',num:'2024-0153',montant:'850000000'});save()")
  pg.evaluate("setTimeout(syStart,0)");pg.wait_for_timeout(600);pg.fill('#cd input[name=a]','Test#Motdepasse2026');pg.fill('#cd input[name=b]','Test#Motdepasse2026');pg.click('#cd .pri');pg.wait_for_timeout(3000)
  pg.click('#cd button[data-i="0"]');pg.wait_for_timeout(4000);pg.evaluate("$('#cd').open&&$('#cd').close()")
  P('synchro active :',pg.evaluate("!!(SY&&SY.code)"))
  pg.evaluate("go('cyber')");pg.wait_for_timeout(300)
  P('zone de saisie + avertissement :',pg.evaluate("!!$('#cyi')&&$('#v').textContent.includes('aucune donnée de PTUA')"))
  pg.fill('#cyi','Ce lien est-il sûr ? http://exemple.xyz');pg.click('#cys');pg.wait_for_timeout(1200)
  P('réponse affichée :',pg.evaluate("[...document.querySelectorAll('.cym')].map(e=>e.className.slice(4)+':'+e.textContent).slice(-2)"))
  P('XSS neutralisé :',pg.evaluate("!window.__x&&!document.querySelector('.cym img')"))
  a=AG[-1];P('envoi : identifiants 64 hex :',len(a['id'])==64 and len(a['auth'])==64,'| aucune donnée PTUA :','SOGEA' not in json.dumps(a),'| champs :',sorted(a.keys()))
  pg.fill('#cyi','Et pour mon téléphone ?');pg.click('#cys');pg.wait_for_timeout(1200)
  P('historique transmis :',[m['role'] for m in AG[-1]['history']])
  MODE['m']='quota';pg.fill('#cyi','encore');pg.click('#cys');pg.wait_for_timeout(1000)
  P('quota affiché :',pg.evaluate("[...document.querySelectorAll('.cym')].pop().textContent"))
  MODE['m']='down';pg.fill('#cyi','encore 2');pg.click('#cys');pg.wait_for_timeout(1000)
  P('panne affichée :',pg.evaluate("[...document.querySelectorAll('.cym')].pop().textContent"),'| bouton réactivé :',pg.evaluate("!$('#cys').disabled"))
  MODE['m']='ok';pg.fill('#cyi','suite');pg.click('#cys');pg.wait_for_timeout(1000)
  P('erreurs exclues de l’historique :',all('⚠️' not in m['content'] for m in AG[-1]['history']))
  P('rien enregistré (stockage local, journal) :',pg.evaluate("!Object.values(localStorage).some(v=>v.includes('exemple.xyz'))&&!JSON.stringify(db).includes('exemple.xyz')"),'| rien dans la synchro :',all('exemple' not in r['blob'] for r in DB.values()))
  pg.evaluate("go('dash')");pg.evaluate("go('cyber')");pg.wait_for_timeout(300)
  P('conversation conservée en changeant d’onglet :',pg.evaluate("document.querySelectorAll('.cym').length")>4)
  pg.evaluate("lock()");pg.wait_for_timeout(700)
  P('verrouillage : conversation effacée :',pg.evaluate("CYM.length===0&&!document.body.innerText.includes('exemple.xyz')"))
  pg.fill('#pin','Test#Motdepasse2026');pg.evaluate("setTimeout(unl,0)");pg.wait_for_timeout(2000);pg.evaluate("go('cyber')");pg.wait_for_timeout(300)
  P('après déverrouillage : vide et utilisable :',pg.evaluate("document.querySelectorAll('.cym').length===1&&!!$('#cyi')"))
  pg.evaluate("go('act')");pg.wait_for_timeout(1500)
  P('activité : serveur attendu, pas d’alerte :',pg.evaluate("!$('#v').textContent.includes('inattendu')"))
  pg.evaluate("document.documentElement.dataset.t='dark';go('cyber')");pg.wait_for_timeout(300)
  P('thème sombre sans erreur')
  P('erreurs :',errs)
  b.close()
