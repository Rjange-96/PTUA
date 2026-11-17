# v9.10 — Type (et marché) figé en haut de la fenêtre de modification des garanties, même en défilant
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path=__import__('shutil').which('google-chrome'))
  pg=b.new_page();pg.set_default_timeout(15000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2300)
  pg.evaluate("setTimeout(pinMenu,0)");pg.wait_for_timeout(300)
  pg.fill('#cd input[name=a]','Test#Figer2026');pg.fill('#cd input[name=b]','Test#Figer2026');pg.click('#cd .pri');pg.wait_for_timeout(2500)
  pg.evaluate("""db.marches.push({id:'m1',num:'2026-0099',titulaire:'T',objet:'O'});
    db.garanties.push({id:'g1',marche:'m1',type:'Bonne exécution',organisme:'Org',montant:'1000',echeance:'2027-01-01',statut:'Active'});
    save();render();0""")
  # 1) ouverture : le bandeau affiche le marché et le type de la garantie en cours
  pg.evaluate("go('garanties');edit('garanties','g1')");pg.wait_for_timeout(300)
  P('bandeau affiche marché + type à l’ouverture :',pg.evaluate("$('#dsub').textContent")=='2026-0099 — Bonne exécution')
  P('bandeau en position figée (sticky) :',pg.evaluate("getComputedStyle($('#dhd')).position")=='sticky')
  # 2) le bandeau reste collé en haut même après défilement du formulaire
  off0=pg.evaluate("$('#dhd').getBoundingClientRect().top-$('#dlg').getBoundingClientRect().top")
  pg.evaluate("$('#dlg').scrollTop=$('#dlg').scrollHeight")
  off1=pg.evaluate("$('#dhd').getBoundingClientRect().top-$('#dlg').getBoundingClientRect().top")
  P('bandeau toujours visible en haut après défilement :',abs(off0-off1)<2,'(',off0,'->',off1,')')
  P('texte du bandeau inchangé après défilement :',pg.evaluate("$('#dsub').textContent")=='2026-0099 — Bonne exécution')
  # 3) le bandeau se met à jour si on change le type ou le marché affiché (avant d'enregistrer)
  pg.evaluate("db.marches.push({id:'m2',num:'2026-0100',titulaire:'T2'});save()")
  pg.evaluate("edit('garanties','g1')");pg.wait_for_timeout(200)
  pg.select_option('#df select[name=type]','Performance environnementale et sociale')
  P('bandeau mis à jour après changement de type :',pg.evaluate("$('#dsub').textContent")=='2026-0099 — Performance environnementale et sociale')
  pg.select_option('#df select[name=marche]','m2')
  P('bandeau mis à jour après changement de marché :',pg.evaluate("$('#dsub').textContent")=='2026-0100 — Performance environnementale et sociale')
  # 4) nouvelle garantie (sans id) : bandeau cohérent dès la saisie
  pg.evaluate("$('#dlg').close();edit('garanties')");pg.wait_for_timeout(200)
  P('bandeau affiche au moins le type par défaut pour une nouvelle garantie :',pg.evaluate("$('#dsub').textContent")=='Avance de démarrage')
  pg.select_option('#df select[name=marche]','m1');pg.select_option('#df select[name=type]','Soumission')
  P('bandeau rempli dès la saisie (nouvelle garantie) :',pg.evaluate("$('#dsub').textContent")=='2026-0099 — Soumission')
  # 5) pas d'effet de bord sur les autres fiches (marché, assurance…)
  pg.evaluate("$('#dlg').close();go('marches');edit('marches','m1')");pg.wait_for_timeout(200)
  P('bandeau vide pour une fiche marché :',pg.evaluate("$('#dsub').textContent")=='')
  pg.evaluate("$('#dlg').close()")
  P('erreurs :',errs[:5])
  b.close()
