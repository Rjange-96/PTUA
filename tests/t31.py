# v9.9 — Garantie de performance environnementale et sociale + modèles de courrier personnels (Word .docx / PDF)
# Prérequis : python3 tests/t31_gen.py (crée les fichiers de test dans /tmp/claude-0/tpl)
import json,hashlib,io
from playwright.sync_api import sync_playwright
from docx import Document
def P(*a):print(*a,flush=True)
DB={};FILES={};errs=[];alerts=[];T='/tmp/claude-0/tpl';GP='Performance environnementale et sociale'
H=lambda x:hashlib.sha256(x.encode()).hexdigest()
def handle(route):
  req=route.request;fn=req.url.split('/rpc/')[1];a=json.loads(req.post_data or '{}');row=DB.get(a.get('p_id'));ok=bool(row and row['h']==H(a.get('p_auth','')))
  if fn=='ptua_get':out=[{'ver':row['ver'],'blob':row['blob'],'updated_at':''}] if ok else []
  elif fn=='ptua_put':
    if a['p_ver']==0:
      out=-1 if row else 1
      if not row:DB[a['p_id']]={'h':H(a['p_auth']),'ver':1,'blob':a['p_blob']}
    elif ok and row['ver']==a['p_ver']:row['ver']+=1;row['blob']=a['p_blob'];out=row['ver']
    else:out=-1
  elif fn=='ptua_file_put':FILES[(a['p_id'],a['p_fid'])]=a['p_blob'];out=True
  elif fn=='ptua_file_get':out=FILES.get((a['p_id'],a['p_fid'])) if ok else None
  elif fn=='ptua_file_del':FILES.pop((a['p_id'],a['p_fid']),None);out=ok
  else:out=[]
  route.fulfill(status=200,content_type='application/json',body=json.dumps(out))
