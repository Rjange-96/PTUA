# v9.5 — Partage avec un collègue : accès séparé, révocable, clé du propriétaire jamais transmise.
# Faux serveur reproduisant les règles SQL (ptua_ok = propriétaire OU collègue non révoqué ; gestion des accès = propriétaire seul).
import json,hashlib
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
DB={};FILES={};MEM={};errs=[];alerts=[];EVIL_LABEL=[False]
H=lambda x:hashlib.sha256(x.encode()).hexdigest()
def owner(a):r=DB.get(a.get('p_id'));return bool(r and r['h']==H(a.get('p_auth','')))
def okk(a):return owner(a) or any(m['sid']==a.get('p_id') and not m['rev'] and m['h']==H(a.get('p_auth','')) for m in MEM.values())
def handle(route):
  req=route.request;fn=req.url.split('/rpc/')[1];a=json.loads(req.post_data or '{}');st=200
  if req.headers.get('apikey','')!='sb_publishable_sFlCanmeyZ_iOQJ6zynyqA_qPgTsUey':return route.fulfill(status=401,body='{}')
  row=DB.get(a.get('p_id'))
  if fn=='ptua_get':out=[{'ver':row['ver'],'blob':row['blob'],'updated_at':''}] if row and okk(a) else []
  elif fn=='ptua_put':
    if a['p_ver']==0:
      out=-1 if row else 1
      if not row:DB[a['p_id']]={'h':H(a['p_auth']),'ver':1,'blob':a['p_blob']}
    elif okk(a) and row['ver']==a['p_ver']:row['ver']+=1;row['blob']=a['p_blob'];out=row['ver']
    else:out=-1
  elif fn=='ptua_file_put':
    if not okk(a):return route.fulfill(status=400,body='{"message":"acces refuse"}')
    FILES.setdefault((a['p_id'],a['p_fid']),a['p_blob']);out=True
  elif fn=='ptua_file_get':out=FILES.get((a['p_id'],a['p_fid'])) if okk(a) else None
  elif fn=='ptua_file_del':
    if okk(a):FILES.pop((a['p_id'],a['p_fid']),None)
    out=okk(a)
  elif fn=='ptua_hist_list':out=[]
  elif fn=='ptua_member_add':
    if not owner(a):return route.fulfill(status=400,body='{"message":"acces refuse"}')
    MEM[a['p_lid']]={'sid':a['p_id'],'h':H(a['p_mauth']),'env':a['p_env'],'label':a['p_label'],'rev':False};out=True
  elif fn=='ptua_member_list':
    out=[{'lid':k,'label':('<img src=x onerror=window.__x=1>' if EVIL_LABEL[0] else m['label']),'created_at':'2026-11-15T10:00:00Z','last_seen':None,'revoked_at':'2026-11-15T11:00:00Z' if m['rev'] else None} for k,m in MEM.items() if m['sid']==a['p_id']] if owner(a) else []
  elif fn=='ptua_member_revoke':
    m=MEM.get(a['p_lid']);out=bool(owner(a) and m and m['sid']==a['p_id'])
    if out:m['rev']=True;m['env']=''
  elif fn=='ptua_member_open':
    m=MEM.get(a['p_lid']);out=[{'sid':m['sid'],'env':m['env']}] if m and not m['rev'] and m['h']==H(a['p_auth']) else []
  else:out=None;st=404
  route.fulfill(status=st,content_type='application/json',body=json.dumps(out))
