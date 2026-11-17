# v9.21 — assureur contrôlé d'après la liste 2026 + revue d'expert (cohérence des données)
from playwright.sync_api import sync_playwright
def P(*a):print(*a,flush=True)
errs=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  c=b.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True);pg=c.new_page();pg.set_default_timeout(20000)
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('dialog',lambda d:d.accept())
  pg.goto('http://localhost:8765/');pg.wait_for_timeout(2500)
  # --- jeu sain : aucune incohérence
  pg.evaluate("""db.marches.push({id:'ok',titulaire:'SOGEA SATOM',num:'2026-0001',objet:'Pont',montant:'1000000000',notif:'2026-01-10',debut:'2026-03-01',delaiM:'18',taux:'1',plafond:'10',avance:'100000000'});
   db.garanties.push({id:'gok',marche:'ok',type:'Bonne exécution',organisme:'SERENITY SA',montant:'40000000',emission:'2026-01-25',echeance:'2028-12-31',statut:'Active'});
   db.assurances.push({id:'aok',marche:'ok',type:'Tous risques chantier (TRC)',assureur:'SUNU Assurances IARD',police:'TRC-1',assure:'SOGEA SATOM',montant:'1000000000',prime:'5000000',effet:'2026-02-20',echeance:'2028-12-31',statut:'Active'});
   db.os.push({id:'osd',marche:'ok',num:'OS1',type:'Démarrage',date:'2026-03-01'});
   save();go('conf')""");pg.wait_for_timeout(500)
  L=pg.evaluate("coh().map(x=>x.s+'|'+x.m+'|'+x.t)")
  P('jeu sain : aucune incohérence :',L==[],L[:3])
  P('carte « aucune incohérence » :','Aucune incohérence détectée' in pg.inner_text('#v'))
  # --- jeu piégé
  pg.evaluate("""db.marches.push({id:'m2',avance:'200000',titulaire:'BATIMAX',num:'2026-0001',objet:'x',montant:'50000',notif:'2026-05-10',debut:'2026-03-01',delaiM:'200',reception:'2026-02-01',fin_garantie:'2026-01-01',garmois:'12',taux:'25',plafond:'30'});
   db.marches.push({id:'m3',titulaire:'',num:'',montant:'100000000',notif:'2062-01-01',debut:'2026-03-01'});
   db.avenants.push({id:'v1',marche:'m2',num:'A1',date:'2026-04-01',montant:'30000'});
   db.garanties.push({id:'g1',marche:'m2',type:'Bonne exécution',organisme:'AXA Côte d’Ivoire',montant:'90000',emission:'2026-12-01',echeance:'2026-03-01',statut:'Active'});
   db.garanties.push({id:'g2',marche:'m2',type:'Avance de démarrage',organisme:'NSIA',montant:'10',emission:'2026-06-01',statut:'Mainlevée obtenue',fin_ev:'PV de réception définitive'});
   db.garanties.push({id:'g3',marche:'zzz',type:'Soumission',organisme:'Serenity',montant:'5',statut:'Active'});
   db.garanties.push({id:'g5',marche:'m2',type:'Bonne exécution',organisme:'SERENITY SA',montant:'40000',emission:'2026-04-01',echeance:'2030-01-01',statut:'Active'});
   db.assurances.push({id:'a3',marche:'ok',type:'Tous risques chantier (TRC)',assureur:'SUNU Assurances IARD',police:'TRC-3',assure:'SOGEA SATOM',montant:'1000000000',effet:'2026-02-20',echeance:'2027-01-01',statut:'Active'});
   db.garanties.push({id:'g4',marche:'m2',type:'Bonne exécution',organisme:'AXA Côte d’Ivoire',montant:'90000',emission:'2026-12-01',echeance:'2026-03-01',statut:'Active'});
   db.assurances.push({id:'a1',marche:'m2',type:'Tous risques chantier (TRC)',assureur:'Coris Bank International',police:'P1',assure:'AUTRE ENTREPRISE',montant:'10000',prime:'20000',effet:'2026-09-01',echeance:'2026-05-01',statut:'Active'});
   db.assurances.push({id:'a2',marche:'m2',type:'Responsabilité civile (RC)',assureur:'Wafa Vie',police:'P2',statut:'Expirée',echeance:'2030-01-01'});
   db.os.push({id:'o1',marche:'m2',num:'OS1',type:'Démarrage',date:'2026-02-01'});db.os.push({id:'o2',marche:'m2',num:'OS1',type:'Démarrage',date:'2026-03-01'});
   db.os.push({id:'o3',marche:'m2',num:'OS3',type:'Reprise',date:'2026-04-01'});db.os.push({id:'o4',marche:'m2',num:'OS4',type:'Prolongation',date:'2026-04-02'});
   db.reserves.push({id:'r1',marche:'m2',type:'Réception provisoire',objet:'fissure',date:'2026-05-01',levee:'2026-04-01',statut:'Levée'});
   save();render()""");pg.wait_for_timeout(300)
  T=pg.evaluate("coh().map(x=>x.s+'|'+x.ent+'|'+x.t)")
  has=lambda ent,sub,s=None:any(x.split('|')[1]==ent and sub in x and (s is None or x.startswith(s+'|')) for x in T)
  P('  nb :',len(T))
  P('n° de marché en double :',has('marches','en double','ko'))
  P('année improbable (2062) :',has('marches','improbable','ko'))
  P('démarrage avant notification :',has('marches','antérieur à la notification','warn'))
  P('réception avant démarrage :',has('marches','Réception (','ko') or has('marches','antérieure au démarrage','ko'))
  P('délai de garantie avant réception :',has('marches','Fin du délai de garantie','ko'))
  P('délai 200 mois :',has('marches','200 mois','warn'))
  P('taux de pénalité 25 ‰ :',has('marches','25 ‰','warn'))
  P('plafond 30 % :',has('marches','Plafond de pénalités','warn'))
  P('avenants cumulés > 30 % :',has('marches','Avenants cumulés','warn'))
  P('titulaire manquant :',has('marches','Titulaire non renseigné','warn'))
  P('garantie > marché :',has('garanties','supérieure au montant du marché','ko'))
  P('émission après échéance :',has('garanties','postérieure à l’échéance','ko'))
  P('garantie avant notification :',has('garanties','avant la notification','warn'))
  P('garantie sans marché :',has('garanties','marché inexistant','ko'))
  P('garantie en double :',has('garanties','en double','warn'))
  P('organisme non habilité (AXA) :',has('garanties','absent de la liste 2026','warn'))
  P('mainlevée sans date + événement incohérent :',has('garanties','Mainlevée obtenue','info') and has('garanties','incohérent avec une garantie','warn'))
  P('garantie d’avance < avance :',any('garanties|' in x and 'inférieure à l’avance' in x for x in T))
  P('assurance : effet après démarrage :',has('assurances','après le démarrage','warn'))
  P('assurance : échéance avant fin des travaux :',has('assurances','avant la fin prévue','warn'))
  P('assurance : assuré ≠ titulaire :',has('assurances','différent du titulaire','warn'))
  P('assurance : capital TRC < marché :',has('assurances','Capital TRC','warn'))
  P('assurance : prime > capital :',has('assurances','Prime (','ko'))
  P('assurance : banque comme assureur :',has('assurances','banque','warn'))
  P('assurance : société vie seule :',has('assurances','Wafa Vie','warn'))
  P('assurance : Expirée mais échéance future :',has('assurances','Expirée','info'))
  P('OS : deux démarrages :',has('os','Plusieurs OS de démarrage','warn'))
  P('OS : n° en double :',has('os','en double','warn'))
  P('OS : reprise sans arrêt :',has('os','sans arrêt préalable','warn'))
  P('OS : prolongation sans durée :',has('os','sans durée','warn'))
  P('réserve : levée avant notification :',has('reserves','antérieure à la notification','ko'))
  P('tri par gravité (ko d’abord) :',pg.evaluate("(()=>{const L=coh();const i=L.findIndex(x=>x.s!='ko');return i<0||L.slice(i).every(x=>x.s!='ko')})()"))
  # interface
  pg.evaluate("go('conf')");pg.wait_for_timeout(300)
  tx=pg.inner_text('#v')
  P('carte revue d’expert affichée :','Revue d’expert' in tx and 'Incohérence' in tx and 'Que faire' in tx)
  pg.evaluate("cohSet('ko')");pg.wait_for_timeout(300)
  P('filtre « incohérences » :',pg.evaluate("document.querySelectorAll('#v .card:last-child .b.r').length")>0 and pg.evaluate("document.querySelectorAll('#v .card:last-child .b.o').length")==0)
  pg.evaluate("cohSet('all')");pg.evaluate("render()");pg.wait_for_timeout(200)
  P('alerte tableau de bord :',pg.evaluate("go('dash'),document.body.textContent.includes('incohérence(s) ou anomalie(s)')"))
  P('bouton Ouvrir ouvre la fiche :',pg.evaluate("cohOpen('garanties','g1'),cur.e=='garanties'&&cur.id=='g1'"))
  pg.evaluate("$('#dlg')&&$('#dlg').close&&$('#dlg').close()")
  # --- analyse d'une assurance : contrôle de l'assureur
  pg.evaluate("go('conf')")
  R={}
  for i in ['aok','a1','a2']:
    pg.evaluate(f"anPol='{i}';render()")
    R[i]=pg.evaluate(f"(()=>{{const a=db.assurances.find(x=>x.id=='{i}'),m=mk(a.marche);const r=anRun(a,m,'',{{}});const c=r.C.find(c=>c.l.startsWith('Compagnie agréée en assurance'));return c?c.v+'|'+c.co:''}})()")
    P(' ',i,R[i][:140])
  P('assurance SUNU IARD : conforme :',R['aok'].startswith('ok|'))
  P('assurance banque : non conforme :',R['a1'].startswith('ko|'))
  P('assurance société vie : non conforme :',R['a2'].startswith('ko|'))
  # --- XSS dans les messages
  pg.evaluate("db.marches.push({id:'x',titulaire:'<img src=x onerror=window.__x=1>',num:'<b>9</b>',montant:'1000000',notif:'2026-05-10',debut:'2026-03-01'});save();go('conf')");pg.wait_for_timeout(300)
  P('XSS neutralisé :',pg.evaluate("window.__x")is None)
  P('erreurs :',errs)
