from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[];alerts=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  c=b.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True);pg=c.new_page();pg.set_default_timeout(15000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:(alerts.append(d.message[:100]),d.accept()))
  cd=c.new_cdp_session(pg);cd.send('WebAuthn.enable')
  try:
    cd.send('WebAuthn.addVirtualAuthenticator',{'options':{'protocol':'ctap2','ctap2Version':'ctap2_1','transport':'internal','hasResidentKey':True,'hasUserVerification':True,'isUserVerified':True,'automaticPresenceSimulation':True,'hasPrf':True}});P('authenticator virtuel PRF : ok')
  except Exception as e:P('PRF virtuel indisponible :',str(e)[:150]);raise
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500)
  P('bouton Face ID caché avant activation :',pg.evaluate("$('#fb').hidden"))
  pg.evaluate("setTimeout(pinMenu,0)");pg.wait_for_timeout(500);pg.fill('#cd input[name=a]','Test#Motdepasse2026');pg.fill('#cd input[name=b]','Test#Motdepasse2026');pg.click('#cd .pri');pg.wait_for_timeout(3000)
  pg.evaluate("db.marches.push({id:'m1',titulaire:'SOGEA',num:'2024-0153'});save()");pg.wait_for_timeout(500)
  pg.evaluate("go('sauv')");pg.wait_for_timeout(600);P('bouton carte :',pg.evaluate("[...document.querySelectorAll('button')].some(b=>b.textContent.includes('Activer Face ID'))"))
  pg.evaluate("setTimeout(fidMenu,0)");pg.wait_for_timeout(600);pg.fill('#cd input[name=c]','mauvais');pg.click('#cd .pri');pg.wait_for_timeout(1500)
  P('mauvais code refusé, rien stocké :',any('incorrect' in a for a in alerts),pg.evaluate("!localStorage.getItem('ptua_fid')"))
  pg.evaluate("setTimeout(fidMenu,0)");pg.wait_for_timeout(600);pg.fill('#cd input[name=c]','Test#Motdepasse2026');pg.click('#cd .pri');pg.wait_for_timeout(3500)
  st=pg.evaluate("localStorage.getItem('ptua_fid')")
  P('Face ID activé :',[a for a in alerts if 'Face ID' in a][-1:],'| stocké :',bool(st),'| code en clair dans le stockage ?','Test#Motdepasse2026' in (st or '') or 'Test#Motdepasse2026' in pg.evaluate("JSON.stringify(Object.entries(localStorage))"))
  pg.evaluate("lock()");pg.wait_for_timeout(800);P('verrouillé, bouton visible :',pg.evaluate("!$('#lk').hidden&&!$('#fb').hidden"),'| données vidées :',pg.evaluate("db.marches.length==0"))
  pg.screenshot(path='/tmp/f1.png')
  pg.click('#fb');pg.wait_for_timeout(3500)
  P('déverrouillé par Face ID :',pg.evaluate("$('#lk').hidden"),'| données :',pg.evaluate("db.marches.map(m=>m.titulaire)"))
  # rechargement complet de la page
  pg.reload();pg.wait_for_timeout(2500);P('après rechargement : bouton visible',pg.evaluate("!$('#fb').hidden"));pg.click('#fb');pg.wait_for_timeout(3500);P('  déverrouillé :',pg.evaluate("$('#lk').hidden"))
  # code toujours valable
  pg.evaluate("lock()");pg.wait_for_timeout(600);pg.fill('#pin','Test#Motdepasse2026');pg.press('#pin','Enter');pg.wait_for_timeout(3000);P('code classique toujours OK :',pg.evaluate("$('#lk').hidden"))
  # changement de code -> Face ID retiré
  pg.evaluate("setTimeout(pinMenu,0)");pg.wait_for_timeout(500);pg.click('#cd button[data-i="1"]');pg.wait_for_timeout(500)
  pg.fill('#cd input[name=c]','Test#Motdepasse2026');pg.fill('#cd input[name=n]','Test#Nouveau2026a');pg.fill('#cd input[name=n2]','Test#Nouveau2026a');pg.click('#cd .pri');pg.wait_for_timeout(3500)
  P('changement de code : Face ID retiré :',pg.evaluate("!localStorage.getItem('ptua_fid')"))
  pg.evaluate("lock()");pg.wait_for_timeout(500);P('bouton masqué après retrait :',pg.evaluate("$('#fb').hidden"))
  # stockage altéré -> repli propre
  pg.fill('#pin','Test#Nouveau2026a');pg.press('#pin','Enter');pg.wait_for_timeout(3000)
  pg.evaluate("setTimeout(fidMenu,0)");pg.wait_for_timeout(600);pg.fill('#cd input[name=c]','Test#Nouveau2026a');pg.click('#cd .pri');pg.wait_for_timeout(3500)
  pg.evaluate("(()=>{const o=JSON.parse(localStorage.getItem('ptua_fid'));o.ct=o.ct.slice(0,-8)+'AAAAAAAA';localStorage.setItem('ptua_fid',JSON.stringify(o))})()")
  pg.evaluate("lock()");pg.wait_for_timeout(600);pg.click('#fb');pg.wait_for_timeout(2500)
  P('stockage corrompu : message :',pg.evaluate("$('#lke').textContent"),'| Face ID retiré :',pg.evaluate("!localStorage.getItem('ptua_fid')"))
  pg.fill('#pin','Test#Nouveau2026a');pg.press('#pin','Enter');pg.wait_for_timeout(3000);P('  code OK ensuite :',pg.evaluate("$('#lk').hidden"))
  # désactivation
  pg.evaluate("setTimeout(fidMenu,0)");pg.wait_for_timeout(600);pg.fill('#cd input[name=c]','Test#Nouveau2026a');pg.click('#cd .pri');pg.wait_for_timeout(3500)
  pg.evaluate("setTimeout(fidMenu,0)");pg.wait_for_timeout(600);pg.click('#cd button[data-i="0"]');pg.wait_for_timeout(800);P('désactivation :',pg.evaluate("!localStorage.getItem('ptua_fid')"))
  # sans support (navigateur sans WebAuthn)
  c2=b.new_context();p2=c2.new_page();p2.add_init_script("delete window.PublicKeyCredential");p2.goto('http://localhost:8765/');p2.wait_for_timeout(2000);P('sans WebAuthn : fidOk =',p2.evaluate("fidOk()"))
  P('erreurs :',errs);b.close()
