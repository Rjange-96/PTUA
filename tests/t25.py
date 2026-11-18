import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page();pg.on('dialog',lambda d:d.accept())
  errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2000);pg.evaluate("localStorage.clear()")
  out=pg.evaluate("""async()=>{const e=new Date(Date.now()+20*864e5).toISOString().slice(0,10);
   db=sanDB({marches:[{id:'m1',num:'M;1,x',titulaire:'T'}],garanties:[{id:'g1',marche:'m1',type:'Soumission',statut:'Active',echeance:e,organisme:'ACME\\rATTACH:https://evil.example/x.exe\\rX-EVIL:1',montant:5}],os:[]});
   let o='';const s=offer;offer=(n,t)=>{o=t};choose=async()=>0;await icsExp();offer=s;return o}""")
  lines=[l for l in __import__('re').split(r'\r\n|\r|\n',out)]
  print('ligne ATTACH injectée :',any(l.startswith('ATTACH:') for l in lines),'| X-EVIL :',any(l.startswith('X-EVIL') for l in lines))
  print('point-virgule échappé :',r'M\;1\,x' in out)
  print('erreurs :',errs);b.close()
