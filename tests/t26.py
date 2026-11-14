import sys,shutil,subprocess,time,os,re
from playwright.sync_api import sync_playwright
src=sys.argv[1] if len(sys.argv)>1 else '.';D='/tmp/ptua_srv_t26';shutil.rmtree(D,ignore_errors=True);shutil.copytree(src,D,ignore=shutil.ignore_patterns('.git','tests'))
srv=subprocess.Popen(['python3','-m','http.server','8766'],cwd=D,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');ctx=b.new_context();pg=ctx.new_page();pg.on('dialog',lambda d:d.accept())
  errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8766/');pg.evaluate("navigator.serviceWorker.ready.then(()=>new Promise(r=>navigator.serviceWorker.controller?r():navigator.serviceWorker.addEventListener('controllerchange',r)))");pg.wait_for_timeout(1500)
  print('caches initiaux :',pg.evaluate("caches.keys()"))
  # une autre application du même domaine crée son cache
  pg.evaluate("caches.open('residence-v3').then(c=>c.put('/autre-app/x',new Response('x')))")
  # publication d'une nouvelle version de PTUA
  s=open(D+'/sw.js').read();s=re.sub(r"const V='[\d.]+'","const V='99.0'",s);open(D+'/sw.js','w').write(s)
  pg.evaluate("navigator.serviceWorker.getRegistration().then(r=>r.update())");pg.wait_for_timeout(2500)
  pg.evaluate("navigator.serviceWorker.getRegistration().then(r=>r.waiting&&r.waiting.postMessage('skip'))");pg.wait_for_timeout(2500)
  k=pg.evaluate("caches.keys()");print('après mise à jour :',k,'| cache de l’autre app conservé :','residence-v3' in k)
  # l'autre application efface le cache de PTUA (comme residence/sw.js)
  pg.evaluate("caches.keys().then(ks=>Promise.all(ks.filter(x=>x!=='residence-v3').map(x=>caches.delete(x))))")
  pg.reload();pg.wait_for_timeout(3000)
  ok=pg.evaluate("caches.match('./lib/pdf.worker.min.mjs',{ignoreSearch:true}).then(x=>!!x)");print('cache PTUA reconstitué après effacement :',ok)
  ctx.set_offline(True);
  try:pg.reload();pg.wait_for_timeout(1500);print('ouverture hors ligne :',pg.evaluate("typeof APPV=='string'"))
  except Exception as e:print('ouverture hors ligne : False',str(e)[:80])
  print('erreurs :',errs);b.close()
finally: srv.kill()
