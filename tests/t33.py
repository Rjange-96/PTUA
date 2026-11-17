# v9.10/v9.12 — Réunions : enregistrement audio, transcription et PV automatiques (IA),
# avec relance automatique (sans bouton) en cas de panne du service de transcription.
# Le micro est simulé par Chrome (--use-fake-device-for-media-stream) ; l'edge function
# agent-pv est simulée comme le serveur Supabase (aucun appel réseau réel).
import json,hashlib
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
DB={};errs=[];PVCALLS=[];MODE={'m':'ok'}
def handle(route):
  req=route.request
  if '/functions/v1/agent-pv' in req.url:
    a=json.loads(req.post_data or '{}');PVCALLS.append(a)
    row=DB.get(a.get('id'));ok=bool(row and row['h']==hashlib.sha256(a.get('auth','').encode()).hexdigest())
    if not ok:return route.fulfill(status=401,content_type='application/json',body='{"error":"Accès refusé"}')
    if a.get('mime') not in ('audio/webm','audio/mp4','audio/ogg','audio/aac'):return route.fulfill(status=400,content_type='application/json',body='{"error":"Format audio non pris en charge"}')
    if MODE['m']=='down':return route.fulfill(status=500,content_type='application/json',body='{"error":"La transcription a échoué (audio illisible ou service indisponible)"}')
    return route.fulfill(status=200,content_type='application/json',body=json.dumps({'transcription':'Bonjour à tous. <img src=x onerror=window.__x=1> Nous avons discuté du planning.','pv':'OBJET DE LA RÉUNION:\nRéunion de chantier test\n\nDÉCISIONS PRISES:\n- Valider le planning'}))
  a=json.loads(req.post_data or '{}');fn=req.url.split('/rpc/')[1]
  h=hashlib.sha256(a.get('p_auth','').encode()).hexdigest();row=DB.get(a.get('p_id'));ok=bool(row and row['h']==h)
  if fn=='ptua_get':out=[{'ver':row['ver'],'blob':row['blob']}] if ok else []
  elif fn=='ptua_put' and a['p_ver']==0:
    out=-1 if row else 1
    if not row:DB[a['p_id']]={'h':h,'ver':1,'blob':a['p_blob']}
  elif fn=='ptua_put' and ok and row['ver']==a['p_ver']:row['ver']+=1;row['blob']=a['p_blob'];out=row['ver']
  elif fn=='ptua_put':out=-1
  elif fn=='ptua_file_put':out=True
  elif fn=='ptua_file_get':out=None
  else:out=[]
  route.fulfill(status=200,content_type='application/json',body=json.dumps(out))
