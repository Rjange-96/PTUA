from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  pg=b.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True).new_page();pg.set_default_timeout(6000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2300);pg.evaluate("localStorage.clear()");pg.reload();pg.wait_for_timeout(2300)
  pg.evaluate("""()=>{db.marches.push({id:'m1',titulaire:'SOGEA',num:'2024-0153',montant:'850000000',debut:'2026-01-08',delaiM:'12'});
   db.garanties.push({id:'g1',marche:'m1',type:'Bonne exécution',organisme:'NSIA',montant:'42500000',echeance:'2026-12-30',statut:'Active'});save()}""")
  for t in ['dash','pres','search','marches','garanties','os','avenants','stats','veille','sauv','amel','journal']:
    pg.evaluate(f"go('{t}')");pg.wait_for_timeout(150)
  P('all tabs rendered, errors so far:',len(errs))
  pg.evaluate("window._f=null;dl=(n,t)=>{window._f=t};setTimeout(expJ,0)");pg.wait_for_timeout(300)
  pg.fill('#cd input[name=a]','Sauvegarde!2026');pg.fill('#cd input[name=b]','Sauvegarde!2026');pg.click('#cd .pri');pg.wait_for_timeout(2500);pg.click('#cd .pri');pg.wait_for_timeout(300)
  f=pg.evaluate("window._f");P('export chiffré:','SOGEA' not in f and '"ct"' in f,'date export enregistrée:',pg.evaluate("!!localStorage.getItem('ptua_exp')"))
  pg.evaluate("""(t)=>{db.marches=[];db.garanties=[];const dt=new DataTransfer();dt.items.add(new File([t],'s.json'));$('#imp').files=dt.files;impJ($('#imp'))}""",f);pg.wait_for_timeout(500)
  pg.fill('#cd input[name=p]','Sauvegarde!2026');pg.click('#cd .pri');pg.wait_for_timeout(2500)
  P('import chiffré:',pg.evaluate("db.marches[0].titulaire+' / lien garantie ok: '+(db.garanties[0].marche==db.marches[0].id)"))
  pg.evaluate("window._f=null;setTimeout(icsExp,0)");pg.wait_for_timeout(300);pg.click('#cd .pri');pg.wait_for_timeout(300);pg.click('#cd .pri');pg.wait_for_timeout(300)
  P('ics:',(pg.evaluate("window._f") or '').count('BEGIN:VEVENT'),'événements')
  P('errors:',errs)
  b.close()
