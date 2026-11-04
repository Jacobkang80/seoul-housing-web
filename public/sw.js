const CACHE='seoul-housing-web-v2';
self.addEventListener('install',event=>{
  const assets=['./','./manifest.webmanifest','./icon-192.png','./icon-512.png'].map(name=>new Request(new URL(name,self.location.href),{cache:'reload'}));
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(assets)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('seoul-housing-web-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch',event=>{
  const request=event.request,url=new URL(request.url);
  if(request.method!=='GET'||url.origin!==self.location.origin)return;
  const data=url.pathname.endsWith('/data/snapshot.json');
  const key=data?new Request(url.origin+url.pathname):request;
  event.respondWith((async()=>{
    let cache=null;
    try{cache=await caches.open(CACHE)}catch{}
    try{
      const options=data?{cache:'no-store'}:request.mode==='navigate'?{cache:'no-cache'}:undefined;
      const response=await fetch(request,options);
      if(response.status>=500||response.status===408||response.status===429)throw Error('Temporary server error');
      // Storage limits must not turn a good online response into stale data.
      if(response.ok&&cache){try{await cache.put(key,response.clone())}catch{}}
      return response;
    }catch(error){
      let cached=null;
      if(cache){try{cached=await cache.match(key,{ignoreSearch:true})||(request.mode==='navigate'?await cache.match(new URL('./',self.location.href)):null)}catch{}}
      if(!cached)throw error;
      if(data){
        const headers=new Headers(cached.headers);
        headers.set('X-Seoul-Offline','1');headers.delete('Content-Encoding');headers.delete('Content-Length');
        return new Response(await cached.arrayBuffer(),{status:200,headers});
      }
      return cached;
    }
  })());
});
