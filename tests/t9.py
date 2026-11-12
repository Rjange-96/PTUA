import json,hashlib
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
DB={};errs=[];alerts=[]
def handle(route):
  req=route.request;fn=req.url.split('/rpc/')[1];a=json.loads(req.post_data or '{}')
  if req.headers.get('apikey','')!='sb_publishable_sFlCanmeyZ_iOQJ6zynyqA_qPgTsUey':return route.fulfill(status=401,body='{}')
  h=hashlib.sha256(a.get('p_auth','').encode()).hexdigest();row=DB.get(a['p_id'])
  if fn=='ptua_get':out=[{'ver':row['ver'],'blob':row['blob'],'updated_at':''}] if row and row['h']==h else []
  else:
    if a['p_ver']==0:
      if row: out=-1
      else: DB[a['p_id']]={'h':h,'ver':1,'blob':a['p_blob']};out=1
    elif row and row['h']==h and row['ver']==a['p_ver']: row['ver']+=1;row['blob']=a['p_blob'];out=row['ver']
    else: out=-1
  route.fulfill(status=200,content_type='application/json',body=json.dumps(out),headers={'access-control-allow-origin':'*'})
def dev(b,name,mobile):
  c=b.new_context(viewport={'width':393 if mobile else 1280,'height':852},is_mobile=mobile,has_touch=mobile)
  pg=c.new_page();pg.set_default_timeout(8000)
  pg.route('https://iofbwpzhptctyelmylkz.supabase.co/**',handle)
  pg.on('pageerror',lambda e:errs.append(name+': '+str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(name+': '+m.text))
  pg.on('dialog',lambda d:(alerts.append(name+': '+d.message[:80]),d.accept()))
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2300);return pg
def enc(pg,code='Test#Motdepasse2026'):
  pg.evaluate("setTimeout(pinMenu,0)");pg.wait_for_timeout(300);pg.fill('#cd input[name=a]',code);pg.fill('#cd input[name=b]',code);pg.click('#cd .pri');pg.wait_for_timeout(2500)
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  pc=dev(b,'PC',False)
  pc.evaluate("""()=>{db.marches.push({id:'m1',titulaire:'SOGEA SATOM',num:'2024-0153',objet:'Voirie',montant:'850000000',debut:'2026-01-08',delaiM:'12'},{id:'m2',titulaire:'COLAS',num:'2025-0007',objet:'Pont',montant:'300000000'});
     db.garanties.push({id:'g1',marche:'m1',type:'Bonne exécution',organisme:'NSIA',montant:'42500000',echeance:'2026-12-30',statut:'Active'});save()}""")
  enc(pc)
  pc.evaluate("setTimeout(syStart,0)");pc.wait_for_timeout(300);pc.click('#cd .pri');pc.wait_for_timeout(2500)
  key=pc.evaluate("$('.code').textContent");P('clé PC :',key);pc.click('#cd .pri');pc.wait_for_timeout(1500)
  P('serveur : lignes',len(DB),'| contient du texte clair ?',any('SOGEA' in r['blob'] or 'NSIA' in r['blob'] for r in DB.values()),'| badge PC :',pc.evaluate("$('#sys').textContent"))
  ph=dev(b,'iPhone',True);enc(ph,'Test#Autre2026xx')
  # mauvaise clé
  ph.evaluate("setTimeout(syStart,0)");ph.wait_for_timeout(300);ph.click('#cd button[data-i=\"2\"]');ph.wait_for_timeout(300)
  ph.fill('#syc','AAAA-BBBB-CCCC-DDDD-EEEE-FFFF');ph.click('#cd .pri');ph.wait_for_timeout(2500)
  P('mauvaise clé refusée :',ph.evaluate("SY===null"),'| serveur lignes :',len(DB))
  # bonne clé
  ph.evaluate("setTimeout(syStart,0)");ph.wait_for_timeout(300);ph.click('#cd button[data-i=\"2\"]');ph.wait_for_timeout(300)
  ph.fill('#syc',key.lower());ph.click('#cd .pri');ph.wait_for_timeout(3000)
  P('iPhone a reçu les données du PC :',ph.evaluate("db.marches.map(m=>m.num).join(', ')+' | garanties '+db.garanties.length"))
  # iPhone ajoute une garantie (via le formulaire) -> PC
  ph.evaluate("go('garanties');edit('garanties')");ph.wait_for_timeout(300)
  ph.select_option('#df select[name=marche]','m2');ph.fill('#df input[name=organisme]','SUNU');ph.fill('#df input[name=montant]','15000000');ph.evaluate("ok()");ph.wait_for_timeout(4000)
  pc.evaluate("syncNow()");pc.wait_for_timeout(2500)
  P('PC voit la garantie ajoutée sur iPhone :',pc.evaluate("db.garanties.some(g=>g.organisme=='SUNU')"))
  # modifications simultanées : PC modifie m1, iPhone supprime m2 (avec ses garanties)
  pc.evaluate("route=1;db.marches.find(m=>m.id=='m1').objet='Voirie (modifié PC)';db.marches.find(m=>m.id=='m1')._u=Date.now();save()")
  ph.evaluate("confirm=()=>true;del('marches','m2')")
  pc.wait_for_timeout(4500);ph.wait_for_timeout(500);ph.evaluate("syncNow()");ph.wait_for_timeout(2500);pc.evaluate("syncNow()");pc.wait_for_timeout(2500)
  r1=pc.evaluate("[db.marches.map(m=>m.objet).join('/'),db.garanties.map(g=>g.organisme).join('/')]");r2=ph.evaluate("[db.marches.map(m=>m.objet).join('/'),db.garanties.map(g=>g.organisme).join('/')]")
  P('PC     :',r1);P('iPhone :',r2);P('identiques :',r1==r2)
  ph.evaluate("go('sauv')");ph.wait_for_timeout(400);ph.screenshot(path='/tmp/s_sync.png')
  ph.reload();ph.wait_for_timeout(2300);ph.fill('#pin','Test#Autre2026xx');ph.evaluate("setTimeout(unl,0)");ph.wait_for_timeout(3000)
  P('après redémarrage : synchro active',ph.evaluate("!!SY&&SY.code.length==24"),'| badge',ph.evaluate("$('#sys').textContent"))
  ph.context.set_offline(True);ph.evaluate("dispatchEvent(new Event('offline'))")
  ph.evaluate("db.marches.push({id:'m9',num:'2026-HORSLIGNE',titulaire:'BOUYGUES',_u:Date.now()});save()");ph.wait_for_timeout(3500)
  P('hors ligne : badge',ph.evaluate("$('#sys').textContent"),'| en attente',ph.evaluate("SY.dc"))
  ph.context.set_offline(False);ph.evaluate("dispatchEvent(new Event('online'))");ph.wait_for_timeout(3500)
  pc.evaluate("syncNow()");pc.wait_for_timeout(2500)
  P('retour réseau -> PC reçoit le marché saisi hors ligne :',pc.evaluate("db.marches.some(m=>m.num=='2026-HORSLIGNE')"))
  P('version serveur :',[r['ver'] for r in DB.values()],'| texte clair sur serveur :',any('SOGEA' in r['blob'] for r in DB.values()))
  P('alertes :',alerts);P('erreurs :',errs)
  b.close()