with sync_playwright() as p:
  b=p.chromium.launch(executable_path=__import__('shutil').which('google-chrome'),args=['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream'])
  c=b.new_context(viewport={'width':1280,'height':900},permissions=['microphone'])
  pg=c.new_page();pg.set_default_timeout(15000)
  pg.route('https://iofbwpzhptctyelmylkz.supabase.co/**',handle)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and 'Failed to load resource' not in m.text and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2300)
  P('onglet « Réunions » présent, icône, pas dans la navigation mobile principale :',pg.evaluate("NAV.some(n=>n[0]=='reunions')"),pg.evaluate("!!ic('reunions')"),not pg.evaluate("PRIM.includes('reunions')"))
  pg.evaluate("setTimeout(pinMenu,0)");pg.wait_for_timeout(300)
  pg.fill('#cd input[name=a]','Test#Reunion2026');pg.fill('#cd input[name=b]','Test#Reunion2026');pg.click('#cd .pri');pg.wait_for_timeout(2500)
  pg.evaluate("setTimeout(syStart,0)");pg.wait_for_timeout(400);pg.click('#cd .pri');pg.wait_for_timeout(2500);pg.click('#cd .pri');pg.wait_for_timeout(500)
  pg.evaluate("db.marches.push({id:'m1',num:'2026-0042',titulaire:'T'});save();0")
  pg.evaluate("go('reunions')");pg.wait_for_timeout(300)
  P('1) liste vide au départ :',pg.evaluate("$('#v').textContent.includes('Aucune réunion')"))
  # 2) Enregistrement : chrono, champs désactivés, arrêt, sauvegarde
  pg.click('button:has-text(\"Nouvelle réunion\")');pg.wait_for_timeout(200)
  pg.fill('#rvo','Réunion de chantier test');pg.select_option('#rvm','m1');pg.fill('#rvp','Jean, Marie')
  pg.click('#rvb');pg.wait_for_timeout(1200)
  try:pg.wait_for_function("$('#rvtimer').textContent!='00:00'",timeout=5000)  # machine chargée : le 1er tic peut tarder
  except Exception:pass
  P('2) enregistrement démarré : chrono actif, champs verrouillés :',pg.evaluate("$('#rvtimer').textContent")!='00:00',pg.evaluate("$('#rvo').disabled"))
  pg.wait_for_timeout(1200);pg.click('#rvb');pg.wait_for_timeout(3000)
  P('2) dialogue fermé, réunion créée (statut initial transcription ou déjà terminé) :',not pg.evaluate("$('#cd').open"),pg.evaluate("db.reunions.length==1"),pg.evaluate("['Transcription en cours','Terminé'].includes(db.reunions[0].statut)"))
  for _ in range(20):
    pg.wait_for_timeout(300)
    if pg.evaluate("db.reunions[0].statut")!='Transcription en cours':break
  P('3) transcription terminée automatiquement, sans ouvrir de fenêtre bloquante :',pg.evaluate("db.reunions[0].statut")=='Terminé')
  P('3) mime audio envoyé reconnu par le serveur :',PVCALLS and PVCALLS[0]['mime'] in ('audio/webm','audio/mp4','audio/ogg','audio/aac'))
  P('3) objet/marché/participants transmis en contexte :',PVCALLS and PVCALLS[0]['objet']=='Réunion de chantier test' and PVCALLS[0]['participants']=='Jean, Marie')
  rid=pg.evaluate("db.reunions[0].id")
  pg.evaluate("go('reunions')");pg.wait_for_timeout(300)
  P('4) badge « Terminé » affiché dans la liste :',pg.evaluate("$('#v').textContent.includes('Terminé')"))
  # 5) Lecture du PV : généré, éditable, contenu XSS neutralisé à l'affichage
  pg.evaluate(f"revOpen('{rid}')");pg.wait_for_timeout(300);pg.click('[data-a=\"pv\"]');pg.wait_for_timeout(300)
  P('5) PV affiché dans l’éditeur avec les sections générées :',pg.evaluate("$('#cot').value").find('DÉCISIONS')>=0)
  pg.evaluate("$('#cd').close()")
  pg.evaluate(f"revOpen('{rid}')");pg.wait_for_timeout(300);pg.click('[data-a=\"tx\"]');pg.wait_for_timeout(300)
  P('5) transcription brute affichée, XSS non exécuté :',pg.evaluate("$('#cot').value").find('Bonjour')>=0,not pg.evaluate("window.__x"))
  pg.evaluate("$('#cd').close()")
  # 6) Panne du service : relance automatique sans bouton, puis succès dès que le service revient
  MODE['m']='down'
  pg.evaluate("go('reunions')");pg.wait_for_timeout(300);pg.click('button:has-text(\"Nouvelle réunion\")');pg.wait_for_timeout(200)
  pg.click('#rvb');pg.wait_for_timeout(1000);pg.click('#rvb');pg.wait_for_timeout(2500)
  rid2=pg.evaluate("db.reunions[1].id")
  for _ in range(20):
    pg.wait_for_timeout(300)
    if pg.evaluate(f"db.reunions.find(r=>r.id=='{rid2}').retries")>=1:break
  P('6) après une panne : statut reste « Transcription en cours » (pas « Erreur »), compteur de tentatives incrémenté :',pg.evaluate(f"db.reunions.find(r=>r.id=='{rid2}').statut")=='Transcription en cours',pg.evaluate(f"db.reunions.find(r=>r.id=='{rid2}').retries")>=1)
  pg.evaluate(f"revOpen('{rid2}')");pg.wait_for_timeout(200)
  P('6) aucun bouton « Relancer » proposé (relance automatique uniquement), message rassurant affiché :',not pg.evaluate("!!document.querySelector('[data-a=\"retry\"]')"),pg.evaluate("$('#cd').textContent").find('tentative automatique')>=0)
  pg.evaluate("$('#cd').close()")
  MODE['m']='ok'
  pg.evaluate(f"pvProcess('{rid2}')");pg.wait_for_timeout(1500)
  for _ in range(20):
    pg.wait_for_timeout(300)
    if pg.evaluate(f"db.reunions.find(r=>r.id=='{rid2}').statut")!='Transcription en cours':break
  P('6) dès que le service répond de nouveau : Terminé, compteur de tentatives remis à zéro :',pg.evaluate(f"db.reunions.find(r=>r.id=='{rid2}').statut")=='Terminé',pg.evaluate(f"db.reunions.find(r=>r.id=='{rid2}').retries")==0)
  # 6bis) abandon définitif après plusieurs échecs, sans jamais perdre l'audio ; reprise automatique
  # à la réouverture de l'application (pvRescan), sans action de l'utilisateur
  MODE['m']='down'
  pg.evaluate("go('reunions')");pg.wait_for_timeout(300);pg.click('button:has-text(\"Nouvelle réunion\")');pg.wait_for_timeout(200)
  pg.click('#rvb');pg.wait_for_timeout(800);pg.click('#rvb');pg.wait_for_timeout(2000)
  rid3=pg.evaluate("db.reunions[2].id")
  pg.evaluate(f"(async()=>{{for(let i=0;i<10&&db.reunions.find(r=>r.id=='{rid3}').statut!='Erreur';i++)await pvProcess('{rid3}')}})()")
  for _ in range(30):
    pg.wait_for_timeout(300)
    if pg.evaluate(f"db.reunions.find(r=>r.id=='{rid3}').statut")=='Erreur':break
  P('6bis) abandon définitif après plusieurs échecs, audio toujours présent :',pg.evaluate(f"db.reunions.find(r=>r.id=='{rid3}').statut")=='Erreur',pg.evaluate(f"db.reunions.find(r=>r.id=='{rid3}').files.length")==1)
  MODE['m']='ok'
  pg.evaluate("pvRescan()")
  for _ in range(20):
    pg.wait_for_timeout(300)
    if pg.evaluate(f"db.reunions.find(r=>r.id=='{rid3}').statut")=='Terminé':break
  P('6bis) reprise automatique au redémarrage de l’application (pvRescan), sans intervention :',pg.evaluate(f"db.reunions.find(r=>r.id=='{rid3}').statut")=='Terminé')
  # 7) Écoute / téléchargement de l'audio d'origine
  pg.evaluate(f"revOpen('{rid2}')");pg.wait_for_timeout(300)
  P('7) boutons écoute/téléchargement de l’audio proposés :',pg.evaluate("!!document.querySelector('[data-a=\"play\"]')&&!!document.querySelector('[data-a=\"dl\"]')"))
  pg.evaluate("$('#cd').close()")
  # 8) Verrouillage pendant un enregistrement en cours : micro coupé, rien de perdu de façon incohérente
  pg.evaluate("go('reunions')");pg.wait_for_timeout(300);pg.click('button:has-text(\"Nouvelle réunion\")');pg.wait_for_timeout(200)
  pg.click('#rvb');pg.wait_for_timeout(800)
  before=pg.evaluate("!!(REC&&REC.mr&&REC.mr.state!='inactive')")
  pg.evaluate("lock()");pg.wait_for_timeout(300)
  P('8) enregistrement actif avant verrouillage, proprement abandonné après (micro coupé, dialogue fermé) :',before,pg.evaluate("REC===null"),not pg.evaluate("$('#cd').open"))
  # 9) suppression d'une réunion : fiche + document retirés, pas de doublon de garanties/marchés
  pg.fill('#pin','Test#Reunion2026');pg.evaluate("setTimeout(unl,0)");pg.wait_for_timeout(1000)
  n0=pg.evaluate("db.reunions.length")
  pg.evaluate("go('reunions')");pg.wait_for_timeout(300)
  pg.evaluate(f"del('reunions','{rid}')")
  P('9) suppression d’une réunion : une de moins, pas d’effet sur les marchés :',pg.evaluate("db.reunions.length")==n0-1,pg.evaluate("db.marches.length")==1)
  # 10) suppression du marché lié : la réunion restante garde son historique mais perd le lien (pas de suppression en cascade)
  pg.evaluate("del('marches','m1')")
  P('10) marché supprimé : réunion restante conservée, lien marché effacé (pas de cascade) :',pg.evaluate("db.reunions.length")==n0-1,pg.evaluate("db.reunions[0]&&db.reunions[0].marche")=='')
  P('erreurs :',[e for e in errs if 'net::ERR' not in e][:8])
  b.close()
