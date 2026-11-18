// Gestionnaire PTUA — service worker v9.4
// v9.4 : seuls les caches « ptua-* » sont gérés ; le cache est reconstitué s'il a été effacé.
// Cache d'abord (démarrage instantané, hors ligne). Les nouvelles versions attendent l'accord de l'utilisateur.
const V='9.29',C='ptua-'+V,F=['./','./index.html','./manifest.webmanifest','./icon-180.png','./icon-192.png','./icon-512.png','./lib/qrcode.js','./lib/jsqr.js','./lib/public-sans.woff2','./lib/pdf.min.mjs','./lib/pdf.worker.min.mjs'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F.map(u=>new Request(u,{cache:'reload'})))))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x.startsWith('ptua-')&&x!=C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener('message',e=>{if(e.data==='skip')self.skipWaiting()});
self.addEventListener('fetch',e=>{const r=e.request,u=new URL(r.url);if(r.method!='GET'||u.origin!=location.origin)return;
 if(u.pathname.endsWith('/version.json'))return; // toujours sur le réseau
 if(r.mode=='navigate')return e.respondWith(caches.match('./index.html').then(x=>x||fetch(r).then(n=>{if(n.ok)caches.open(C).then(c=>c.addAll(F.map(u=>new Request(u,{cache:'reload'})))).catch(()=>{});return n}))); // cache effacé par une autre app du domaine : reconstitution automatique
 e.respondWith(caches.match(r,{ignoreSearch:true}).then(x=>x||fetch(r).then(n=>{if(n.ok){const c=n.clone();caches.open(C).then(k=>k.put(r,c))}return n})))});

// v9.17 — rappels : le serveur envoie un message générique ; le détail se lit dans l'application
self.addEventListener('push',e=>{let b='Des échéances demandent votre attention.';try{const d=e.data&&e.data.json();if(d&&d.b)b=String(d.b).slice(0,120)}catch(_){}
 e.waitUntil(self.registration.showNotification('PTUA',{body:b,icon:'./icon-192.png',badge:'./icon-192.png',tag:'ptua-rappel',renotify:true}))});
self.addEventListener('notificationclick',e=>{e.notification.close();e.waitUntil(self.clients.matchAll({type:'window',includeUncontrolled:true}).then(l=>{for(const c of l){if('focus' in c)return c.focus()}return self.clients.openWindow('./')}))});
