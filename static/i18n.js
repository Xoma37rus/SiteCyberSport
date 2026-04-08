/**
 * i18n — система мультиязычности
 */

class I18n {
    constructor() {
        this.currentLang = localStorage.getItem('lang') || 'ru';
        this.fallbackLang = 'ru';
        this.translations = {};
        this.loaded = false;
    }

    async init() {
        await this.loadTranslations(this.currentLang);
        this.applyTranslations();
        this.createLangSwitcher();
        this.loaded = true;
    }

    async loadTranslations(lang) {
        if (this.translations[lang]) return;

        try {
            const response = await fetch(`/static/locales/${lang}.json`);
            if (response.ok) {
                this.translations[lang] = await response.json();
            }
        } catch (e) {
            console.warn(`Failed to load translations for ${lang}`);
            this.translations[lang] = {};
        }
    }

    t(key, params = {}) {
        const translations = this.translations[this.currentLang] ||
                            this.translations[this.fallbackLang] || {};

        let value = key.split('.').reduce((obj, k) => obj && obj[k], translations);

        if (!value) {
            // Fallback
            const fallbackTranslations = this.translations[this.fallbackLang] || {};
            value = key.split('.').reduce((obj, k) => obj && obj[k], fallbackTranslations);
        }

        if (!value) return key;

        // Подстановка параметров
        Object.entries(params).forEach(([k, v]) => {
            value = value.replace(`{${k}}`, v);
        });

        return value;
    }

    applyTranslations() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.dataset.i18n;
            const text = this.t(key);
            if (el.tagName === 'INPUT' && el.type !== 'submit') {
                el.placeholder = text;
            } else {
                el.textContent = text;
            }
        });
    }

    async setLanguage(lang) {
        await this.loadTranslations(lang);
        this.currentLang = lang;
        localStorage.setItem('lang', lang);
        document.documentElement.lang = lang;
        this.applyTranslations();

        // Обновляем UI
        document.querySelectorAll('.lang-option').forEach(el => {
            el.classList.toggle('active', el.dataset.lang === lang);
        });
    }

    createLangSwitcher() {
        const navMenu = document.querySelector('.nav-menu');
        if (!navMenu || document.querySelector('.lang-switcher')) return;

        const languages = [
            { code: 'ru', name: '🇷🇺 RU' },
            { code: 'en', name: '🇬🇧 EN' },
            { code: 'uk', name: '🇺🇦 UK' },
            { code: 'kk', name: '🇰🇿 KZ' },
        ];

        const container = document.createElement('div');
        container.className = 'lang-switcher';
        container.style.cssText = `
            display: flex;
            gap: 4px;
            align-items: center;
        `;

        languages.forEach(lang => {
            const btn = document.createElement('button');
            btn.className = `lang-option ${lang.code === this.currentLang ? 'active' : ''}`;
            btn.dataset.lang = lang.code;
            btn.textContent = lang.name;
            btn.style.cssText = `
                background: ${lang.code === this.currentLang ? 'var(--accent-cyan)' : 'transparent'};
                color: ${lang.code === this.currentLang ? 'var(--bg-primary)' : 'var(--text-secondary)'};
                border: 1px solid var(--border-color);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s;
            `;
            btn.addEventListener('click', () => this.setLanguage(lang.code));
            btn.addEventListener('mouseenter', () => {
                if (lang.code !== this.currentLang) {
                    btn.style.borderColor = 'var(--accent-cyan)';
                }
            });
            btn.addEventListener('mouseleave', () => {
                if (lang.code !== this.currentLang) {
                    btn.style.borderColor = 'var(--border-color)';
                }
            });
            container.appendChild(btn);
        });

        navMenu.appendChild(container);
    }

    getLanguage() {
        return this.currentLang;
    }
}

// Авто-инициализация
document.addEventListener('DOMContentLoaded', () => {
    window.i18n = new I18n();
    window.i18n.init();
});

window.I18n = I18n;
