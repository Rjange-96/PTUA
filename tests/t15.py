import json,hashlib
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
DB={};FILES={};errs=[];alerts=[]
def handle(route):
  req=route.request;fn=req.url.split('/rpc/')[1];a=json.loads(req.post_data or '{}')
  h=hashlib.sha256(a.get('p_auth','').encode()).hexdigest();row=DB.get(a['p_id']);ok=row and row['h']==h
  if fn=='ptua_get':out=[{'ver':row['ver'],'blob':row['blob']}] if ok else []
  elif fn=='ptua_file_put':
    if not ok:return route.fulfill(status=400,body='{}')
    FILES.setdefault((a['p_id'],a['p_fid']),a['p_blob']);out=True
  elif fn=='ptua_file_get':out=FILES.get((a['p_id'],a['p_fid'])) if ok else None
  elif fn=='ptua_file_del':
    if ok:FILES.pop((a['p_id'],a['p_fid']),None)
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
    c=b.new_context(viewport={'width':393 if mob else 1280,'height':852},is_mobile=mob,has_touch=mob);pg=c.new_page();pg.set_default_timeout(10000)
    pg.route('https://iofbwpzhptctyelmylkz.supabase.co/**',handle);pg.on('pageerror',lambda e:errs.append(name+str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(name+m.text));pg.on('dialog',lambda d:(alerts.append(d.message[:70]),d.accept()))
    pg.goto('http://localhost:8765/');pg.wait_for_timeout(2400);return pg
  def enc(pg,c):
    pg.fill('#cd input[name=a]',c);pg.fill('#cd input[name=b]',c);pg.click('#cd .pri');pg.wait_for_timeout(3000)
  pc=dev('PC ',False)
  pc.evaluate("db.marches.push({id:'m1',titulaire:'SOGEA SATOM',num:'2024-0153',montant:'850000000'});save();go('garanties')")
  # nouvelle garantie avec scan PDF joint dès l'enregistrement
  pc.click('#v button.pri');pc.wait_for_timeout(300);pc.select_option('#df select[name=marche]','m1');pc.fill('#df input[name=organisme]','NSIA Banque')
  pc.set_input_files('#fa','/tmp/garantie.pdf');pc.click('#dlg .pri');pc.wait_for_timeout(1500)
  P('garantie + PDF joint :',pc.evaluate("JSON.stringify(db.garanties[0].files.map(f=>[f.n,f.t,f.s]))"),'| bouton :',pc.evaluate("$('#tb').textContent.includes('📎 1')"))
  P('fichier chiffré dans IndexedDB :',pc.evaluate("fGet(db.garanties[0].files[0].id).then(d=>{const t=new TextDecoder('latin1').decode(new Uint8Array(d).slice(0,2000));return d.byteLength>300000&&!t.includes('%PDF')})"))
  # ajout d'une photo via la fenêtre Documents
  gid=pc.evaluate("db.garanties[0].id");pc.evaluate(f"docs('garanties','{gid}')");pc.wait_for_timeout(300)
  pc.set_input_files('#ff','/tmp/photo_os.jpg');pc.wait_for_timeout(2500)
  P('photo compressée :',pc.evaluate("JSON.stringify(db.garanties[0].files.map(f=>[f.n,f.s]))"));pc.locator('#cd').screenshot(path='/tmp/d1.png')
  pc.click('#cd [data-o=\"\"]');pc.wait_for_timeout(3500)
  P('visionneuse PC :',pc.evaluate("$('#vpg').textContent"),'| pages',pc.evaluate("document.querySelectorAll('#vz .pg').length"),'| rendu canvas',pc.evaluate("[...document.querySelectorAll('#vz canvas')].some(c=>c.width>500)"))
  pc.screenshot(path='/tmp/d2.png');pc.evaluate("vClose();$('#cd').close()")
  # synchronisation -> iPhone
  pc.evaluate("setTimeout(syStart,0)");pc.wait_for_timeout(600);enc(pc,'Test#Motdepasse2026');pc.click('#cd button[data-i=\"0\"]');pc.wait_for_timeout(4000);k=pc.evaluate("SY.code");pc.click('#cd .pri');pc.wait_for_timeout(2500)
  P('serveur : fichiers',len(FILES),'| en clair ?',any('JVBERi' in v[:200000] for v in FILES.values()))
  ph=dev('iPh ',True);ph.evaluate("setTimeout(syStart,0)");ph.wait_for_timeout(600);enc(ph,'Test#Autre2026xx');ph.click('#cd button[data-i=\"2\"]');ph.wait_for_timeout(300);ph.fill('#syc',k);ph.click('#cd .pri');ph.wait_for_timeout(3500)
  ph.evaluate("go('garanties')");ph.wait_for_timeout(300);P('iPhone voit les documents :',ph.evaluate("$('#v').textContent.includes('Documents (2)')"))
  ph.evaluate(f"view('garanties','{gid}')");ph.wait_for_timeout(5000)
  P('visionneuse iPhone :',ph.evaluate("$('#vpg').textContent"),'| téléchargés et mis en cache :',ph.evaluate("Promise.all(db.garanties[0].files.map(f=>fGet(f.id))).then(a=>a.every(Boolean))"))
  ph.screenshot(path='/tmp/d3.png')
  ph.evaluate("$('#vb').scrollTo(0,$('#vb').scrollHeight)");ph.wait_for_timeout(1200);P('après défilement :',ph.evaluate("$('#vpg').textContent"))
  ph.evaluate("lock()");ph.wait_for_timeout(800);P('verrouillage ferme la visionneuse :',ph.evaluate("!$('#dv').open&&$('#dv').innerHTML===''"))
  # retrait d'un document sur le PC -> supprimé partout
  f0=pc.evaluate("db.garanties[0].files[0].id");pc.evaluate(f"docs('garanties','{gid}')");pc.wait_for_timeout(300);pc.click(f'#cd [data-x=\"{f0}\"]');pc.wait_for_timeout(4500)
  P('retrait : serveur',len(FILES),'fichier(s) | PC',pc.evaluate("db.garanties[0].files.length"))
  # fichier piégé refusé
  open('/tmp/faux.pdf','w').write('<script>alert(1)</script>');pc.set_input_files('#ff','/tmp/faux.pdf');pc.wait_for_timeout(1200)
  P('faux PDF refusé :',any('PDF valide' in a for a in alerts))
  P('erreurs :',errs);b.close()
