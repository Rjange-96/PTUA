# v9.20 — liste officielle 2026 des organismes habilités à délivrer des cautionnements : contrôle automatique de l'organisme garant
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  c=b.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True);pg=c.new_page();pg.set_default_timeout(20000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500)
  pg.evaluate("""db.marches.push({id:'m1',titulaire:'SOGEA SATOM',num:'2026-0001',objet:'Traversée d’Adjamé',montant:'1000000000',debut:'2026-03-01',delaiM:'18',notif:'2026-01-10'});
   const O=['SERENITY SA','SUNU Assurances IARD','NSIA Banque','NSIA','Société Inconnue SA','<img src=x onerror=window.__x=1>',''];
   O.forEach((o,i)=>db.garanties.push({id:'g'+i,marche:'m1',type:'Bonne exécution',organisme:o,montant:'40000000',emission:'2026-01-25',echeance:'2027-12-31',statut:'Active'}));
   save();go('conf')""");pg.wait_for_timeout(600)
  P('carte liste 2026 présente :','Liste officielle 2026 des organismes habilités' in pg.inner_text('#v'))
  res={}
  for i in range(7):
    pg.evaluate(f"GAP='g{i}';render()");pg.evaluate(f"gaGo('g{i}')");pg.wait_for_function(f"GAR.g{i}!=null",timeout=20000)
    res[i]=pg.evaluate(f"(()=>{{const c=GAR.g{i}.C.find(c=>c.l.startsWith('Organisme habilité'));return c?c.v+'|'+c.co:''}})()")
    P(' ',i,res[i][:150])
  P('assureur habilité (Serenity) : conforme :',res[0].startswith('ok|') and 'cautionnements' in res[0])
  P('assureur non habilité (SUNU IARD) : NON CONFORME :',res[1].startswith('ko|') and 'ne figure pas' in res[1])
  P('banque : à vérifier :',res[2].startswith('chk|') and 'banque' in res[2])
  P('nom ambigu (NSIA) : à vérifier :',res[3].startswith('chk|'))
  P('organisme inconnu : à vérifier :',res[4].startswith('chk|') and 'non retrouvé' in res[4])
  P('organisme piégé : à vérifier, aucun script :',res[5].startswith('chk|') and pg.evaluate("window.__x")is None)
  P('organisme vide : à vérifier :',res[6].startswith('chk|'))
  # la décision de l'utilisateur reste possible sur un assureur non habilité, et la case agrément n'efface pas le constat
  pg.evaluate("gaSetS('g1','ag',true)");pg.evaluate("GAP='g1';render()");pg.evaluate("gaGo('g1')");pg.wait_for_function("GAR.g1!=null");pg.wait_for_timeout(300)
  P('case cochée : le non habilité reste signalé :',pg.evaluate("GAR.g1.C.find(c=>c.l.startsWith('Organisme habilité')).v")=='ko')
  P('verdict global non conforme :',pg.evaluate("GAR.g1.verdict")=='ko')
  # pastille dans la fiche
  pg.evaluate("GAP='g0';render()");P('pastille ✅ pour Serenity :','Habilité aux cautionnements' in pg.inner_text('#v'))
  pg.evaluate("GAP='g1';render()");P('pastille ❌ pour SUNU :','Non habilité aux cautionnements' in pg.inner_text('#v'))
  # vérificateur libre
  pg.evaluate("agrQ('La Loyale')");P('vérificateur : La Loyale habilitée :','Habilitée' in pg.text_content('#agrR'))
  pg.evaluate("agrQ('AXA')");P('vérificateur : AXA non habilitée :','NON habilitée' in pg.text_content('#agrR'))
  P('13 sociétés dans la liste des cautionnements :',pg.evaluate("AGR.E.filter(e=>e[3].includes('c')).length")==13)
  # liste périmée : bascule en « à vérifier »
  pg.evaluate("AGR.annee=2020");pg.evaluate("gaGo('g0')");pg.wait_for_function("GAR.g0!=null");pg.wait_for_timeout(300)
  P('liste d\'une année passée : à vérifier :',pg.evaluate("GAR.g0.C.find(c=>c.l.startsWith('Organisme habilité')).v")=='chk')
  P('erreurs :',errs)
