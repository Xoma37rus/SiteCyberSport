/**
 * PWA Utilities — установка, обновления, офлайн статус
 */

class PWAUtils {
    constructor() {
        this.isInstalled = false;
        this.deferredPrompt = null;
        this.isOnline = navigator.onLine;
    }

    async init() {
        // Регистрация Service Worker
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/static/sw.js');
                console.log('Service Worker registered:', registration.scope);
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }

        // Обработка установки
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallButton();
        });

        // Отслеживание онлайн/офлайн
        window.addEventListener('online', () => this.updateOnlineStatus(true));
        window.addEventListener('offline', () => this.updateOnlineStatus(false));

        // Проверка, установлено ли уже
        window.addEventListener('appinstalled', () => {
            this.isInstalled = true;
            this.hideInstallButton();
            console.log('PWA installed');
        });
    }

    async install() {
        if (!this.deferredPrompt) {
            console.log('Install prompt not available');
            return;
        }

        this.deferredPrompt.prompt();
        const { outcome } = await this.deferredPrompt.userChoice;
        console.log(`User response: ${outcome}`);
        this.deferredPrompt = null;
        this.hideInstallButton();
    }

    showInstallButton() {
        let installBanner = document.getElementById('pwa-install-banner');
        if (installBanner) return;

        installBanner = document.createElement('div');
        installBanner.id = 'pwa-install-banner';
        installBanner.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #00f0ff, #3a86ff);
            color: #0d1117;
            padding: 12px 24px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
            z-index: 9999;
            box-shadow: 0 4px 16px rgba(0, 240, 255, 0.3);
            animation: slideUp 0.3s ease;
        `;

        installBanner.innerHTML = `
            <span style="font-weight: 600;">Установить EasyCyberPro</span>
            <button id="pwa-install-btn" style="
                background: #0d1117;
                color: #00f0ff;
                border: none;
                border-radius: 8px;
                padding: 6px 16px;
                font-weight: 700;
                cursor: pointer;
            ">Установить</button>
            <button id="pwa-dismiss-btn" style="
                background: transparent;
                border: none;
                color: #0d1117;
                font-size: 18px;
                cursor: pointer;
                padding: 0 4px;
            ">&times;</button>
        `;

        document.body.appendChild(installBanner);

        document.getElementById('pwa-install-btn').addEventListener('click', () => this.install());
        document.getElementById('pwa-dismiss-btn').addEventListener('click', () => this.hideInstallBanner());
    }

    hideInstallButton() {
        const banner = document.getElementById('pwa-install-banner');
        if (banner) banner.remove();
    }

    hideInstallBanner() {
        this.hideInstallButton();
        this.deferredPrompt = null;
    }

    updateOnlineStatus(online) {
        this.isOnline = online;
        let banner = document.getElementById('online-status-banner');

        if (!online) {
            if (!banner) {
                banner = document.createElement('div');
                banner.id = 'online-status-banner';
                banner.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    background: #f87171;
                    color: white;
                    text-align: center;
                    padding: 8px;
                    z-index: 10000;
                    font-weight: 600;
                `;
                banner.textContent = '⚠️ Нет подключения к интернету';
                document.body.appendChild(banner);
            }
        } else {
            if (banner) {
                banner.remove();
                // Показываем сообщение о восстановлении
                const restored = document.createElement('div');
                restored.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    background: #34d399;
                    color: white;
                    text-align: center;
                    padding: 8px;
                    z-index: 10000;
                    font-weight: 600;
                    animation: fadeOut 2s ease forwards;
                `;
                restored.textContent = '✅ Подключение восстановлено';
                document.body.appendChild(restored);
                setTimeout(() => restored.remove(), 2000);
            }
        }
    }

    /**
     * Запрос разрешения на push-уведомления
     */
    async requestNotificationPermission() {
        if (!('Notification' in window)) {
            console.warn('Notifications not supported');
            return false;
        }

        if (Notification.permission === 'granted') {
            return true;
        }

        if (Notification.permission === 'denied') {
            console.warn('Notifications denied');
            return false;
        }

        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }
}

// Авто-инициализация
document.addEventListener('DOMContentLoaded', () => {
    window.pwaUtils = new PWAUtils();
    window.pwaUtils.init();
});

window.PWAUtils = PWAUtils;
