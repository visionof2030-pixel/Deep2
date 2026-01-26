// sw.js
self.addEventListener("install", e => {
  e.waitUntil(
    caches.open("admin-cache").then(c =>
      c.addAll([
        "/admin.html",
        "/manifest.json"
      ])
    )
  )
})

self.addEventListener("fetch", e => {
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request))
  )
})