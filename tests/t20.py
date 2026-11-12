import json
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[]
mode=['ok']
def h(route):
  if mode[0]=='ok':route.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body='{"status":"ok","protocol":"DOH","profile":"abc123","srcIP":"1.2.3.4"}')
  elif mode[0]=='un':route.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body='{"status":"unconfigured"}')
  elif mode[0]=='evil':route.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body='{"status":"<img src=x onerror=window.__x=1>"}')
  else:route.abort()
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');c=b.new_context(viewport={'width':393,'height':852},is_mobile=True);pg=c.new_page();pg.set_default_timeout(15000)
  pg.route('https://test.nextdns.io/**',h);pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and 'ERR_FAILED' not in m.text and 'Failed to load' not in m.text and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500);pg.evaluate("go('act')");pg.wait_for_timeout(1500)
  P('carte présente :',pg.evaluate("document.body.innerText.includes('Surveiller tout l’iPhone')"))
  for m,exp in [('ok','actif'),('un','pas actif'),('evil','pas actif'),('ko','illisible')]:
    mode[0]=m;pg.click('text=Vérifier NextDNS');pg.wait_for_timeout(1500);t=pg.evaluate("$('#dnsr').textContent");P(m,'->',t[:90],'| attendu',exp in t)
  P('XSS neutralisé :',pg.evaluate("window.__x===undefined"),'| IP/identifiant jamais affichés :',pg.evaluate("!document.body.innerText.includes('1.2.3.4')&&!document.body.innerText.includes('abc123')"))
  P('CSP autorise test.nextdns.io :',pg.evaluate("document.querySelector('meta[http-equiv=Content-Security-Policy]').content.includes('test.nextdns.io')"))
  mode[0]='ok';pg.evaluate("setTimeout(diag,0)");pg.wait_for_timeout(9000);P('diag DNS :',pg.evaluate("[...document.querySelectorAll('#cd .dl p')].filter(p=>p.textContent.includes('DNS')).map(p=>p.textContent)"))
  pg.evaluate("$('#cd').close();go('act')");pg.wait_for_timeout(800);pg.screenshot(path='/tmp/h1.png',full_page=True)
  P('erreurs :',errs);b.close()
