/**
 * Onboarding Tour — интерактивный тур для новых пользователей
 */

class OnboardingTour {
    constructor() {
        this.steps = [];
        this.currentStep = 0;
        this.overlay = null;
        this.tooltip = null;
    }

    /**
     * Запуск тура
     */
    start(steps) {
        this.steps = steps;
        this.currentStep = 0;
        this.showStep(0);
    }

    /**
     * Показать шаг
     */
    showStep(index) {
        if (index >= this.steps.length) {
            this.end();
            return;
        }

        this.currentStep = index;
        const step = this.steps[index];

        // Создаём overlay
        if (!this.overlay) {
            this.overlay = document.createElement('div');
            this.overlay.className = 'onboarding-overlay';
            this.overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.7);
                z-index: 9998;
                transition: opacity 0.3s;
            `;
            document.body.appendChild(this.overlay);
        }

        // Создаём tooltip
        if (!this.tooltip) {
            this.tooltip = document.createElement('div');
            this.tooltip.className = 'onboarding-tooltip';
            this.tooltip.style.cssText = `
                position: fixed;
                background: #1c2128;
                border: 2px solid #00f0ff;
                border-radius: 16px;
                padding: 24px;
                max-width: 400px;
                z-index: 9999;
                box-shadow: 0 8px 32px rgba(0, 240, 255, 0.2);
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            `;
            document.body.appendChild(this.tooltip);
        }

        // Подсвечиваем элемент
        const target = document.querySelector(step.target);
        if (target) {
            target.style.boxShadow = '0 0 0 4px #00f0ff';
            target.style.transition = 'box-shadow 0.3s';
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        // Заполняем tooltip
        this.tooltip.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                <h3 style="color: #00f0ff; margin: 0; font-size: 18px;">
                    ${step.icon || '🎮'} ${step.title}
                </h3>
                <button class="onboarding-close" style="
                    background: none;
                    border: none;
                    color: #8b949e;
                    font-size: 20px;
                    cursor: pointer;
                    padding: 0 4px;
                ">&times;</button>
            </div>
            <p style="color: #8b949e; margin: 0 0 20px 0; line-height: 1.5;">${step.description}</p>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #8b949e; font-size: 13px;">${index + 1} / ${this.steps.length}</span>
                <div style="display: flex; gap: 8px;">
                    ${index > 0 ? '<button class="onboarding-prev" style="padding: 8px 16px; background: #30363d; border: none; border-radius: 8px; color: #fff; cursor: pointer;">← Назад</button>' : ''}
                    <button class="onboarding-next" style="padding: 8px 16px; background: linear-gradient(135deg, #00f0ff, #3a86ff); border: none; border-radius: 8px; color: #0d1117; font-weight: 700; cursor: pointer;">
                        ${index < this.steps.length - 1 ? 'Далее →' : 'Завершить 🎉'}
                    </button>
                </div>
            </div>
        `;

        // Позиционируем tooltip
        this.positionTooltip(target);

        // Обработчики
        this.tooltip.querySelector('.onboarding-close').addEventListener('click', () => this.end());
        if (this.tooltip.querySelector('.onboarding-prev')) {
            this.tooltip.querySelector('.onboarding-prev').addEventListener('click', () => this.prev());
        }
        this.tooltip.querySelector('.onboarding-next').addEventListener('click', () => this.next());

        // Сохраняем прогресс
        localStorage.setItem('onboarding_step', index);
    }

    /**
     * Позиционирование tooltip
     */
    positionTooltip(target) {
        if (!target || !this.tooltip) return;

        const rect = target.getBoundingClientRect();
        const tooltipRect = this.tooltip.getBoundingClientRect();

        let top = rect.bottom + 16;
        let left = rect.left;

        // Проверяем, помещается ли tooltip снизу
        if (top + tooltipRect.height > window.innerHeight) {
            top = rect.top - tooltipRect.height - 16;
        }

        // Проверяем, помещается ли tooltip справа
        if (left + tooltipRect.width > window.innerWidth) {
            left = window.innerWidth - tooltipRect.width - 16;
        }

        // Проверяем, не выходит ли за левый край
        if (left < 16) {
            left = 16;
        }

        this.tooltip.style.top = `${top}px`;
        this.tooltip.style.left = `${left}px`;
    }

    /**
     * Следующий шаг
     */
    next() {
        this.resetHighlight();
        this.showStep(this.currentStep + 1);
    }

    /**
     * Предыдущий шаг
     */
    prev() {
        this.resetHighlight();
        this.showStep(this.currentStep - 1);
    }

    /**
     * Сброс подсветки
     */
    resetHighlight() {
        if (this.steps[this.currentStep]) {
            const target = document.querySelector(this.steps[this.currentStep].target);
            if (target) {
                target.style.boxShadow = '';
            }
        }
    }

    /**
     * Завершение тура
     */
    end() {
        this.resetHighlight();
        if (this.overlay) {
            this.overlay.remove();
            this.overlay = null;
        }
        if (this.tooltip) {
            this.tooltip.remove();
            this.tooltip = null;
        }
        localStorage.setItem('onboarding_completed', 'true');
        localStorage.removeItem('onboarding_step');
    }
}

// Шаг по умолчанию для новых пользователей
const defaultSteps = [
    {
        target: '.navbar',
        icon: '🧭',
        title: 'Навигация',
        description: 'Здесь вы найдёте турниры, рейтинг, новости и свой профиль.',
    },
    {
        target: '.dashboard, .profile-section',
        icon: '👤',
        title: 'Ваш профиль',
        description: 'Настройте аватар, био, социальные сети и дисциплины.',
    },
    {
        target: '.rating-card',
        icon: '📊',
        title: 'Рейтинг ELO',
        description: 'Ваш рейтинг растёт с каждой победой. Цель — Level 10 (2000+ ELO)!',
    },
    {
        target: '.tournaments-section',
        icon: '🏆',
        title: 'Турниры',
        description: 'Участвуйте в турнирах по Dota 2, CS2 и Мир танков.',
    },
    {
        target: '.leaderboard',
        icon: '🥇',
        title: 'Таблица лидеров',
        description: 'Соревнуйтесь с лучшими игроками и поднимайтесь в рейтинге!',
    },
    {
        target: '.coach-section',
        icon: '🎓',
        title: 'Тренерство',
        description: 'Найдите тренера для улучшения навыков или станьте тренером сами.',
    },
];

// Авто-запуск для новых пользователей
document.addEventListener('DOMContentLoaded', () => {
    const completed = localStorage.getItem('onboarding_completed');
    const isNew = document.body.dataset.newUser === 'true';

    if (!completed && isNew) {
        const tour = new OnboardingTour();
        setTimeout(() => tour.start(defaultSteps), 1000);

        // Кнопка "Пропустить"
        const skipBtn = document.createElement('button');
        skipBtn.textContent = 'Пропустить тур';
        skipBtn.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            background: #30363d;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            color: #fff;
            cursor: pointer;
        `;
        skipBtn.addEventListener('click', () => {
            tour.end();
            skipBtn.remove();
        });
        document.body.appendChild(skipBtn);
    }
});

window.OnboardingTour = OnboardingTour;
window.defaultOnboardingSteps = defaultSteps;
