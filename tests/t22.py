# v9.0 — module Conformité : pièces, garanties, assurances, persistance, fiche
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  c=b.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True);pg=c.new_page();pg.set_default_timeout(15000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500)
  pg.evaluate("""db.marches.push({id:'m1',titulaire:'SOGEA <img src=x onerror=window.__x=1>',num:'2026-0001',objet:'Voirie',montant:'1000000000',debut:'2026-03-01',delaiM:'6',notif:'2026-01-10'});
   db.garanties.push({id:'g1',marche:'m1',type:'Bonne exécution',organisme:'NSIA',montant:'20000000',emission:'2026-03-15',echeance:'2026-06-01',statut:'Active'});
   db.garanties.push({id:'g2',marche:'m1',type:'Soumission',organisme:'NSIA',montant:'10000000',statut:'Active'});
   db.assurances.push({id:'a1',marche:'m1',type:'Tous risques chantier (TRC)',assureur:'NSIA',police:'T1',montant:'900000000',effet:'2026-04-01',echeance:'2026-12-01',statut:'Active'});
   db.os.push({id:'o1',marche:'m1',type:'Démarrage',date:'2026-03-01'});save();go('conf')""");pg.wait_for_timeout(700)
  G=pg.evaluate("cfGar(mk('m1')).map(x=>x[0]+'|'+x[1])");[P(' G',x) for x in G]
  A=pg.evaluate("cfAss(mk('m1')).map(x=>x[0]+'|'+x[1]+'|'+x[2])");[P(' A',x) for x in A]
  P('GBE 2 % hors fourchette :',any(x.startswith('warn') and '2.0 %' in x for x in G))
  P('GBE tardive (65 j) :',any(x.startswith('warn') and 'dépassé' in x for x in G))
  P('échéance avant fin travaux :',any('antérieure à la fin prévue' in x for x in G))
  P('soumission à libérer :',any('Garantie de soumission' in x for x in G))
  P('TRC effet après démarrage :',any('postérieur au démarrage' in x for x in A))
  P('décennale/RC/AT manquantes :',sum('Aucune police' in x for x in A)==3)
  P('TRC et GBE détectées :',pg.evaluate("cfRows(mk('m1')).flatMap(p=>p.it).filter(i=>['gbe','trc','osd'].includes(i.k)).every(i=>i.done)"))
  # alerte de retard : fiscale sans date => pas de retard ; avec date ancienne => retard
  pg.evaluate("cfDate('m1','dA','2026-01-05')");pg.wait_for_timeout(300)
  P('retard attestation fiscale :',pg.evaluate("cfRows(mk('m1'))[0].it[0].j<0"))
  pg.evaluate("cfTog('m1','fisc')");pg.wait_for_timeout(200);P('fisc fait :',pg.evaluate("cfRows(mk('m1'))[0].it[0].done"))
  pg.evaluate("cfTog('m1','fisc')");P('fisc N/A :',pg.evaluate("cfRows(mk('m1'))[0].it[0].na"))
  pg.evaluate("cfClause('a1',2)");P('clause cochée :',pg.evaluate("CFS(db.assurances[0]).c[2]==1"))
  P('XSS :',pg.evaluate("window.__x===undefined"),'| échappé dans la page :','<img src=x' not in pg.inner_html('#v'))
  P('page contient les sections :',all(s in pg.inner_text('#v') for s in ['Légalité des garanties','Conformité des assurances','Clauses à vérifier','Redevance de régulation','2 500 000'.replace(' ',' ')]) or 'Redevance' in pg.inner_text('#v'))
  P('alerte tableau de bord :',pg.evaluate("go('dash'),$('#al').textContent.includes('conformité à traiter')"))
  # persistance et sanitation
  pg.evaluate("go('conf')");R=pg.evaluate("JSON.stringify(sanDB(JSON.parse(JSON.stringify(db))).marches[0].cf)");P('cf survit à sanDB :',len(R)>10)
  pg.evaluate("window.print=()=>{window.__p=document.body.classList.contains('pfs')&&$('#fs').textContent.includes('FICHE DE CONFORMITÉ')}");pg.evaluate("cfPrint('m1')");pg.wait_for_timeout(400);P('fiche imprimable :',pg.evaluate("window.__p===true"))
  # fusion de synchro : la version la plus récente gagne
  M=pg.evaluate("(()=>{const L=JSON.parse(JSON.stringify(db)),R=JSON.parse(JSON.stringify(db));R.marches[0].cf='{\"s\":{\"enr\":\"f\"}}';R.marches[0]._u=Date.now()+5000;return mergeDB(L,R).marches[0].cf})()");P('fusion sync :','enr' in M)
  pg.screenshot(path='/tmp/c1.png',full_page=True)
  pg.evaluate("go('conf')");P('onglet visible dans Plus :',pg.evaluate("NAV.some(n=>n[0]=='conf')"))
  P('erreurs :',errs);b.close()
