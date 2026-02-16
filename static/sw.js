/* diary/static/sw.js */

const CACHE_NAME = 'diary-speed-v1';
const urlsToCache = [
  '/',
  '/static/style.css',
  '/static/script.js'
  // 不包含 manifest.json 或 icon，因為您不需要安裝功能
];

// 安裝時快取核心檔案
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// 攔截請求：有快取讀快取，沒快取讀網路
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response; // 命中快取！
        }
        return fetch(event.request);
      })
  );
});

// 清除舊快取 (當版本更新時)
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});