CONFIRM=[True]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  def dev(name,mob):
    c=b.new_context(viewport={'width':393 if mob else 1280,'height':852},is_mobile=mob,has_touch=mob);pg=c.new_page();pg.set_default_timeout(10000)
    pg.route('https://iofbwpzhptctyelmylkz.supabase.co/**',handle);pg.on('pageerror',lambda e:errs.append(name+str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(name+m.text))
    def dlg(d):
      alerts.append(name+d.message[:90])
      if d.type=='confirm' and not CONFIRM[0] and 'Rejoindre un espace' in d.message:d.dismiss()
      else:d.accept()
    pg.on('dialog',dlg);pg.goto('http://localhost:8765/');pg.wait_for_timeout(2300);return pg
  def enc(pg,code):
    pg.evaluate("setTimeout(pinMenu,0)");pg.wait_for_timeout(300);pg.fill('#cd input[name=a]',code);pg.fill('#cd input[name=b]',code);pg.click('#cd .pri');pg.wait_for_timeout(2500)
  def join(pg,code):
    pg.evaluate("setTimeout(syStart,0)");pg.wait_for_timeout(400);pg.click('#cd button[data-i="3"]');pg.wait_for_timeout(300);pg.fill('#syc',code);pg.click('#cd .pri');pg.wait_for_timeout(3500)
  # 1) Propriétaire : données + document + synchronisation
  pc=dev('PC: ',False)
  pc.evaluate("""()=>{db.marches.push({id:'m1',titulaire:'SOGEA SATOM',num:'2024-0153',montant:'850000000'});db.garanties.push({id:'g1',marche:'m1',type:'Bonne exécution',organisme:'NSIA',montant:'42500000',echeance:'2026-12-30',statut:'Active'});save()}""")
  enc(pc,'Test#Motdepasse2026')
  pc.evaluate("setTimeout(syStart,0)");pc.wait_for_timeout(300);pc.click('#cd .pri');pc.wait_for_timeout(2500)
  okey=pc.evaluate("SY.code");pc.click('#cd .pri');pc.wait_for_timeout(800)
  pc.evaluate("""async()=>{const c=document.createElement('canvas');c.width=c.height=40;c.getContext('2d').fillRect(0,0,20,20);const bl=await new Promise(r=>c.toBlob(r,'image/jpeg',.9));await addFiles('garanties','g1',[new File([bl],'acte.jpg',{type:'image/jpeg'})])}""");pc.wait_for_timeout(2500)
  pc.evaluate("syncNow()");pc.wait_for_timeout(2500)
  # 2) Invitation
  pc.evaluate("go('sauv')");pc.wait_for_timeout(400)
  P('bouton « Partager avec un collègue » (propriétaire) :',pc.evaluate("[...document.querySelectorAll('button')].some(b=>b.textContent.includes('Partager avec un collègue'))"))
  pc.evaluate("setTimeout(ivList,0)");pc.wait_for_timeout(1200);pc.click('#cd [data-v="n"]');pc.wait_for_timeout(400);pc.fill('#ivn','Me Konan');pc.click('#cd .pri');pc.wait_for_timeout(2500)
  inv=pc.evaluate("$('#cd .code').textContent");P('invitation créée :',len(inv.replace('-',''))==24,'| QR affiché :',pc.evaluate("!!$('#cd .qr svg')"));pc.click('#cd .pri');pc.wait_for_timeout(400)
  P('enveloppe serveur sans clé du propriétaire ni données en clair :',all(okey not in m['env'] and 'SOGEA' not in m['env'] for m in MEM.values()))
  # 3) Collègue : mauvais code, puis refus de la confirmation, puis acceptation
  co=dev('Collègue: ',True);enc(co,'Autre#Code2026xx')
  join(co,'AAAA-BBBB-CCCC-DDDD-EEEE-FFFF');P('mauvais code refusé :',co.evaluate("SY===null"))
  CONFIRM[0]=False;join(co,inv);P('confirmation anti-hameçonnage refusée -> rien relié :',co.evaluate("SY===null"),'| marchés reçus :',co.evaluate("db.marches.length"));CONFIRM[0]=True
  join(co,inv.lower())
  P('collègue a reçu les fiches :',co.evaluate("db.marches.map(m=>m.num).join(',')+' / '+db.garanties.map(g=>g.organisme).join(',')"))
  P('accès invité, sans la clé du propriétaire :',co.evaluate("SY.guest===1&&!('code' in SY)"),'| clé absente de la mémoire :',co.evaluate(f"!JSON.stringify(SY).includes('{okey}')"))
  P('un seul espace sur le serveur :',len(DB))
  co.evaluate("go('sauv')");co.wait_for_timeout(400)
  P('collègue : pas de clé ni de gestion des accès :',co.evaluate("![...document.querySelectorAll('button')].some(b=>/Afficher la clé|Partager avec/.test(b.textContent))"),'| bandeau invité :',co.evaluate("document.body.textContent.includes('Espace partagé par un collègue')"))
  # 4) Document joint lisible par le collègue
  n=co.evaluate("(async()=>{const f=db.garanties[0].files[0];const b=await fLoad(f);return b.length})()");P('document lu par le collègue (octets) :',n)
  # 5) Modifications croisées
  co.evaluate("db.marches.push({id:'m7',num:'2026-COLLEGUE',titulaire:'COLAS',_u:Date.now()});save()");co.wait_for_timeout(3500)
  pc.evaluate("syncNow()");pc.wait_for_timeout(2500);P('propriétaire voit l’ajout du collègue :',pc.evaluate("db.marches.some(m=>m.num=='2026-COLLEGUE')"))
  pc.evaluate("db.marches.find(m=>m.id=='m1').objet='Voirie (propriétaire)';db.marches.find(m=>m.id=='m1')._u=Date.now();save()");pc.wait_for_timeout(3500)
  co.evaluate("syncNow()");co.wait_for_timeout(2500);P('collègue voit la modification du propriétaire :',co.evaluate("db.marches.find(m=>m.id=='m1').objet=='Voirie (propriétaire)'"))
  # 6) Assistant sécurité accessible (même contrôle d'accès) et redémarrage du collègue
  co.reload();co.wait_for_timeout(2300);co.fill('#pin','Autre#Code2026xx');co.evaluate("setTimeout(unl,0)");co.wait_for_timeout(3000)
  P('après redémarrage : accès invité conservé :',co.evaluate("!!SY&&SY.guest===1"))
  # 7) Libellé piégé renvoyé par le serveur : neutralisé
  EVIL_LABEL[0]=True;pc.evaluate("setTimeout(ivList,0)");pc.wait_for_timeout(1200);P('libellé piégé neutralisé :',pc.evaluate("!window.__x"));EVIL_LABEL[0]=False
  pc.evaluate("$('#cd').close()")
  # 8) Retrait de l'accès
  pc.evaluate("setTimeout(ivList,0)");pc.wait_for_timeout(1200);pc.click('#cd [data-r]');pc.wait_for_timeout(1500)
  P('liste : accès marqué retiré :',pc.evaluate("$('#cd').textContent.includes('Retiré')"));pc.evaluate("$('#cd').close()")
  co.evaluate("db.marches.push({id:'m8',num:'APRES-RETRAIT',_u:Date.now()});save()");co.wait_for_timeout(3500)
  P('collègue déconnecté après retrait :',co.evaluate("SY===null"),'| fiches conservées sur son appareil :',co.evaluate("db.marches.length>0"))
  pc.evaluate("syncNow()");pc.wait_for_timeout(2500)
  P('aucune écriture du collègue après retrait (vu par le propriétaire) :',pc.evaluate("!db.marches.some(m=>m.num=='APRES-RETRAIT')"))
  # 9) Code d'invitation réutilisé après retrait
  t3=dev('Tiers: ',True);enc(t3,'Tiers#Code2026xx');join(t3,inv);P('invitation retirée inutilisable :',t3.evaluate("SY===null&&db.marches.length==0"))
  # 10) Le propriétaire continue normalement
  pc.evaluate("db.marches.push({id:'m9',num:'PROPRIO-OK',_u:Date.now()});save()");pc.wait_for_timeout(3500);P('propriétaire synchronise toujours :','PROPRIO-OK'!='' and pc.evaluate("SY.last>0&&!SY.dc"))
  P('alertes :',[x for x in alerts if 'retir' in x.lower() or 'introuvable' in x.lower()][:4])
  P('erreurs :',[e for e in errs if 'status of 400' not in e])
  b.close()
