# v9.6 — Compression et découpage automatiques des gros PDF (sans question, sans limite de 600 pages, enregistrement au fil de l'eau)
# Prérequis : python3 tests/t28_gen.py (crée a12.pdf, b700.pdf et scan15.pdf dans /tmp/claude-0/pdf)
import sys,os
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
D=sys.argv[1] if len(sys.argv)>1 else '/tmp/claude-0/pdf'
errs=[];alerts=[];chooses=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page();pg.set_default_timeout(15000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:(alerts.append(d.message),d.accept()))
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2300);pg.evaluate("localStorage.clear()");pg.reload();pg.wait_for_timeout(2300)
  pg.evaluate("db.marches.push({id:'m1',num:'M-1',titulaire:'T'},{id:'m2',num:'M-2',titulaire:'T2'});db.garanties.push({id:'g1',marche:'m1',type:'Soumission',statut:'Active'});save();window.__ch=0;const c0=choose;choose=(...a)=>{window.__ch++;return c0(...a)};0")
  def attach(e,i,f,wait_s):
    pg.evaluate(f"go('{e}');edit('{e}','{i}')");pg.wait_for_timeout(300);pg.set_input_files('#fa',f);pg.evaluate("ok()")
    pg.wait_for_timeout(500)
    for _ in range(wait_s*2):
      pg.wait_for_timeout(500)
      if not pg.evaluate("JOB.run"):break
    m=pg.evaluate("JOB.msg?JOB.msg.t+'\\n'+JOB.msg.d:''")
    if m:alerts.append(m)
  def check(e,i):
    return pg.evaluate("""async([e,i])=>{const x=db[e].find(z=>z.id==i),L=await pdfLib();let pages=0,mx=0,names=[];for(const f of x.files||[]){const b=await fLoad(f);mx=Math.max(mx,b.length);names.push(f.n);if(f.t=='application/pdf'){const d=await L.getDocument({data:b,isEvalSupported:false}).promise;pages+=d.numPages;d.destroy()}}return{n:(x.files||[]).length,pages,mx,first:names[0],last:names[names.length-1]}}""",[e,i])
  # A) 9 Mo, 12 pages : aucune question, compression et découpage automatiques
  alerts.clear();attach('marches','m1',D+'/a12.pdf',120);r=check('marches','m1')
  P('A) aucune question posée :',pg.evaluate("window.__ch")==0,'| pages conservées :',r['pages'],'/ 12 | parties :',r['n'],'| plus grosse partie ≤ 3,4 Mo :',r['mx']<=3.4e6,'| nom :',r['first'])
  P('   message :',(alerts[-1] if alerts else '').replace('\n',' | ')[:160])
  # A2) document de type scan : reste en couleur, fortement allégé
  pg.evaluate("db.marches.push({id:'m4',num:'M-4'});save()");alerts.clear();attach('marches','m4',D+'/scan15.pdf',120);r=check('marches','m4')
  P('A2) scan 10 Mo : pages',r['pages'],'/ 15 | reste en couleur :',not any('noir et blanc' in a for a in alerts),'|',(alerts[-1] if alerts else '').split('\n')[0])
  # B) 56 Mo, 700 pages : auparavant refusé (> 600 pages)
  alerts.clear();attach('marches','m2',D+'/b700.pdf',600);r=check('marches','m2')
  P('B) 700 pages acceptées :',r['pages']==700,'(',r['pages'],') | parties :',r['n'],'≤ 60 :',r['n']<=60,'| plus grosse ≤ 3,4 Mo :',r['mx']<=3.4e6,'| dernière :',r['last'])
  P('   message :',(alerts[-1] if alerts else '').replace('\n',' | ')[:200])
  # C) fiche presque pleine (58 documents) : les 2 places restantes sont remplies, la suite est signalée
  pg.evaluate("""(async()=>{const g=db.garanties[0];g.files=[];for(let i=0;i<58;i++){const en=await fEnc(new Uint8Array([1,2,3]));const id='fz'+i;await fPut(id,en.data);g.files.push({id,n:'x.jpg',t:'image/jpeg',s:3,d:Date.now(),k:en.k})}save()})()""");pg.wait_for_timeout(1500)
  alerts.clear();attach('garanties','g1',D+'/b700.pdf',600)
  n=pg.evaluate("db.garanties[0].files.length");P('C) fiche pleine gérée :',n==60,'| message :',[a for a in alerts if 'pleine' in a][:1] and 'oui','|',(alerts[-1] if alerts else '').split('⚠️')[-1].strip()[:120])
  # D) bouton Arrêter
  pg.evaluate("db.marches.push({id:'m3',num:'M-3'});save()");alerts.clear()
  pg.evaluate("go('marches');edit('marches','m3')");pg.wait_for_timeout(300);pg.set_input_files('#fa',D+'/b700.pdf');pg.evaluate("ok()")
  for _ in range(60):
    pg.wait_for_timeout(500)
    if pg.evaluate("!!$('#job [data-j=s]')&&/partie/.test($('#job').textContent)"):break
  P('   bouton Arrêter affiché :',pg.evaluate("!!$('#job [data-j=s]')"),'| estimation affichée :',pg.evaluate("$('#job .jd').textContent")[:110])
  pg.click('#job [data-j=s]')
  for _ in range(60):
    pg.wait_for_timeout(500)
    if not pg.evaluate("JOB.run"):break
  m=pg.evaluate("JOB.msg?JOB.msg.d:''")
  if m:alerts.append(m)
  r=check('marches','m3');P('D) arrêt : pages déjà traitées conservées :',r['pages']>0 and r['pages']<700,'(',r['pages'],') | message :',[a for a in alerts if 'arrêtée' in a][:1] and 'oui')
  # E) petit PDF et photo inchangés
  pg.evaluate("""(async()=>{const c=document.createElement('canvas');c.width=c.height=50;const bl=await new Promise(r=>c.toBlob(r,'image/jpeg',.9));addFiles('marches','m3',[new File([bl],'photo.jpg',{type:'image/jpeg'}),new File([mkPdf([{w:8,h:8,pw:8,ph:8,bytes:new Uint8Array(await bl.arrayBuffer())}])],'petit.pdf',{type:'application/pdf'})])})()""");pg.wait_for_timeout(3500)
  P('E) photo et petit PDF joints tels quels :',pg.evaluate("db.marches.find(m=>m.id=='m3').files.slice(-2).map(f=>f.n).join(' + ')"))
  P('erreurs :',errs[:5]);b.close()
