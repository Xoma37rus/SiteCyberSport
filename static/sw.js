/**
 * Service Worker для PWA — кэширование, офлайн-режим, push-уведомления
 */
const CACHE_NAME = 'easycyberpro-v1';
const STATIC_CACHE = 'easycyberpro-static-v1';
const DYNAMIC_CACHE = 'easycyberpro-dynamic-v1';

const STATIC_ASSETS = [
    '/',
    '/static/style.css',
    '/static/bracket.js',
    '/static/charts.js',
    '/static/onboarding.js',
    '/static/pwa.js',
    '/static/manifest.json',
    '/static/images/logo.jpg',
];

// Установка — кэширование статических ресурсов
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Активация — очистка старых кэшей
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys.filter((key) => key !== STATIC_CACHE && key !== DYNAMIC_CACHE)
                    .map((key) => caches.delete(key))
            )
        ).then(() => self.clients.claim())
    );
});

// Перехват запросов — стратегия Cache First для статики, Network First для API
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Статические файлы — Cache First
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(request).then((response) => {
                return response || fetch(request).then((fetchResponse) => {
                    return caches.open(DYNAMIC_CACHE).then((cache) => {
                        cache.put(request, fetchResponse.clone());
                        return fetchResponse;
                    });
                });
            })
        );
        return;
    }

    // HTML страницы — Network First
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    return caches.open(DYNAMIC_CACHE).then((cache) => {
                        cache.put(request, response.clone());
                        return response;
                    });
                })
                .catch(() => caches.match('/'))
        );
        return;
    }

    // API запросы — Network Only
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(fetch(request));
        return;
    }
});

// Push-уведомления
self.addEventListener('push', (event) => {
    if (!event.data) return;

    let data;
    try {
        data = event.data.json();
    } catch {
        data = { title: 'EasyCyberPro', body: 'Новое уведомление' };
    }

    const options = {
        body: data.body || 'Новое уведомление',
        icon: data.icon || '/static/images/icon-192.png',
        badge: data.badge || '/static/images/icon-96.png',
        image: data.image || null,
        data: data.data || {},
        tag: data.tag || 'default',
        renotify: true,
        requireInteraction: false,
        actions: data.actions || [
            { action: 'view', title: 'Открыть' },
            { action: 'close', title: 'Закрыть' },
        ],
    };

    event.waitUntil(
        self.registration.showNotification(data.title || 'EasyCyberPro', options)
    );
});

// Клик по уведомлению
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'view' || !event.action) {
        const urlToOpen = event.notification.data?.url || '/dashboard';
        event.waitUntil(
            clients.matchAll({ type: 'window' }).then((windowClients) => {
                for (const client of windowClients) {
                    if (client.url.includes(urlToOpen)) {
                        return client.focus();
                    }
                }
                return clients.openWindow(urlToOpen);
            })
        );
    }
});

// Фоновая синхронизация
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-results') {
        event.waitUntil(syncResults());
    }
});

async function syncResults() {
    // Синхронизация результатов матчей при восстановлении соединения
    const cache = await caches.open(DYNAMIC_CACHE);
    // TODO: реализовать отправку закэшированных результатов
}
