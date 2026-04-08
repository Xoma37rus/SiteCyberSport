/**
 * Theme Switcher — переключатель тёмной/светлой темы
 */

class ThemeSwitcher {
    constructor() {
        this.themes = {
            dark: {
                '--bg-primary': '#0d1117',
                '--bg-secondary': '#161b22',
                '--bg-card': '#1c2128',
                '--accent-cyan': '#00f0ff',
                '--text-primary': '#ffffff',
                '--text-secondary': '#8b949e',
                '--border-color': '#30363d',
            },
            light: {
                '--bg-primary': '#f6f8fa',
                '--bg-secondary': '#ffffff',
                '--bg-card': '#ffffff',
                '--accent-cyan': '#0891b2',
                '--text-primary': '#1f2937',
                '--text-secondary': '#6b7280',
                '--border-color': '#e5e7eb',
            }
        };

        this.currentTheme = localStorage.getItem('theme') || 'dark';
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.createToggle();
    }

    applyTheme(themeName) {
        const theme = this.themes[themeName];
        if (!theme) return;

        const root = document.documentElement;
        Object.entries(theme).forEach(([prop, value]) => {
            root.style.setProperty(prop, value);
        });

        this.currentTheme = themeName;
        localStorage.setItem('theme', themeName);

        // Обновляем иконку
        const icon = document.querySelector('.theme-toggle-icon');
        if (icon) {
            icon.textContent = themeName === 'dark' ? '☀️' : '🌙';
        }

        // Обновляем meta theme-color
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.content = theme['--bg-primary'];
        }
    }

    toggle() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
    }

    createToggle() {
        // Ищем место для кнопки (в навбаре)
        const navMenu = document.querySelector('.nav-menu');
        if (!navMenu) return;

        // Проверяем, нет ли уже кнопки
        if (document.querySelector('.theme-toggle')) return;

        const btn = document.createElement('button');
        btn.className = 'theme-toggle';
        btn.title = 'Переключить тему';
        btn.style.cssText = `
            background: transparent;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 8px 12px;
            cursor: pointer;
            font-size: 18px;
            transition: all 0.3s;
        `;

        const icon = document.createElement('span');
        icon.className = 'theme-toggle-icon';
        icon.textContent = this.currentTheme === 'dark' ? '☀️' : '🌙';

        btn.appendChild(icon);
        btn.addEventListener('click', () => this.toggle());
        btn.addEventListener('mouseenter', () => {
            btn.style.borderColor = 'var(--accent-cyan)';
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.borderColor = 'var(--border-color)';
        });

        navMenu.appendChild(btn);
    }

    getTheme() {
        return this.currentTheme;
    }

    isDark() {
        return this.currentTheme === 'dark';
    }
}

// Авто-инициализация
document.addEventListener('DOMContentLoaded', () => {
    window.themeSwitcher = new ThemeSwitcher();
});

window.ThemeSwitcher = ThemeSwitcher;
