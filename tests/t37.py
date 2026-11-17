# v9.16 — lecture des scans (OCR sur l'appareil) : préparer avec python3 tests/t37_gen.py
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[];bad=0
def ck(n,c):
  global bad
  P(('OK  ' if c else 'ÉCHEC ')+n)
  if not c:bad+=1
with sync_playwright() as p:
  b=p.chromium.launch(executable_path=__import__('shutil').which('google-chrome'))
  c=b.new_context(viewport={'width':1100,'height':800});pg=c.new_page();pg.set_default_timeout(60000)
  ext=[]
  pg.on('request',lambda r:not r.url.startswith('http://localhost:8765') and not r.url.startswith('data:') and not r.url.startswith('blob:') and ext.append(r.url))
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and 'ERR_' not in m.text and 'Failed to load' not in m.text and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500);pg.evaluate("localStorage.clear()");pg.reload();pg.wait_for_timeout(2500)
  pg.evaluate("""db.marches.push({id:'m1',titulaire:'SOGEA SATOM',num:'2026-0001',objet:'Traversée d’Adjamé',montant:'1000000000',debut:'2026-03-01',delaiM:'18'});
   db.assurances.push({id:'a1',marche:'m1',type:'Tous risques chantier (TRC)',assureur:'NSIA',police:'',assure:'SOGEA SATOM',montant:'1200000000',effet:'2026-03-01',echeance:'2028-12-31',statut:'Active'});
   db.assurances.push({id:'a2',marche:'m1',type:'Tous risques chantier (TRC)',assureur:'',police:'',assure:'SOGEA SATOM',statut:'Active'});
   save();go('assurances')""");pg.wait_for_timeout(500)
  pg.evaluate("docs('assurances','a1')");pg.wait_for_timeout(300);pg.set_input_files('#ff','/tmp/scan_att.pdf');pg.wait_for_timeout(4000)
  pg.evaluate("docs('assurances','a2')");pg.wait_for_timeout(300);pg.set_input_files('#ff','/tmp/scan_att.jpg');pg.wait_for_timeout(4000)
  pg.evaluate("$('#cd').close()")
  ck('documents joints (PDF image seul et JPEG)',pg.evaluate("db.assurances.map(a=>(a.files||[]).length).join()=='1,1'"))
  # lecture de tous les scans depuis la recherche
  pg.evaluate("go('search')");pg.wait_for_timeout(600)
  ck('carte « Lire mes scans » visible',pg.evaluate("document.body.innerText.includes('Lire mes scans')"))
  pg.evaluate("ocAll()");pg.wait_for_function("() => document.querySelector('#ocs') && document.querySelector('#ocs').innerText.includes('Terminé')",timeout=180000)
  P(pg.inner_text('#ocs'))
  t1=pg.evaluate("OCX[db.assurances[0].files[0].id]||''");t2=pg.evaluate("OCX[db.assurances[1].files[0].id]||''")
  ck('OCR du PDF scanné : attestation et police lues',('1.200.000.000' in t1 or '1 200 000 000' in t1) and 'TRC-2026' in t1.replace(' ','').replace('—','-'))
  ck('OCR de la photo JPEG : capital et période lus',('1.200.000.000' in t2 or '1200000000' in t2.replace('.','').replace(' ','')) and '2028' in t2)
  P('  extrait PDF :',t1[:160].replace('\n',' | '))
  ck('texte lu conservé chiffré (pas en clair) dans IndexedDB',pg.evaluate("""(async()=>{const f=db.assurances[0].files[0],d=await stGet('ocr:'+f.id);return !!d&&!new TextDecoder().decode(d).includes('ATTESTATION')})()"""))
  ck('aucune requête vers l’extérieur pendant la lecture',not ext)
  if ext:P(ext[:5])
  # recherche dans le texte des scans
  pg.evaluate("OCX={}");pg.evaluate("go('search')");pg.wait_for_timeout(1500)
  pg.fill('#gq','franchise sinistre');pg.wait_for_timeout(500)
  ck('recherche : trouve une assurance par le texte du scan',pg.evaluate("document.querySelector('#sr').innerText.includes('trouvé dans un scan')"))
  pg.fill('#gq','zzzintrouvablezzz');pg.wait_for_timeout(300)
  ck('recherche : mot absent → aucun résultat',pg.evaluate("document.querySelector('#sr').innerText.includes('Aucun résultat')"))
  # analyse d'assurance sur un PDF scanné
  pg.evaluate("go('conf')");pg.wait_for_timeout(400)
  pg.evaluate("OCX={}");pg.evaluate("anPol='a1';render()");pg.evaluate("anGo('a1')");pg.wait_for_function("() => ANR.a1!=null",timeout=120000);pg.wait_for_timeout(300)
  R=pg.evaluate("(()=>{const R=ANR.a1;return{has:R.has,ocr:(R.info||{}).ocr,C:R.C.map(c=>c.g+'|'+c.l+'|'+c.v)}})()")
  ck('analyse : texte du scan exploité (has) et signalé comme lu automatiquement',R['has'] and R['ocr']==1)
  P('  contrôles :',[x for x in R['C']][:8])
  ck('analyse : l’affichage prévient de vérifier montants et dates',pg.evaluate("document.body.innerText.includes('lu automatiquement')"))
  # suppression du document : texte lu effacé
  pg.evaluate("""(async()=>{const f=db.assurances[0].files[0];await fDel(f.id);window.__g=await stGet('ocr:'+f.id)})()""");pg.wait_for_timeout(500)
  ck('effacement du document : texte lu effacé aussi',pg.evaluate("window.__g===undefined"))
  ck('aucune erreur JavaScript',not errs)
  if errs:P(errs[:5])
  b.close()
P('ÉCHECS :',bad)
raise SystemExit(1 if bad else 0)
