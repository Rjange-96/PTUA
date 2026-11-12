import json,sys
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
URL=sys.argv[1]
evil_backup={"marches":[{"id":"x');window.__p1=1;('","titulaire":"<img src=x onerror=window.__p0=1>","num":"M-1","montant":"1000"}],
 "garanties":[{"id":"g1","marche":"x');window.__p1=1;('","type":"Soumission","statut":"Active"}],"os":[],"avenants":[],"journal":[],
 "ref":{"v":"2026-11-11","base":"x","p":{"ret":[3,5],"gbe":[3,5],"av1":15,"av2":15,"avt":30,"pen":10,"mlGbe":15},"r":[],"applied":["evil"],"lc":"","url":"",
  "s":[["Lien piégé","javascript:window.__p4=1"]],
  "props":[{"id":"evil","op":"add","ent":"marches","after":"num","fs":[["zz\" onfocus=\"window.__p3=1\" autofocus x=\"","<img src=x onerror=window.__p2=1>","text"]],"title":"t","why":"w"}]}}
open('/tmp/evil.json','w').write(json.dumps(evil_backup))
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page();pg.set_default_timeout(6000)
  pg.on('dialog',lambda d:d.accept())
  pg.goto(URL);pg.wait_for_timeout(2300);pg.evaluate("localStorage.clear()")
  pg.set_input_files('#imp','/tmp/evil.json');pg.wait_for_timeout(800)
  if pg.evaluate("$('#cd')&&$('#cd').open"):pg.click('#cd .pri');pg.wait_for_timeout(500)
  for t in ['marches','garanties','veille']:
    pg.evaluate(f"go('{t}')");pg.wait_for_timeout(300)
  pg.evaluate("go('marches');$('#vp').hidden=false");pg.wait_for_timeout(200)
  try: pg.click('#tb button:has-text(\"Modifier\")',timeout=2000);pg.wait_for_timeout(300)
  except Exception as e: P('no modify btn')
  try: pg.evaluate("go('veille')");pg.click('a:has-text(\"Lien piégé\")',timeout=2000);pg.wait_for_timeout(300)
  except Exception as e: P('no evil link')
  try:
    pg.evaluate("go('marches')");pg.click('#tb button:has-text(\"Suppr\")',timeout=2000);pg.wait_for_timeout(300)
  except Exception as e: P('no del')
  P('PWNED flags:',pg.evaluate("[window.__p0,window.__p1,window.__p2,window.__p3,window.__p4]"))
  P('csv:',pg.evaluate("(()=>{let o='';const s=dl;dl=(n,t)=>o=t;db.marches=[{id:'a1',num:'=HYPERLINK(\"http://evil\",\"x\")',montant:'-500'}];tab='marches';expC();dl=s;return o.split('\\n')[1]})()"))
  b.close()
