from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[];alerts=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  c=b.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True,accept_downloads=True);pg=c.new_page();pg.set_default_timeout(15000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:(alerts.append(d.message[:80]),d.accept()))
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500)
  pg.evaluate("""db.marches.push({id:'m1',titulaire:'SOGEA SATOM <img src=x onerror=window.__x=1>',num:'2024-0153',objet:'Réhabilitation de la voirie',montant:'850000000',debut:'2025-01-10',delaiM:'6',taux:'0.5',plafond:'10'});
   db.garanties.push({id:'g1',marche:'m1',type:'Bonne exécution',organisme:'NSIA Banque',montant:'85000000',emission:'2025-01-05',echeance:'2027-02-01',statut:'Active',fin_ev:'PV de réception définitive',fin_date:'2026-10-01'});
   db.assurances.push({id:'a1',marche:'m1',type:'Tous risques chantier (TRC)',assureur:'NSIA Assurances',police:'TRC-2026-0042',assure:'SOGEA SATOM',montant:'900000000',echeance:'2026-12-01',statut:'Active'});
   db.os.push({id:'o1',marche:'m1',num:'OS1',type:'Démarrage',date:'2025-01-10'});save();go('marches')""");pg.wait_for_timeout(800)
  T=pg.evaluate("(()=>{const o={};for(const [e,id] of [['marches','m1'],['garanties','g1'],['assurances','a1']])o[e]=lettres(e,db[e].find(x=>x.id==id)).map(t=>[t.n,t.t]);return o})()")
  for e,l in T.items():P(e,'->',[n for n,_ in l])
  allt='\n'.join(t for l in T.values() for _,t in l)
  P('aucun undefined/NaN/null :',not any(w in allt for w in ['undefined','NaN','null','[object']))
  m=dict(T['marches'])
  P('mise en demeure : numéro, objet, montant, retard, pénalité :','2024-0153' in m['Mise en demeure d’exécuter le marché'],'Réhabilitation' in allt,'850 000 000'.replace(' ',' ') in allt or '850 000 000' in allt,'jour(s)' in allt,'0,5 ‰' in allt)
  
  pg.screenshot(path='/tmp/i0.png')
  # UI marché : bouton ✉️ et choix
  pg.evaluate("go('garanties')");pg.wait_for_timeout(500);P('bouton ✉️ sur garanties :',pg.evaluate("[...document.querySelectorAll('button')].some(b=>b.textContent.includes('✉️'))"))
  pg.evaluate("go('os')");pg.wait_for_timeout(400);P('pas de ✉️ sur OS :',pg.evaluate("![...document.querySelectorAll('#v button')].some(b=>b.textContent.includes('✉️'))"))
  pg.evaluate("go('marches')");pg.wait_for_timeout(400);pg.evaluate("setTimeout(()=>cour('marches','m1'),0)");pg.wait_for_timeout(500);P('choix des modèles marché :',pg.evaluate("[...document.querySelectorAll('#cd button')].map(b=>b.textContent.trim()).slice(0,3)"))
  pg.click('#cd button[data-i="0"]');pg.wait_for_timeout(600);pg.screenshot(path='/tmp/i1.png')
  P('texte dans l’éditeur :',pg.evaluate("$('#cot').value.length>500"),'| éditable :',pg.evaluate("(()=>{$('#cot').value+=' MODIF';return $('#cot').value.endsWith('MODIF')})()"))
  with pg.expect_download() as d: pg.click('#cd button[data-v="w"]')
  d.value.save_as('/tmp/c.doc');h=open('/tmp/c.doc',encoding='utf8').read()
  P('Word :',d.value.suggested_filename,'| HTML échappé :','<img src=x' not in h and '&lt;img' in h,'| modification incluse :','MODIF' in h,'| balises Word :','urn:schemas-microsoft-com:office:word' in h)
  P('XSS neutralisé :',pg.evaluate("window.__x===undefined"))
  pg.evaluate("window.print=()=>{window.__p=document.body.classList.contains('pfs')&&$('#fs').textContent.includes('Bonjour <b>x</b>')}");pg.evaluate("courShow({n:'t',f:'t',t:'Bonjour <b>x</b>'})");pg.click('#cd button[data-v="p"]');pg.wait_for_timeout(600);P('impression prête :',pg.evaluate("window.__p"),'| journal :',pg.evaluate("db.journal.some(j=>j.m.includes('Courrier généré'))"))
  pg.evaluate("$('#cd').open&&$('#cd').close()")
  P('erreurs :',errs);b.close()
