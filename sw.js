/* WilFit: guarda no aparelho as fotos leves dos exercícios (carregam na hora nas próximas vezes).
   Só cuida das imagens de img/p e img/m; o app em si sempre vem atualizado da rede. */
const CACHE = "wilfit-fotos-v1";
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k !== CACHE) await caches.delete(k);
  await self.clients.claim();
})()));
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== self.location.origin || !/\/img\/(p|m)\/[^/]+\.webp$/.test(u.pathname)) return;
  e.respondWith(caches.open(CACHE).then(async c => {
    const salvo = await c.match(e.request);
    if (salvo) return salvo;
    const r = await fetch(e.request);
    if (r.ok) c.put(e.request, r.clone());
    return r;
  }));
});
