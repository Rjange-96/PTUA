# v9.7 — Jauge de progression en arrière-plan : l'application reste utilisable pendant la compression et l'envoi au cloud.
# Prérequis : python3 tests/t28_gen.py
import json,hashlib
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
DB={};FILES={};errs=[];alerts=[];D='/tmp/claude-0/pdf'
H=lambda x:hashlib.sha256(x.encode()).hexdigest()
def handle(route):
  req=route.request;fn=req.url.split('/rpc/')[1];a=json.loads(req.post_data or '{}');row=DB.get(a.get('p_id'));ok=bool(row and row['h']==H(a.get('p_auth','')))
  if fn=='ptua_get':out=[{'ver':row['ver'],'blob':row['blob'],'updated_at':''}] if ok else []
  elif fn=='ptua_put':
    if a['p_ver']==0:
      out=-1 if row else 1
      if not row:DB[a['p_id']]={'h':H(a['p_auth']),'ver':1,'blob':a['p_blob']}
    elif ok and row['ver']==a['p_ver']:row['ver']+=1;row['blob']=a['p_blob'];out=row['ver']
    else:out=-1
  elif fn=='ptua_file_put':
    if not ok:return route.fulfill(status=400,body='{}')
    FILES[(a['p_id'],a['p_fid'])]=a['p_blob'];out=True
  elif fn=='ptua_file_get':out=FILES.get((a['p_id'],a['p_fid'])) if ok else None
  elif fn=='ptua_file_del':out=ok
  else:out=[]
  route.fulfill(status=200,content_type='application/json',body=json.dumps(out))
