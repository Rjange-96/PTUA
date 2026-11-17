# v9.8 — Thèmes : Classique clair/sombre, Ninja, Pirate ; choix mémorisé ; aucune erreur dans les onglets ; contraste des textes principaux
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[]
def L(c):
  r,g,b=[x/255 for x in c[:3]];f=lambda x:x/12.92 if x<=0.03928 else ((x+0.055)/1.055)**2.4;return .2126*f(r)+.7152*f(g)+.0722*f(b)
def C(a,b):x,y=sorted([L(a),L(b)],reverse=True);return (x+.05)/(y+.05)
with sync_playwright() as p:
  b=p.chromium.launch(executable_path=__import__('shutil').which('google-chrome'));pg=b.new_page(viewport={'width':1280,'height':800})
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2300);pg.evaluate("localStorage.clear();db.marches.push({id:'m1',num:'M-1',titulaire:'T'});save();render()")
  pg.click('#th');pg.wait_for_timeout(300);opts=pg.evaluate("[...$('#cd').querySelectorAll('button')].map(b=>b.textContent)");P('choix proposés :',opts[:4])
  pg.click('#cd button[data-i="2"]');pg.wait_for_timeout(300);P('Ninja appliqué :',pg.evaluate("document.documentElement.dataset.s"))
  pg.reload();pg.wait_for_timeout(2300);P('Ninja mémorisé après redémarrage :',pg.evaluate("document.documentElement.dataset.s"))
  rgb=lambda js:[int(x) for x in __import__('re').findall(r'[\d.]+',pg.evaluate(js))[:3]]
  for k in ['ninja','pirate','clair','sombre']:
    pg.evaluate(f"thSet('{k}')");pg.wait_for_timeout(200)
    for t in ['dash','marches','garanties','assurances','conf','os','avenants','search','stats','pres','veille','sauv','act','cyber','amel','journal']:pg.evaluate(f"go('{t}')")
    pg.evaluate("go('dash')");pg.wait_for_timeout(200)
    c1=C(rgb("getComputedStyle($('.card h2')).color"),rgb("getComputedStyle($('.card')).backgroundColor"))
    c2=C(rgb("getComputedStyle($('header h1')).webkitTextFillColor||getComputedStyle($('header h1')).color"),rgb("getComputedStyle($('header')).backgroundColor")) if k in('ninja','pirate') else 99
    c3=C(rgb("getComputedStyle($('nav button:not(.on)')).color"),rgb("getComputedStyle($('nav')).backgroundColor")) if k in('ninja','pirate') else 99
    P(f'{k:7s}: onglets OK | contraste titres cartes {c1:.1f} | en-tête {min(c2,99):.1f} | menu {min(c3,99):.1f} | ≥ 4,5 :',min(c1,c2,c3)>=4.5)
  P('aucun nom ni logo de licence :',not any(w in open('index.html',encoding='utf-8').read() for w in ['Naruto','One Piece','Konoha','Mugiwara','Luffy','Uzumaki']))
  P('erreurs :',errs);b.close()
