import json,re
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
# Un seul numéro de version partout : application, en-tête, onglet du navigateur, cache hors ligne, avis de mise à jour.
html=open('index.html',encoding='utf-8').read();sw=open('sw.js',encoding='utf-8').read();vj=json.load(open('version.json',encoding='utf-8'))
appv=re.search(r"const APPV='([^']+)'",html).group(1)
src={'version.json':vj['version'],'sw.js':re.search(r"const V='([^']+)'",sw).group(1),
 '<title>':re.search(r'<title>[^<]*PTUA v([0-9.]+)</title>',html).group(1)}
P('APPV :',appv)
P('versions cohérentes (fichiers) :',all(v==appv for v in src.values()),src)
P('notes de version.json en liste :',isinstance(vj.get('notes'),list) and len(vj['notes'])>0)
P('aucune version figée dans le code :',re.findall(r"PTUA v[0-9]+\.[0-9]+'",html)==[])
errs=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path=__import__('shutil').which('google-chrome'));pg=b.new_page()
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500)
  P('en-tête affiché :',pg.evaluate("$('#av')?.textContent"),'| à jour :',pg.evaluate("$('#av')?.textContent")=='v'+appv)
  P('titre de l’onglet :',pg.title(),'| à jour :',pg.title().endswith('v'+appv))
  pg.evaluate("localStorage.clear()");pg.reload();pg.wait_for_timeout(2300)
  pg.evaluate("db.marches.push({id:'m1',titulaire:'SOGEA',num:'2024-0153',montant:'1000',debut:'2026-01-08',delaiM:'48'});db.garanties.push({id:'g1',marche:'m1',type:'Bonne exécution',organisme:'NSIA',montant:'1',echeance:'2099-12-30',statut:'Active'});save()")
  pg.on('dialog',lambda d:d.accept())
  pg.evaluate("window._f=null;offer=(n,t)=>{window._f=t};setTimeout(icsExp,0)");pg.wait_for_timeout(300)
  for _ in range(2):
    if pg.evaluate("!!$('#cd')?.open"):pg.click('#cd .pri');pg.wait_for_timeout(300)
  f=pg.evaluate("window._f") or ''
  P('calendrier .ics : PRODID v'+appv+' :',('PRODID:-//PTUA//Gestionnaire PTUA v'+appv+'//FR') in f)
  # Notes de mise à jour : liste ou simple phrase doivent toutes deux s'afficher.
  for kind,notes in (('liste',['Nouveauté A','Nouveauté B']),('phrase','Nouveauté unique')):
    pg.route('**/version.json*',lambda r,_q=None,n=notes:r.fulfill(status=200,content_type='application/json',body=json.dumps({'version':'99.0','date':'2026-11-17','importance':'normale','notes':n})))
    pg.evaluate("localStorage.removeItem('ptua_upd');window.UPD=null");pg.evaluate("chkUpd(false)");pg.wait_for_timeout(800)
    P('notes de mise à jour ('+kind+') affichées :',pg.evaluate("(()=>{const u=JSON.parse(localStorage.getItem('ptua_upd')||'null');return !!u&&u.notes.length>0&&u.notes.every(x=>x.startsWith('Nouveauté'))})()"))
    pg.unroute('**/version.json*')
  b.close()
P('erreurs :',errs)
