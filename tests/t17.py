import json,hashlib
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
DB={};FILES={};REMOVED=set();errs=[];alerts=[];QUOTA=[False]
def handle(route):
  req=route.request;fn=req.url.split('/rpc/')[1];a=json.loads(req.post_data or '{}')
  h=hashlib.sha256(a.get('p_auth','').encode()).hexdigest();row=DB.get(a['p_id']);ok=row and row['h']==h
  if fn=='ptua_get':out=[{'ver':row['ver'],'blob':row['blob'],'updated_at':'2026-11-12T19:00:00Z'}] if ok else []
  elif fn=='ptua_file_put':
    if not ok:return route.fulfill(status=400,content_type='application/json',body='{"message":"acces refuse"}')
    if QUOTA[0]:return route.fulfill(status=400,content_type='application/json',body='{"message":"quota de documents atteint"}')
    key=(a['p_id'],a['p_fid'])
    if key not in FILES and key not in REMOVED:FILES[key]=a['p_blob']
    out=True
  elif fn=='ptua_file_get':out=FILES.get((a['p_id'],a['p_fid'])) if ok else None
  elif fn=='ptua_file_del':
    if ok:
      key=(a['p_id'],a['p_fid'])
      if key in FILES:FILES.pop(key);REMOVED.add(key)
    out=bool(ok)
  elif a['p_ver']==0:
    out=-1 if row else 1
    if not row: DB[a['p_id']]={'h':h,'ver':1,'blob':a['p_blob']}
  elif ok and row['ver']==a['p_ver']: row['ver']+=1;row['blob']=a['p_blob'];out=row['ver']
  else: out=-1
  route.fulfill(status=200,content_type='application/json',body=json.dumps(out))
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  def dev(name,mob):
    c=b.new_context(viewport={'width':393 if mob else 1280,'height':852},is_mobile=mob,has_touch=mob,accept_downloads=True);pg=c.new_page();pg.set_default_timeout(15000)
    pg.route('https://iofbwpzhptctyelmylkz.supabase.co/**',handle);pg.on('pageerror',lambda e:errs.append(name+str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(name+m.text));pg.on('dialog',lambda d:(alerts.append(d.message[:90]),d.accept()))
    pg.goto('http://localhost:8765/');pg.wait_for_timeout(3500);return pg
  def enc(pg,c):
    pg.fill('#cd input[name=a]',c);pg.fill('#cd input[name=b]',c);pg.click('#cd .pri');pg.wait_for_timeout(3000)
  pc=dev('PC ',False)
  P('SW précache PDF :',pc.evaluate("(async()=>{for(let i=0;i<20;i++){if(await caches.match('./lib/pdf.worker.min.mjs')&&await caches.match('./lib/pdf.min.mjs'))return true;await new Promise(r=>setTimeout(r,500))}return false})()"))
  pc.evaluate("db.marches.push({id:'m1',titulaire:'SOGEA SATOM',num:'2024-0153',montant:'850000000'});db.garanties.push({id:'g1',marche:'m1',organisme:'NSIA'});save();docs('garanties','g1')");pc.wait_for_timeout(300)
  pc.set_input_files('#ff',['/tmp/garantie.pdf','/tmp/photo_os.jpg']);pc.wait_for_timeout(4000)
  P('2 documents joints :',pc.evaluate("db.garanties[0].files.length"));pc.evaluate("$('#cd').close()")
  pc.evaluate("setTimeout(syStart,0)");pc.wait_for_timeout(600);enc(pc,'Test#Motdepasse2026');pc.click('#cd button[data-i=\"0\"]');pc.wait_for_timeout(4000);k=pc.evaluate("SY.code")
  P('bouton fiche de secours :',pc.evaluate("!!$('#cd [data-v=p]')"));pc.click('#cd .pri');pc.wait_for_timeout(2500)
  P('serveur fichiers :',len(FILES))
  pc.evaluate("go('sauv')");pc.wait_for_timeout(1200);P('statut docs :',pc.evaluate("$('#fst').textContent"))
  # diagnostic
  pc.evaluate("setTimeout(diag,0)");pc.wait_for_timeout(9000)
  P('diagnostic :\n'+pc.evaluate("[...document.querySelectorAll('#cd .dl p')].map(p=>p.textContent).join('\\n')"));P('verdict :',pc.evaluate("$('#cd p[style*=\"600\"]')?.textContent"))
  pc.locator('#cd').screenshot(path='/tmp/e1.png');pc.click('#cd .pri');P('fichiers serveur après diag (inchangé) :',len(FILES))
  # sauvegarde complète
  pc.evaluate("setTimeout(expFull,0)");pc.wait_for_timeout(500);pc.fill('#cd input[name=a]','Test#Sauvegarde2026!');pc.fill('#cd input[name=b]','Test#Sauvegarde2026!');pc.click('#cd .pri');pc.wait_for_timeout(3500)
  P('offre :',pc.evaluate("$('#cd h3').textContent"))
  with pc.expect_download() as d: pc.click('#cd .pri')
  d.value.save_as('/tmp/full.ptua');raw=open('/tmp/full.ptua','rb').read()
  P('fichier :',d.value.suggested_filename,len(raw),'octets | en clair ?',b'SOGEA' in raw or b'%PDF' in raw or b'JFIF' in raw)
  # suppression d'un doc (tombstone) puis d'une fiche, puis restauration
  f0=pc.evaluate("db.garanties[0].files[0].id");pc.evaluate("docs('garanties','g1')");pc.wait_for_timeout(300);pc.click(f'#cd [data-x=\"{f0}\"]');pc.wait_for_timeout(4000);pc.evaluate("$('#cd').open&&$('#cd').close()")
  P('après retrait : PC',pc.evaluate("db.garanties[0].files.length"),'serveur',len(FILES))
  pc.set_input_files('#imp','/tmp/full.ptua');pc.wait_for_timeout(600);pc.fill('#cd input[name=p]','mauvais');pc.click('#cd .pri');pc.wait_for_timeout(2500)
  P('mauvais mot de passe refusé :',any('incorrect' in a for a in alerts))
  pc.set_input_files('#imp','/tmp/full.ptua');pc.wait_for_timeout(600);pc.fill('#cd input[name=p]','Test#Sauvegarde2026!');pc.click('#cd .pri');pc.wait_for_timeout(7000)
  P('restauré : docs',pc.evaluate("db.garanties[0].files.length"),'| id ré-attribué :',pc.evaluate(f"!db.garanties[0].files.some(f=>f.id=='{f0}')"),'| lisibles :',pc.evaluate("Promise.all(db.garanties[0].files.map(f=>fLoad(f).then(b=>b.length==f.s))).then(a=>a.every(Boolean))"),'| serveur',len(FILES))
  P('alertes :',[a for a in alerts if 'restaur' in a or 'Remplacer' in a])
  # iPhone neuf : récupère tout
  ph=dev('iPh ',True);ph.evaluate("setTimeout(syStart,0)");ph.wait_for_timeout(600);enc(ph,'Test#Autre2026xx');ph.click('#cd button[data-i=\"2\"]');ph.wait_for_timeout(300);ph.fill('#syc',k);ph.click('#cd .pri');ph.wait_for_timeout(4500)
  P('iPhone : docs',ph.evaluate("db.garanties[0]?.files.length"),'| lisibles',ph.evaluate("Promise.all(db.garanties[0].files.map(f=>fLoad(f).then(b=>b.length==f.s))).then(a=>a.every(Boolean))"))
  # restauration sur appareil vierge sans synchro
  nv=dev('Neuf ',False);nv.set_input_files('#imp','/tmp/full.ptua');nv.wait_for_timeout(600);nv.fill('#cd input[name=p]','Test#Sauvegarde2026!');nv.click('#cd .pri');nv.wait_for_timeout(6000)
  P('appareil vierge : marchés',nv.evaluate("db.marches.length"),'docs',nv.evaluate("db.garanties[0].files.length"),'lisibles',nv.evaluate("Promise.all(db.garanties[0].files.map(f=>fLoad(f).then(b=>b.length==f.s))).then(a=>a.every(Boolean))"))
  # fichier corrompu / piégé
  bad=bytearray(raw);bad[-50]^=255;open('/tmp/bad.ptua','wb').write(bad);n0=len(alerts)
  nv.set_input_files('#imp','/tmp/bad.ptua');nv.wait_for_timeout(600);nv.fill('#cd input[name=p]','Test#Sauvegarde2026!');nv.click('#cd .pri');nv.wait_for_timeout(6000)
  P('doc altéré détecté :',[a for a in alerts[n0:] if 'illisible' in a])
  open('/tmp/bad2.ptua','wb').write(raw[:15]+b'\xff\xff\xff\xff'+raw[19:]);n0=len(alerts);nv.set_input_files('#imp','/tmp/bad2.ptua');nv.wait_for_timeout(1500);P('en-tête piégé refusé :',alerts[n0:])
  # quota
  QUOTA[0]=True;pc.evaluate("docs('garanties','g1')");pc.wait_for_timeout(300);pc.set_input_files('#ff','/tmp/photo_os.jpg');pc.wait_for_timeout(4000);pc.evaluate("$('#cd').open&&$('#cd').close();go('sauv')");pc.wait_for_timeout(1500)
  P('quota signalé :',pc.evaluate("$('#fst').textContent.includes('plein')"));QUOTA[0]=False
  # fiche
  pc.evaluate("window.print=()=>{window.__pr=document.body.classList.contains('pfs')&&$('#fs').textContent.includes(syFmt(SY.code))};setTimeout(fiche,0)");pc.wait_for_timeout(1200);P('fiche de secours prête à imprimer :',pc.evaluate("window.__pr"))
  ph.evaluate("go('sauv')");ph.wait_for_timeout(1000);ph.screenshot(path='/tmp/e2.png',full_page=True)
  P('erreurs :',errs);b.close()