with sync_playwright() as p:
  b=p.chromium.launch(executable_path=__import__('shutil').which('google-chrome'))
  def dev(name):
    c=b.new_context(viewport={'width':1280,'height':850},accept_downloads=True);pg=c.new_page();pg.set_default_timeout(15000);pg.route('https://iofbwpzhptctyelmylkz.supabase.co/**',handle)
    pg.on('pageerror',lambda e:errs.append(name+str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(name+m.text));pg.on('dialog',lambda d:(alerts.append(d.message),d.accept()))
    pg.goto('http://localhost:8765/');pg.wait_for_timeout(2300)
    pg.evaluate("setTimeout(pinMenu,0)");pg.wait_for_timeout(300);pg.fill('#cd input[name=a]','Test#Modeles2026');pg.fill('#cd input[name=b]','Test#Modeles2026');pg.click('#cd .pri');pg.wait_for_timeout(2500);return pg
  pc=dev('PC: ')
  pc.evaluate("db.marches.push({id:'m1',num:'2026-0042',titulaire:'Entreprise Démo (fictive)',objet:'Assainissement',montant:'300000000',debut:'2026-02-01',delaiM:'8'});save();render();0")
  # 1) nouveau type de garantie
  pc.evaluate("go('garanties');edit('garanties')");pc.wait_for_timeout(300)
  P('type proposé :',GP in pc.evaluate("[...$('#df select[name=type]').options].map(o=>o.value)"))
  pc.select_option('#df select[name=marche]','m1');pc.select_option('#df select[name=type]',GP);pc.fill('#df input[name=organisme]','Banque Démo Verte');pc.fill('#df input[name=montant]','15000000');pc.fill('#df input[name=echeance]','2027-03-31');pc.click('#dlg .pri');pc.wait_for_timeout(400)
  gid=pc.evaluate(f"db.garanties.find(g=>g.type=='{GP}').id");P('garantie enregistrée :',bool(gid))
  for t in ['dash','garanties','conf','stats','pres','search','veille']:pc.evaluate(f"go('{t}')")
  P('onglets (tableau de bord, conformité, statistiques, présentation) sans erreur :',not errs)
  pc.evaluate("db.garanties.push({id:'gx',marche:'m1',type:'Type d’une version future',statut:'Active'});save();edit('garanties','gx')");pc.wait_for_timeout(300);pc.click('#dlg .pri');pc.wait_for_timeout(300)
  P('type inconnu conservé à l’enregistrement :',pc.evaluate("db.garanties.find(g=>g.id=='gx').type"))
  # 2) ajout de modèles
  def add(f,i):
    alerts.clear();pc.evaluate("setTimeout(tplList,0)");pc.wait_for_timeout(300);pc.set_input_files('#tpf',f);pc.wait_for_timeout(1500)
    if i is not None and pc.evaluate("$('#cd').open&&!!$('#cd button[data-i]')"):pc.click(f'#cd button[data-i="{i}"]');pc.wait_for_timeout(1500)
    pc.evaluate("$('#cd').open&&$('#cd').close()");return alerts[-1] if alerts else ''
  m=add(T+'/modele.docx',2);P('Word ajouté :','ajouté' in m,'|',m.replace('\n',' | ')[:200])
  m=add(T+'/modele.pdf',0);P('PDF ajouté :','ajouté' in m,'|',m.replace('\n',' | ')[:160])
  P('.doc refusé :','.docx' in add(T+'/ancien.doc',None),'| faux Word refusé :','refusé' in add(T+'/faux.docx',None),'| fichier piégé (bombe) refusé :','volumineux' in add(T+'/bombe.docx',None))
  P('modèles enregistrés :',pc.evaluate("db.tpl.map(t=>t.nom+' ('+t.ent+')').join(', ')"))
  # 3) utilisation : Word rempli
  pc.evaluate(f"setTimeout(()=>cour('garanties','{gid}'),0)");pc.wait_for_timeout(400)
  opts=pc.evaluate("[...$('#cd').querySelectorAll('button[data-i]')].map(b=>b.textContent)");P('modèles proposés pour la garantie :',[o for o in opts if 'mon modèle' in o])
  i=[k for k,o in enumerate(opts) if 'modele' in o and '📝' in o][0];pc.click(f'#cd button[data-i="{i}"]');pc.wait_for_timeout(2500)
  tx=pc.evaluate("$('#cot').value");P('texte rempli :','2026-0042' in tx and 'Banque Démo Verte' in tx and GP in tx and '15 000 000' in tx.replace(' ',' ').replace('\xa0',' '),'| champs non remplacés :',[x for x in ['{{numero_marche}}','{{organisme}}'] if x in tx],'| champ inconnu laissé :','{{inconnu}}' in tx)
  with pc.expect_download() as dw:pc.click('#cd [data-v="x"]')
  path=dw.value.path();doc=Document(path);body='\n'.join(p.text for p in doc.paragraphs)+'\n'+'\n'.join(c.text for r in doc.tables[0].rows for c in r.cells);hd=doc.sections[0].header.paragraphs[0].text
  P('Word (mise en page du modèle) :','2026-0042' in body and 'Banque Démo Verte' in body and 'Entreprise Démo' in body,'| en-tête rempli :','{{' not in hd and '2026' in hd,'| tableau rempli :','Banque Démo Verte' in doc.tables[0].rows[0].cells[1].text,'| gras conservé :',any(r.bold for p in doc.paragraphs for r in p.runs if 'gras' in r.text))
  pc.evaluate("$('#cd').close()")
  # 4) utilisation : PDF rempli (sur un marché)
  pc.evaluate("setTimeout(()=>cour('marches','m1'),0)");pc.wait_for_timeout(400)
  opts=pc.evaluate("[...$('#cd').querySelectorAll('button[data-i]')].map(b=>b.textContent)");i=[k for k,o in enumerate(opts) if '📄' in o and 'mon modèle' in o][0];pc.click(f'#cd button[data-i="{i}"]');pc.wait_for_timeout(2500)
  tx=pc.evaluate("$('#cot').value");P('PDF rempli :','2026-0042' in tx and 'Entreprise Démo' in tx and '{{' not in tx,'|',tx.replace('\n',' | ')[:120]);pc.evaluate("$('#cd').close()")
  P('Word non proposé pour un marché (modèle réservé aux garanties) :',not any('📝' in o for o in opts))
  # 5) synchronisation vers un 2e appareil
  pc.evaluate("setTimeout(syStart,0)");pc.wait_for_timeout(300);pc.click('#cd .pri');pc.wait_for_timeout(2500);key=pc.evaluate("SY.code");pc.click('#cd .pri');pc.wait_for_timeout(500);pc.evaluate("fSync()");pc.wait_for_timeout(2500)
  ph=dev('iPhone: ');ph.evaluate("setTimeout(syStart,0)");ph.wait_for_timeout(300);ph.click('#cd button[data-i="2"]');ph.wait_for_timeout(300);ph.fill('#syc',key);ph.click('#cd .pri');ph.wait_for_timeout(3500)
  P('2e appareil : modèles reçus :',ph.evaluate("db.tpl.length"))
  ph.evaluate(f"setTimeout(()=>cour('garanties','{gid}'),0)");ph.wait_for_timeout(400);opts=ph.evaluate("[...$('#cd').querySelectorAll('button[data-i]')].map(b=>b.textContent)");i=[k for k,o in enumerate(opts) if '📝' in o][0];ph.click(f'#cd button[data-i="{i}"]');ph.wait_for_timeout(3000)
  P('2e appareil : modèle Word utilisable :','Banque Démo Verte' in ph.evaluate("$('#cot')?.value||''"));ph.evaluate("$('#cd').close()")
  # 6) retrait d'un modèle -> propagé
  pc.evaluate("setTimeout(tplList,0)");pc.wait_for_timeout(300);pc.click('#cd [data-x]');pc.wait_for_timeout(3500);ph.evaluate("syncNow()");ph.wait_for_timeout(2500)
  P('retrait propagé :',pc.evaluate("db.tpl.length"),'/',ph.evaluate("db.tpl.length"))
  # 7) import JSON : les modèles ne sont pas perdus
  P('remplacement des données (import) conserve les modèles :',pc.evaluate("(()=>{const n=db.tpl.length,d=replaceAll(sanDB(JSON.parse(JSON.stringify(db))));return d.tpl.length==n&&!d.tpl.some(t=>d.fdel[t.f.id])})()"))
  # 8) nom piégé
  pc.evaluate("db.tpl.push({...db.tpl[0],id:'tz',nom:'<img src=x onerror=window.__x=1>'});db.tpl=sanTpl(db.tpl);setTimeout(tplList,0)");pc.wait_for_timeout(400);P('nom piégé neutralisé :',pc.evaluate("!window.__x"))
  P('erreurs :',[e for e in errs if 'status of 400' not in e][:5]);b.close()
