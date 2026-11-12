import json,hashlib,time
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
DB={};H={};errs=[];alerts=[]
def handle(route):
  req=route.request;fn=req.url.split('/rpc/')[1];a=json.loads(req.post_data or '{}')
  h=hashlib.sha256(a.get('p_auth','').encode()).hexdigest();row=DB.get(a['p_id']);ok=row and row['h']==h
  if fn=='ptua_get':out=[{'ver':row['ver'],'blob':row['blob']}] if ok else []
  elif fn=='ptua_hist_list':out=[{'ver':v,'saved_at':t,'taille':len(b)} for (v,t,b) in sorted(H.get(a['p_id'],[]),reverse=True)] if ok else []
  elif fn=='ptua_hist_get':out=next((b for (v,t,b) in H.get(a['p_id'],[]) if v==a['p_ver']),None) if ok else None
  elif a['p_ver']==0:
    out=-1 if row else 1
    if not row: DB[a['p_id']]={'h':h,'ver':1,'blob':a['p_blob']}
  elif ok and row['ver']==a['p_ver']:
    H.setdefault(a['p_id'],[]).append((row['ver'],time.strftime('%Y-%m-%dT%H:%M:%S.000Z',time.gmtime(time.time()-3600*(10-row['ver']))),row['blob']))
    row['ver']+=1;row['blob']=a['p_blob'];out=row['ver']
  else: out=-1
  route.fulfill(status=200,content_type='application/json',body=json.dumps(out))
def dev(b,name):
  c=b.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True)
  pg=c.new_page();pg.set_default_timeout(8000);pg.route('https://iofbwpzhptctyelmylkz.supabase.co/**',handle)
  pg.on('pageerror',lambda e:errs.append(name+': '+str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(name+': '+m.text))
  pg.on('dialog',lambda d:(alerts.append(name+': '+d.message[:60]),d.accept()))
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2300);return pg
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  pc=dev(b,'PC')
  pc.evaluate("db.marches.push({id:'m1',titulaire:'SOGEA',num:'2024-0153',montant:'1000'},{id:'m2',titulaire:'COLAS',num:'2025-0007',montant:'2000'});db.garanties.push({id:'g1',marche:'m1',type:'Soumission',statut:'Active',organisme:'NSIA'});save()")
  pc.evaluate("setTimeout(syStart,0)");pc.wait_for_timeout(600);pc.fill('#cd input[name=a]','Test#Motdepasse2026');pc.fill('#cd input[name=b]','Test#Motdepasse2026');pc.click('#cd .pri');pc.wait_for_timeout(3000)
  pc.click('#cd button[data-i="0"]');pc.wait_for_timeout(2500);key=pc.evaluate("SY.code");pc.click('#cd .pri');pc.wait_for_timeout(500)
  pc.evaluate("db.marches[0].objet='modif';db.marches[0]._u=Date.now();save()");pc.wait_for_timeout(4000)
  # catastrophe : suppression de tous les marchés, synchronisée
  pc.evaluate("confirm=()=>true;del('marches','m1');del('marches','m2')");pc.wait_for_timeout(4500)
  P('après catastrophe : marchés PC',pc.evaluate("db.marches.length"),'| versions archivées',len(list(H.values())[0]))
  pc.evaluate("go('sauv')");pc.wait_for_timeout(400)
  P('carte « rien à faire » affichée :',pc.evaluate("document.body.innerText.includes('Rien à faire de votre côté')"),'| bannière export 7 j masquée :',pc.evaluate("!$('#al').textContent.includes('Aucune sauvegarde depuis')"))
  pc.screenshot(path='/tmp/s79.png',full_page=False)
  pc.evaluate("cloudHist()");pc.wait_for_timeout(1500);pc.locator('#cd').screenshot(path='/tmp/s79h.png')
  pc.locator('#cd [data-r]').last.click();pc.wait_for_timeout(4000)
  P('après restauration : marchés PC',pc.evaluate("db.marches.map(m=>m.num).join(', ')"),'| garanties',pc.evaluate("db.garanties.length"))
  # appareil effacé -> nouvel appareil récupère tout avec la clé
  ph=dev(b,'Nouvel iPhone')
  ph.evaluate("setTimeout(syStart,0)");ph.wait_for_timeout(600);ph.fill('#cd input[name=a]','Test#Autre2026xx');ph.fill('#cd input[name=b]','Test#Autre2026xx');ph.click('#cd .pri');ph.wait_for_timeout(3000)
  ph.click('#cd button[data-i="2"]');ph.wait_for_timeout(300);ph.fill('#syc',key);ph.click('#cd .pri');ph.wait_for_timeout(3500)
  P('appareil vierge a tout récupéré :',ph.evaluate("db.marches.map(m=>m.num).join(', ')+' | garanties '+db.garanties.length"))
  P('alertes:',alerts);P('erreurs:',errs);b.close()
