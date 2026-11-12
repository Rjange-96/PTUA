// Gestionnaire PTUA — service worker v8.0
// Cache d'abord (démarrage instantané, hors ligne). Les nouvelles versions attendent l'accord de l'utilisateur.
const V='8.4',C='ptua-'+V,F=['./','./index.html','./manifest.webmanifest','./icon-180.png','./icon-192.png','./icon-512.png','./lib/qrcode.js','./lib/jsqr.js','./lib/public-sans.woff2'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F.map(u=>new Request(u,{cache:'reload'})))))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!=C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener('message',e=>{if(e.data==='skip')self.skipWaiting()});
self.addEventListener('fetch',e=>{const r=e.request,u=new URL(r.url);if(r.method!='GET'||u.origin!=location.origin)return;
 if(u.pathname.endsWith('/version.json'))return; // toujours sur le réseau
 if(r.mode=='navigate')return e.respondWith(caches.match('./index.html').then(x=>x||fetch(r)));
 e.respondWith(caches.match(r,{ignoreSearch:true}).then(x=>x||fetch(r).then(n=>{if(n.ok){const c=n.clone();caches.open(C).then(k=>k.put(r,c))}return n})))});
