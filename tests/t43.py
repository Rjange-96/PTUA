import json
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
# Attaque systématique par données piégées (fichier importé ou données reçues par synchronisation) :
# CHAQUE champ de CHAQUE type de fiche reçoit du code, puis on parcourt tous les onglets, la recherche,
# les fenêtres de modification et les exports. Aucun code ne doit s'exécuter.
KINDS={  # contexte visé -> charge
 'html':  lambda t:f'<img src=x onerror="__h(\'{t}\')">',
 'attr':  lambda t:f'"><img src=x onerror="__h(\'{t}\')"><x y="',
 'attr1': lambda t:f"'><img src=x onerror=\"__h('{t}')\"><x y='",
 'js':    lambda t:f"');__h('{t}');('",
 'url':   lambda t:f"javascript:__h('{t}')",
 'svg':   lambda t:f'<svg/onload="__h(\'{t}\')">',
}
ENTS=['marches','garanties','os','avenants','assurances','reserves','reunions']
errs=[];hits=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path=__import__('shutil').which('google-chrome'))
  pg=b.new_context(viewport={'width':1280,'height':900}).new_page();pg.set_default_timeout(8000)
  pg.add_init_script("window.__h=t=>{(window.__hits=window.__hits||[]).push(String(t))};window.alert=window.confirm=()=>true;window.prompt=()=>null")
  pg.on('pageerror',lambda e:errs.append(str(e)[:160]))
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500);pg.evaluate("localStorage.clear()");pg.reload();pg.wait_for_timeout(2500)
  sch=pg.evaluate("Object.fromEntries(Object.keys(S).map(e=>[e,S[e].f.map(f=>f[0])]))")
  P('types de fiches couverts :',sorted(sch)==sorted(ENTS),sorted(sch))
  evil={e:[] for e in ENTS};n=0
  for k,mk in KINDS.items():
    for e in ENTS:
      r={'id':f'{e[:3]}{k}'}
      for f in sch[e]:
        r[f]='m1' if (f=='marche' and k=='html') else mk(f'{e}.{f}.{k}')
      for f in ('note','transcription','pv'):r.setdefault(f,mk(f'{e}.{f}.{k}'))
      evil[e].append(r);n+=1
  evil['marches'].append({'id':'m1','titulaire':KINDS['html']('m1.titulaire'),'num':'M-1','montant':'1000','debut':'2026-01-08','delaiM':'12'})
  evil['journal']=[{'d':KINDS[k]('journal.d.'+k),'m':KINDS[k]('journal.m.'+k),'t':1} for k in KINDS]
  pg.evaluate("ev=>{db=sanDB(ev);save()}",evil)
  P('fiches piégées chargées :',pg.evaluate("Object.values(db).filter(Array.isArray).reduce((a,x)=>a+x.length,0)")>=n)
  tabs=pg.evaluate("NAV.map(x=>x[0])")
  for t in tabs:
    pg.evaluate(f"go('{t}')");pg.wait_for_timeout(250)
  P('onglets parcourus :',len(tabs))
  # recherche globale sur un mot présent dans les charges
  pg.evaluate("go('search')");pg.wait_for_timeout(200)
  try:pg.evaluate("q='img';gq='img';render()");pg.wait_for_timeout(300)
  except Exception:pass
  # fenêtres de modification de chaque fiche
  ids=pg.evaluate("Object.fromEntries(%s.map(e=>[e,db[e].map(x=>x.id)]))"%json.dumps(ENTS))
  opened=0
  for e,L in ids.items():
    for i in L:
      try:
        pg.evaluate(f"go('{e}')");pg.evaluate("([e,i])=>edit(e,i)",[e,i]);pg.wait_for_timeout(60);opened+=1
        pg.evaluate("$('#df')?.open&&$('#df').close();$('#cd')?.open&&$('#cd').close()")
      except Exception as x:errs.append(f'edit {e} {i}: {str(x)[:80]}')
  P('fenêtres de modification ouvertes :',opened)
  # présentation : toutes les diapositives
  try:
    pg.evaluate("go('pres')");pg.wait_for_timeout(200)
    for _ in range(25):pg.keyboard.press('ArrowRight');pg.wait_for_timeout(30)
  except Exception:pass
  # thème sombre + impression (rendu différent)
  pg.evaluate("document.documentElement.dataset.t='dark';go('dash')");pg.wait_for_timeout(200)
  # cliquer sur tous les liens générés depuis les données
  hrefs=pg.evaluate("[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')).filter(h=>/^\\s*javascript:/i.test(h))")
  P('aucun lien javascript: affiché :',hrefs==[],hrefs[:3])
  pg.wait_for_timeout(500)
  hits=pg.evaluate("window.__hits||[]")
  P('code piégé exécuté :',len(hits),'| aucun :',hits==[],sorted(set(hits))[:10])
  b.close()
P('erreurs :',errs[:8])
