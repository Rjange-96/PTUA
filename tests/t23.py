# v9.1 — interface : icônes, sceau, accessibilité, état d'erreur en ligne
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[];alerts=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  for nm,vp,mob in [('mobile',{'width':393,'height':852},True),('PC',{'width':1280,'height':800},False)]:
    c=b.new_context(viewport=vp,is_mobile=mob,has_touch=mob);pg=c.new_page();pg.set_default_timeout(15000)
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:(alerts.append(d.message),d.accept()))
    pg.goto('http://localhost:8765/');pg.wait_for_timeout(2800)
    P(nm,'| cubes décoratifs masqués :',pg.evaluate("getComputedStyle($('#bg')).display=='none'"),'| splash retiré :',pg.evaluate("!$('#sp')"))
    P(' sceau dans l’en-tête :',pg.evaluate("!!document.querySelector('header svg.lgo')"),'| icônes SVG dans la navigation :',pg.evaluate("document.querySelectorAll('#nav svg').length>=5"))
    P(' boutons d’en-tête nommés :',pg.evaluate("[...document.querySelectorAll('.hb button')].every(b=>b.getAttribute('aria-label')||b.title)"),'| icône thème :',pg.evaluate("!!$('#th svg')"))
    P(' lien d’évitement :',pg.evaluate("document.querySelector('.skip').getAttribute('href')=='#v'"))
    ok=pg.evaluate("[...document.querySelectorAll('#nav button')].filter(b=>b.offsetParent).every(b=>b.getBoundingClientRect().height>=40)");P(' cibles de navigation ≥ 40 px :',ok)
    pg.evaluate("go('marches');edit('marches')");pg.wait_for_timeout(300)
    pg.evaluate("ok()");pg.wait_for_timeout(200)
    P(' erreur en ligne (pas d’alert) :',pg.evaluate("!!$('#derr')&&$('#derr').getAttribute('role')=='alert'"),'| champ marqué :',pg.evaluate("$('#df [name=num]').getAttribute('aria-invalid')=='true'"),'| focus sur le champ :',pg.evaluate("document.activeElement.name=='num'"),'| alert natif :',len(alerts))
    pg.evaluate("$('#df [name=num]').value='T-1';ok()");pg.wait_for_timeout(300)
    pg.evaluate("edit('marches')");pg.evaluate("$('#df [name=num]').value='T-1';ok()");pg.wait_for_timeout(200)
    P(' doublon signalé en ligne :',pg.evaluate("/existe déjà/.test($('#derr')?.textContent||'')"))
    pg.evaluate("$('#dlg').close()")
    pg.evaluate("go('conf')");pg.wait_for_timeout(300);P(' dates de conformité nommées :',pg.evaluate("[...document.querySelectorAll('#v input[type=date]')].every(i=>i.getAttribute('aria-label'))"),'| bascules aria-pressed :',pg.evaluate("[...document.querySelectorAll('#v button[aria-pressed]')].length>3"))
    pg.evaluate("document.documentElement.dataset.t='dark'");pg.evaluate("go('dash')");P(' thème sombre sans erreur')
    c.close()
  P('erreurs :',errs);b.close()
