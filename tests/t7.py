from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[];msgs=[];mode={'accept':True}
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  pg=b.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True).new_page();pg.set_default_timeout(6000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
  def h(d):
    msgs.append(d.message[:60]);d.accept() if (mode['accept'] or d.type=='alert') else d.dismiss()
  pg.on('dialog',h)
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2300);pg.evaluate("localStorage.clear()");pg.reload();pg.wait_for_timeout(2300)
  pg.evaluate("db.marches.push({id:'m1',titulaire:'SOGEA',num:'2024-0153',montant:'1000'});save()")
  mode['accept']=False
  pg.evaluate("setTimeout(pinMenu,0)");pg.wait_for_timeout(300);pg.fill('#cd input[name=a]','12345678');pg.fill('#cd input[name=b]','12345678');pg.click('#cd .pri');pg.wait_for_timeout(1500)
  P('weak refused:',pg.evaluate("ENC===false"))
  mode['accept']=True
  pg.evaluate("setTimeout(pinMenu,0)");pg.wait_for_timeout(300);pg.fill('#cd input[name=a]','Test#Motdepasse2026');pg.fill('#cd input[name=b]','Test#Motdepasse2026');pg.click('#cd .pri');pg.wait_for_timeout(3000)
  P('strong enabled:',pg.evaluate("ENC&&!Object.values(localStorage).some(v=>v.includes('SOGEA'))"))
  pg.reload();pg.wait_for_timeout(2300)
  for i in range(5):
    pg.fill('#pin','mauvais'+str(i));pg.evaluate("setTimeout(unl,0)");pg.wait_for_timeout(1300)
  P('after 5 wrong:',pg.evaluate("$('#lke').textContent"))
  pg.fill('#pin','Test#Motdepasse2026');pg.evaluate("setTimeout(unl,0)");pg.wait_for_timeout(1500)
  P('blocked even with right code:',pg.evaluate("!$('#lk').hidden"),pg.evaluate("$('#lke').textContent"))
  pg.evaluate("localStorage.removeItem('ptua_until')")
  pg.fill('#pin','Test#Motdepasse2026');pg.evaluate("setTimeout(unl,0)");pg.wait_for_timeout(1800)
  P('unlocked after wait:',pg.evaluate("$('#lk').hidden&&db.marches[0].titulaire"))
  pg.evaluate("edit('marches','m1')");pg.wait_for_timeout(200);pg.evaluate("lock()");pg.wait_for_timeout(600)
  P('DOM wiped on lock:',pg.evaluate("!document.body.innerText.includes('SOGEA')&&$('#df').innerHTML===''"))
  pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
  P('CSP present:',pg.evaluate("!!document.querySelector('meta[http-equiv=Content-Security-Policy]')"))
  P('dialogs:',msgs);P('errors:',errs)
  b.close()