with sync_playwright() as p:
  b=p.chromium.launch(executable_path=__import__('shutil').which('google-chrome'));pg=b.new_page(viewport={'width':1280,'height':850});pg.set_default_timeout(15000)
  pg.route('https://iofbwpzhptctyelmylkz.supabase.co/**',handle)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:(alerts.append(d.message[:80]),d.accept()))
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2300)
  pg.evaluate("db.marches.push({id:'m1',num:'M-1',titulaire:'T'},{id:'m2',num:'M-2'});save()")
  pg.evaluate("setTimeout(pinMenu,0)");pg.wait_for_timeout(300);pg.fill('#cd input[name=a]','Test#Jauge2026!');pg.fill('#cd input[name=b]','Test#Jauge2026!');pg.click('#cd .pri');pg.wait_for_timeout(2500)
  pg.evaluate("setTimeout(syStart,0)");pg.wait_for_timeout(300);pg.click('#cd .pri');pg.wait_for_timeout(2500);pg.click('#cd .pri');pg.wait_for_timeout(500)
  alerts.clear()
  # 1) gros PDF : aucune fenêtre bloquante, jauge visible et qui avance
  pg.evaluate("go('marches');edit('marches','m1')");pg.wait_for_timeout(300);pg.set_input_files('#fa',D+'/b700.pdf');pg.click('#dlg .pri');pg.wait_for_timeout(2500)
  v1=pg.evaluate("+$('#job [role=progressbar]').getAttribute('aria-valuenow')")
  P('aucune fenêtre bloquante :',pg.evaluate("!$('#cd').open&&!$('#dlg').open"),'| jauge visible :',pg.evaluate("!$('#job').hidden"))
  pg.wait_for_timeout(2500);v2=pg.evaluate("+$('#job [role=progressbar]').getAttribute('aria-valuenow')")
  P('la jauge avance :',v2>v1,f'({v1} % → {v2} %) | texte :',pg.evaluate("$('#job .jd').textContent")[:90])
  P('pourcentage dans le titre de l’onglet :',pg.title()[:40])
  # 2) on continue à travailler pendant ce temps
  pg.evaluate("go('garanties')");pg.wait_for_timeout(200);pg.evaluate("go('marches');edit('marches')");pg.wait_for_timeout(300);pg.fill('#df input[name=num]','M-PENDANT');pg.click('#dlg .pri');pg.wait_for_timeout(300)
  P('fiche créée pendant la compression :',pg.evaluate("db.marches.some(m=>m.num=='M-PENDANT')"),'| jauge toujours là :',pg.evaluate("!$('#job').hidden"))
  # 3) file d'attente : un 2e envoi pendant le 1er
  pg.evaluate("edit('marches','m2')");pg.wait_for_timeout(300);pg.set_input_files('#fa',D+'/scan15.pdf');pg.click('#dlg .pri');pg.wait_for_timeout(600)
  P('2e envoi mis en attente :',pg.evaluate("/en attente/.test($('#job').textContent)"))
  # 4) réduire / agrandir
  pg.click('#job [data-j=m]');pg.wait_for_timeout(300);P('jauge réduite :',pg.evaluate("$('#job').classList.contains('min')&&/%/.test($('#job').textContent)"))
  pg.click('#job [data-j=o]');pg.wait_for_timeout(300);P('jauge agrandie :',pg.evaluate("!$('#job').classList.contains('min')"))
  # 5) protection contre la fermeture accidentelle
  P('avertissement si on ferme pendant le travail :',pg.evaluate("(()=>{const e=new Event('beforeunload',{cancelable:true});dispatchEvent(e);return e.defaultPrevented})()"))
  # 6) fin : envoi au cloud visible, message non bloquant
  cloud=False
  for _ in range(400):
    pg.wait_for_timeout(500)
    if pg.evaluate("!!JOB.cloud"):cloud=True
    if not pg.evaluate("JOB.run")and not pg.evaluate("!!JOB.cloud")and pg.evaluate("!fBusy"):break
  P('jauge d’envoi au cloud affichée :',cloud,'| documents envoyés :',len(FILES))
  P('message final dans la jauge :',pg.evaluate("$('#job').textContent.replace(/\\s+/g,' ')")[:260])
  P('aucune fenêtre d’alerte pendant tout le traitement :',alerts==[],alerts[:2])
  P('fichiers : M-1',pg.evaluate("db.marches.find(m=>m.id=='m1').files.length"),'parties | M-2',pg.evaluate("db.marches.find(m=>m.id=='m2').files.length"))
  pg.click('#job [data-j=v]');pg.wait_for_timeout(400);P('« Voir les documents » ouvre la liste :',pg.evaluate("$('#cd').open&&!!$('#cd #ff')"))
  pg.evaluate("$('#cd').close()")
  # 7) envoi depuis la fenêtre Documents : elle reste ouverte et se met à jour
  pg.evaluate("docs('marches','m2')");pg.wait_for_timeout(300);n0=pg.evaluate("$('#cd').querySelectorAll('.di').length");pg.set_input_files('#ff',D+'/a12.pdf');pg.wait_for_timeout(500)
  P('fenêtre Documents toujours ouverte pendant le traitement :',pg.evaluate("$('#cd').open"))
  for _ in range(120):
    pg.wait_for_timeout(500)
    if not pg.evaluate("JOB.run"):break
  pg.wait_for_timeout(500);P('liste mise à jour automatiquement :',pg.evaluate("$('#cd').querySelectorAll('.di').length")>n0)
  pg.evaluate("$('#cd').close()")
  # 8) verrouillage pendant un traitement : arrêt immédiat, rien d'affiché, aucun fichier orphelin
  nb=pg.evaluate("db.marches.find(m=>m.id=='m2').files.length")
  pg.evaluate("edit('marches','m2')");pg.wait_for_timeout(300);pg.set_input_files('#fa',D+'/b700.pdf');pg.click('#dlg .pri');pg.wait_for_timeout(2500)
  pg.evaluate("lock()");pg.wait_for_timeout(3000)
  P('verrouillage : jauge masquée et vidée :',pg.evaluate("$('#job').hidden&&$('#job').innerHTML==''"),'| traitement arrêté :',pg.evaluate("!JOB.run"))
  pg.fill('#pin','Test#Jauge2026!');pg.evaluate("setTimeout(unl,0)");pg.wait_for_timeout(3500)
  na=pg.evaluate("db.marches.find(m=>m.id=='m2').files.length")
  orph=pg.evaluate("""(async()=>{const d=await idb();const keys=await new Promise(r=>{const q=d.transaction('f').objectStore('f').getAllKeys();q.onsuccess=()=>r(q.result)});const ref=new Set(allF().map(f=>f.id));return keys.filter(k=>!ref.has(k)).length})()""")
  P('après déverrouillage : fiches intactes :',na>=nb,f'({nb} → {na}) | fichiers orphelins :',orph)
  P('erreurs :',[e for e in errs if 'status of 400' not in e][:5]);b.close()
