from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
# v9.24 — Carte « Rappels » : avertit quand aucune alerte n'est programmée (sinon le serveur n'envoie jamais rien
# alors que l'écran affichait seulement « Rappels activés »), et donne la date de la première alerte sinon.
errs=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path=__import__('shutil').which('google-chrome'))
  c=b.new_context(viewport={'width':1100,'height':800},permissions=['notifications']);pg=c.new_page();pg.set_default_timeout(15000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500);pg.evaluate("localStorage.clear()");pg.reload();pg.wait_for_timeout(2500)
  pg.evaluate("SY={code:'AAAAAAAAAAAAAAAAAAAAAAAA',ver:0};localStorage.setItem(PUSHK,String(Date.now()))")
  card=lambda:pg.evaluate("(()=>{const d=document.createElement('div');d.innerHTML=pushUI();return {txt:d.innerText,warn:!!d.querySelector('#pz')}})()")
  r=card()
  P('rappels activés reconnus :','Rappels activés' in r['txt'])
  P('aucune échéance : avertissement affiché :',r['warn'] and 'Aucune alerte programmée' in r['txt'])
  pg.evaluate("""()=>{const d=x=>new Date(Date.now()+x*864e5).toISOString().slice(0,10);
   db.garanties.push({id:'g1',type:'Bonne exécution',statut:'Active',echeance:d(45),organisme:'X'});save()}""")
  r=card()
  P('avec une échéance : plus d’avertissement :',not r['warn'])
  P('nombre et date de la première alerte affichés :','alerte(s) programmée(s), première le' in r['txt'])
  pg.evaluate("db.garanties[0].statut='Mainlevée obtenue';save()")
  r=card()
  P('garantie en mainlevée : plus d’alerte, avertissement de nouveau :',r['warn'] and pg.evaluate('pushDue().length')==0)
  pg.evaluate("db.garanties[0].statut='Expirée';save()")
  P('garantie expirée : aucune alerte :',pg.evaluate('pushDue().length')==0)
  pg.evaluate("db.garanties[0].statut='Émise';save()")
  P('garantie émise : alertes :',pg.evaluate('pushDue().length')>0)
  b.close()
P('erreurs :',errs)
