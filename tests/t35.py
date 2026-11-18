# v9.14 — fonds d'écran animés (Ninja, Pirate), fond personnel (photo de l'utilisateur), mode « admirer le décor », animations coupables
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  c=b.new_context(viewport={'width':1280,'height':800});pg=c.new_page();pg.set_default_timeout(15000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500);pg.evaluate("localStorage.clear();thSet('clair')")
  P('thème clair : pas de décor :',pg.evaluate("getComputedStyle($('#wp')).display")=='none')
  pg.evaluate("thSet('ninja')");pg.wait_for_timeout(300)
  P('ninja : décor affiché :',pg.evaluate("getComputedStyle($('#wp')).display")=='block' and pg.evaluate("$('#wp').classList.contains('ninja')"))
  P('ninja : feuilles, brume, shurikens :',pg.evaluate("$('#wp').querySelectorAll('.wl').length>=8 && $('#wp').querySelectorAll('.wpm').length==2 && $('#wp').querySelectorAll('.wsh').length==2"))
  P('ninja : animations actives :',pg.evaluate("getComputedStyle($('#wp .wl')).animationName")=='wfall' and pg.evaluate("getComputedStyle($('#wp .wpm')).animationName")=='wdrift')
  P('ninja : décor derrière le contenu :',pg.evaluate("getComputedStyle($('#wp')).zIndex")=='-1' and pg.evaluate("getComputedStyle($('#wp')).pointerEvents")=='none')
  pg.evaluate("thSet('pirate')");pg.wait_for_timeout(300)
  P('pirate : navire, vagues, mouettes :',pg.evaluate("!!$('#wp .wsh2') && $('#wp').querySelectorAll('.wvw').length==3 && $('#wp').querySelectorAll('.wgl').length>=2 && !!$('#wp .wpc')"))
  P('pirate : navire tangue :',pg.evaluate("getComputedStyle($('#wp .wsh2')).animationName")=='wbob')
  P('pirate : décor ninja retiré :',pg.evaluate("!$('#wp .wl')"))
  # menu des thèmes
  pg.click('#th');pg.wait_for_timeout(300);o=pg.evaluate("[...$('#cd').querySelectorAll('button')].map(b=>b.textContent)");[P('  menu :',x) for x in o]
  P('menu : 4 thèmes + options :',len(o)>=8 and 'Mon fond d’écran' in o[5] or any('Mon fond d’écran' in x for x in o))
  P('menu : admirer le décor présent :',any('Admirer le décor' in x for x in o))
  pg.click('#cd button[data-i="-1"]')
  # mode admirer
  pg.evaluate("wpPeek()");pg.wait_for_timeout(300)
  P('admirer : application masquée :',pg.evaluate("getComputedStyle($('header')).visibility")=='hidden' and pg.evaluate("getComputedStyle($('#wp')).visibility")!='hidden')
  pg.wait_for_timeout(700);pg.mouse.click(600,400);pg.wait_for_timeout(300)
  P('admirer : un toucher ramène l’application :',pg.evaluate("getComputedStyle($('header')).visibility")=='visible' and pg.evaluate("!document.documentElement.classList.contains('peek')"))
  # couper les animations
  pg.evaluate("wpToggle()");pg.wait_for_timeout(200)
  P('animations coupées :',pg.evaluate("getComputedStyle($('#wp .wsh2')).animationName")=='none' and pg.evaluate("localStorage.getItem('ptua_wpanim')")=='0')
  pg.reload();pg.wait_for_timeout(2300);P('coupure mémorisée après redémarrage :',pg.evaluate("getComputedStyle($('#wp .wsh2')).animationName")=='none')
  pg.evaluate("wpToggle()");pg.wait_for_timeout(200);P('animations réactivées :',pg.evaluate("getComputedStyle($('#wp .wsh2')).animationName")=='wbob')
  # mouvement réduit du système
  pg.emulate_media(reduced_motion='reduce');pg.wait_for_timeout(200);P('mouvement réduit respecté :',pg.evaluate("getComputedStyle($('#wp .wsh2')).animationName")=='none');pg.emulate_media(reduced_motion='no-preference')
  # fond personnel
  with pg.expect_file_chooser() as fc:pg.evaluate("wpPick()")
  fc.value.set_files('tests/fixtures/photo_os.jpg');pg.wait_for_function("() => wpGet() !== ''",timeout=15000);pg.wait_for_timeout(500)
  v=pg.evaluate("localStorage.getItem('ptua_wpimg')");P('photo enregistrée (JPEG réduit, < 1,7 Mo) :',v.startswith('data:image/jpeg;base64,') and len(v)<1.7e6,len(v))
  P('photo affichée en fond :',pg.evaluate("$('#wp').classList.contains('own') && $('#wp .wpi').style.backgroundImage.includes('data:image/jpeg') && document.documentElement.dataset.wp=='1'"))
  P('photo : décor du thème remplacé :',pg.evaluate("!$('#wp .wsh2') && !$('#wp .wl')"))
  P('photo : fond 3D classique masqué :',pg.evaluate("getComputedStyle($('#bg')).display")=='none')
  P('photo non synchronisée ni dans la base :',pg.evaluate("!JSON.stringify(db).includes('data:image/jpeg') && !JSON.stringify(syData()).includes('data:image/jpeg')"))
  pg.evaluate("thSet('clair')");pg.wait_for_timeout(300);P('photo visible aussi en thème clair :',pg.evaluate("getComputedStyle($('#wp')).display")=='block')
  pg.screenshot(path='/tmp/t35_photo.png')
  pg.evaluate("thSet('sombre')");pg.wait_for_timeout(300);P('photo en thème sombre : voile sombre :',pg.evaluate("$('#wp').classList.contains('dk')"))
  # photo piégée / fichier non image
  pg.evaluate("localStorage.setItem('ptua_wpimg','data:image/jpeg;base64,AAAA\" onerror=\"window.__x=1')");pg.evaluate("wpApply()");P('valeur piégée refusée :',pg.evaluate("wpGet()===''") and pg.evaluate("window.__x===undefined"))
  pg.evaluate("localStorage.setItem('ptua_wpimg','javascript:alert(1)')");pg.evaluate("wpApply()");P('valeur étrangère refusée :',pg.evaluate("wpGet()===''"))
  pg.evaluate("wpFile(new File(['x'],'a.svg',{type:'image/svg+xml'}))");pg.wait_for_timeout(300);P('SVG refusé :',pg.evaluate("wpGet()===''"))
  pg.evaluate("wpFile(new File(['pas une image'],'a.jpg',{type:'image/jpeg'}))");pg.wait_for_timeout(500);P('fichier corrompu refusé sans planter :',pg.evaluate("wpGet()===''"))
  # retrait
  pg.evaluate("localStorage.removeItem('ptua_wpimg')")
  with pg.expect_file_chooser() as fc:pg.evaluate("wpPick()")
  fc.value.set_files('tests/fixtures/photo_os.jpg');pg.wait_for_function("() => wpGet() !== ''",timeout=15000);pg.evaluate("wpClear()");pg.wait_for_timeout(300)
  P('photo retirée :',pg.evaluate("wpGet()===''") and pg.evaluate("document.documentElement.dataset.wp===undefined"))
  # impression : décor caché ; tous les onglets sans erreur dans les deux thèmes animés
  for k in ['ninja','pirate']:
    pg.evaluate(f"thSet('{k}')")
    for t in ['dash','marches','garanties','assurances','conf','os','avenants','search','stats','pres','veille','sauv','act','cyber','amel','journal']:pg.evaluate(f"go('{t}')")
  pg.emulate_media(media='print');P('impression : décor masqué :',pg.evaluate("getComputedStyle($('#wp')).display")=='none');pg.emulate_media(media='screen')
  # mobile
  m=b.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True);q=m.new_page();q.on('pageerror',lambda e:errs.append(str(e)));q.goto('http://localhost:8765/');q.wait_for_timeout(2500);q.evaluate("localStorage.clear();thSet('ninja')");q.wait_for_timeout(300)
  P('mobile : moins de particules :',q.evaluate("$('#wp').querySelectorAll('.wl').length")<=9);q.evaluate("thSet('pirate')");P('mobile : pirate :',q.evaluate("$('#wp').querySelectorAll('.wsp').length")<=7)
  q.screenshot(path='/tmp/t35_mobile.png')
  P('erreurs :',errs);b.close()
