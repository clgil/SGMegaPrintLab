/* ============================================================
 * SGMegaPrintLab — Service Worker (offline-first)
 * ------------------------------------------------------------
 * Estrategias:
 *   1. CACHE-FIRST  -> assets estáticos (CSS, JS, imágenes, fuentes, iconos).
 *                       La UI carga instantáneamente desde caché.
 *   2. NETWORK-FIRST-> páginas HTML servidas por Flask.
 *                       Si el servidor local está reiniciándose o caído,
 *                       hace fallback a una página offline elegante.
 *
 * Al publicar una nueva versión basta con incrementar VERSION:
 * el SW viejo se limpia solo en el evento "activate".
 * ============================================================ */

const VERSION = 'sgmegaprintlab-v1.0.0';

const STATIC_CACHE  = `${VERSION}-static`;   // CSS, JS, imágenes, fuentes
const DYNAMIC_CACHE = `${VERSION}-dynamic`;  // respuestas HTML (NetworkFirst)
const OFFLINE_CACHE = `${VERSION}-offline`;  // página offline de respaldo

// Página offline embebida: no depende del servidor para nada.
const OFFLINE_HTML = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SGMegaPrintLab — Sin conexión</title>
<style>
  :root { color-scheme: dark; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    min-height: 100vh; display: flex; align-items: center; justify-content: center;
    background: linear-gradient(160deg, #0f172a 0%, #1e293b 55%, #172554 100%);
    color: #e2e8f0; padding: 24px;
  }
  .card {
    max-width: 480px; width: 100%; text-align: center;
    background: rgba(30, 41, 59, .75); backdrop-filter: blur(8px);
    border: 1px solid rgba(148, 163, 184, .2); border-radius: 20px;
    padding: 48px 32px; box-shadow: 0 24px 60px rgba(0,0,0,.45);
  }
  .icon { font-size: 64px; line-height: 1; margin-bottom: 20px; }
  h1 { font-size: 1.5rem; margin-bottom: 12px; color: #f8fafc; }
  p  { font-size: .95rem; line-height: 1.6; color: #94a3b8; margin-bottom: 28px; }
  .btn {
    display: inline-block; background: #2563eb; color: #fff; text-decoration: none;
    padding: 12px 28px; border-radius: 12px; font-weight: 600; font-size: .95rem;
    transition: transform .15s ease, box-shadow .15s ease;
    box-shadow: 0 8px 20px rgba(37, 99, 235, .35);
  }
  .btn:hover { transform: translateY(-2px); box-shadow: 0 12px 26px rgba(37, 99, 235, .45); }
  .hint { margin-top: 22px; font-size: .8rem; color: #64748b; }
  .pulse { animation: pulse 2s ease-in-out infinite; display: inline-block; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .45; } }
</style>
</head>
<body>
  <div class="card">
    <div class="icon"><span class="pulse">🖨️</span></div>
    <h1>Servidor no disponible</h1>
    <p>El servidor local de <strong>SGMegaPrintLab</strong> está reiniciándose o no responde.
       Los datos y la interfaz volverán en unos segundos.</p>
    <a class="btn" href="/dashboard" onclick="location.reload()">Reintentar ahora</a>
    <div class="hint">Consejo: verifica que la aplicación de escritorio esté abierta<br>o ejecuta el servidor del taller nuevamente.</div>
  </div>
</body>
</html>`;

// Precarga de recursos críticos de la UI (CacheFirst en runtime también).
const PRECACHE_URLS = [
  '/static/css/bootstrap.min.css',
  '/static/css/custom.css',
  '/static/css/icons/bootstrap-icons.min.css',
  '/static/js/bootstrap.bundle.min.js',
  '/static/js/utils.js',
  '/static/js/app.js',
  '/static/js/pwa-install.js',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

/* ---------------------------- INSTALL ---------------------------- */
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      // Si un recurso falta (p.ej. aún no desplegado), no bloquear la instalación.
      .catch(() => {})
      .then(() => self.skipWaiting())
  );
});

/* ---------------------------- ACTIVATE --------------------------- */
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => !k.startsWith(VERSION)).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

/* ------------------------- HELPERS DE RUTA ----------------------- */
const isStaticAsset = (url) =>
  url.pathname.startsWith('/static/');

const isHtmlRequest = (request) => {
  const dest = request.destination;
  return (
    request.mode === 'navigate' ||
    dest === 'document' ||
    (request.headers.get('accept') || '').includes('text/html')
  );
};

const isApiCall = (url) =>
  url.pathname.startsWith('/api/') || url.pathname.includes('/_get_file_url/');

/* ---------------------- ESTRATEGIA: CACHE-FIRST ------------------ */
async function cacheFirst(request) {
  const cached = await caches.match(request, { ignoreSearch: false });
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    // Última oportunidad: versión anterior del asset en cualquier caché.
    const fallback = await caches.match(request);
    if (fallback) return fallback;
    return new Response('', { status: 503, statusText: 'Asset no disponible offline' });
  }
}

/* -------------------- ESTRATEGIA: NETWORK-FIRST ------------------ */
async function networkFirst(request) {
  const networkTimeout = new Promise((_, reject) =>
    setTimeout(() => reject(new Error('network-timeout')), 4000)
  );

  try {
    const response = await Promise.race([fetch(request), networkTimeout]);
    if (response && response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
      // Caché dinámica acotada (evita crecimiento indefinido).
      trimCache(DYNAMIC_CACHE, 30);
    }
    return response;
  } catch (err) {
    // 1) Última copia conocida de esa página
    const cached = await caches.match(request);
    if (cached) return cached;

    // 2) Fallback: página offline elegante
    // (Si se añade un template offline.html servido en la raíz, cachearlo aquí.)

    return new Response(OFFLINE_HTML, {
      status: 503,
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
    });
  }
}

async function trimCache(cacheName, maxEntries) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  if (keys.length > maxEntries) {
    await Promise.all(keys.slice(0, keys.length - maxEntries).map((k) => cache.delete(k)));
  }
}

/* ----------------------------- FETCH ----------------------------- */
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Solo GET; todo lo demás (POST de formularios, API de escritura) va directo a red.
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Peticiones de datos/API: nunca cachear (los datos deben ser frescos).
  if (isApiCall(url)) return;

  if (isStaticAsset(url)) {
    event.respondWith(cacheFirst(request));
  } else if (isHtmlRequest(request)) {
    event.respondWith(networkFirst(request));
  }
  // Cualquier otro caso (uploads, etc.): fetch por defecto.
});

/* ------------------------ MENSAJES (opcional) --------------------- */
self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') self.skipWaiting();
});
