/**
 * Charts.js — графики статистики для профилей пользователей
 * Использует Canvas API без внешних зависимостей
 */

class StatsCharts {
    constructor() {
        this.charts = {};
    }

    /**
     * График прогресса ELO (линейный)
     */
    drawEloProgress(canvasId, data, color = '#00f0ff') {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        // Настройка размеров
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);

        const width = rect.width;
        const height = rect.height;
        const padding = { top: 20, right: 20, bottom: 40, left: 50 };
        const chartWidth = width - padding.left - padding.right;
        const chartHeight = height - padding.top - padding.bottom;

        // Очистка
        ctx.clearRect(0, 0, width, height);

        if (!data || data.length === 0) {
            ctx.fillStyle = '#8b949e';
            ctx.font = '14px Segoe UI';
            ctx.textAlign = 'center';
            ctx.fillText('Нет данных', width / 2, height / 2);
            return;
        }

        // Находим min/max
        const elos = data.map(d => d.elo);
        const minElo = Math.min(...elos) - 50;
        const maxElo = Math.max(...elos) + 50;
        const eloRange = maxElo - minElo || 1;

        // Рисуем сетку
        ctx.strokeStyle = '#30363d';
        ctx.lineWidth = 1;
        const gridLines = 5;
        for (let i = 0; i <= gridLines; i++) {
            const y = padding.top + (chartHeight / gridLines) * i;
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(width - padding.right, y);
            ctx.stroke();

            // Подписи ELO
            const eloValue = Math.round(maxElo - (eloRange / gridLines) * i);
            ctx.fillStyle = '#8b949e';
            ctx.font = '11px Segoe UI';
            ctx.textAlign = 'right';
            ctx.fillText(eloValue, padding.left - 8, y + 4);
        }

        // Рисуем линию
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();

        const points = data.map((d, i) => ({
            x: padding.left + (chartWidth / (data.length - 1 || 1)) * i,
            y: padding.top + chartHeight - ((d.elo - minElo) / eloRange) * chartHeight,
            elo: d.elo,
            change: d.change,
        }));

        if (points.length === 1) {
            // Одна точка
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(points[0].x, points[0].y, 4, 0, Math.PI * 2);
            ctx.fill();
        } else {
            // Линия
            ctx.moveTo(points[0].x, points[0].y);
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo(points[i].x, points[i].y);
            }
            ctx.stroke();

            // Градиент под линией
            const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
            gradient.addColorStop(0, color + '40');
            gradient.addColorStop(1, color + '00');

            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.moveTo(points[0].x, height - padding.bottom);
            points.forEach(p => ctx.lineTo(p.x, p.y));
            ctx.lineTo(points[points.length - 1].x, height - padding.bottom);
            ctx.closePath();
            ctx.fill();

            // Точки
            points.forEach(p => {
                ctx.fillStyle = p.change >= 0 ? '#34d399' : '#f87171';
                ctx.beginPath();
                ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
                ctx.fill();
            });
        }

        // Подписи дат (последние 5)
        ctx.fillStyle = '#8b949e';
        ctx.font = '10px Segoe UI';
        ctx.textAlign = 'center';
        const labelStep = Math.max(1, Math.floor(data.length / 5));
        for (let i = 0; i < data.length; i += labelStep) {
            const x = padding.left + (chartWidth / (data.length - 1 || 1)) * i;
            const date = new Date(data[i].date);
            ctx.fillText(date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }), x, height - 10);
        }
    }

    /**
     * Круговая диаграмма Win/Loss
     */
    drawWinLossPie(canvasId, wins, losses, draws) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);

        const width = rect.width;
        const height = rect.height;
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) / 2 - 20;

        const total = wins + losses + draws;
        if (total === 0) {
            ctx.fillStyle = '#8b949e';
            ctx.font = '14px Segoe UI';
            ctx.textAlign = 'center';
            ctx.fillText('Нет данных', centerX, centerY);
            return;
        }

        const segments = [
            { value: wins, color: '#34d399', label: 'Победы' },
            { value: losses, color: '#f87171', label: 'Поражения' },
            { value: draws, color: '#fbbf24', label: 'Ничьи' },
        ].filter(s => s.value > 0);

        let startAngle = -Math.PI / 2;
        segments.forEach(seg => {
            const sliceAngle = (seg.value / total) * Math.PI * 2;
            ctx.fillStyle = seg.color;
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
            ctx.closePath();
            ctx.fill();
            startAngle += sliceAngle;
        });

        // Центральный круг (donut)
        ctx.fillStyle = '#1c2128';
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius * 0.6, 0, Math.PI * 2);
        ctx.fill();

        // Текст в центре
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 20px Segoe UI';
        ctx.textAlign = 'center';
        ctx.fillText(total, centerX, centerY + 5);
        ctx.font = '11px Segoe UI';
        ctx.fillStyle = '#8b949e';
        ctx.fillText('всего игр', centerX, centerY + 20);
    }

    /**
     * Столбчатая диаграмма по дисциплинам
     */
    drawDisciplineBars(canvasId, disciplines) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);

        const width = rect.width;
        const height = rect.height;
        const padding = { top: 20, right: 20, bottom: 60, left: 50 };
        const chartWidth = width - padding.left - padding.right;
        const chartHeight = height - padding.top - padding.bottom;

        if (!disciplines || disciplines.length === 0) {
            ctx.fillStyle = '#8b949e';
            ctx.font = '14px Segoe UI';
            ctx.textAlign = 'center';
            ctx.fillText('Нет данных', width / 2, height / 2);
            return;
        }

        const maxElo = Math.max(...disciplines.map(d => d.elo));
        const barWidth = Math.min(60, (chartWidth / disciplines.length) * 0.6);
        const gap = (chartWidth - barWidth * disciplines.length) / (disciplines.length + 1);

        disciplines.forEach((disc, i) => {
            const x = padding.left + gap + (barWidth + gap) * i;
            const barHeight = (disc.elo / maxElo) * chartHeight;
            const y = padding.top + chartHeight - barHeight;

            // Столбец
            const gradient = ctx.createLinearGradient(x, y, x, padding.top + chartHeight);
            gradient.addColorStop(0, '#00f0ff');
            gradient.addColorStop(1, '#3a86ff');
            ctx.fillStyle = gradient;
            ctx.fillRect(x, y, barWidth, barHeight);

            // Значение ELO
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 12px Segoe UI';
            ctx.textAlign = 'center';
            ctx.fillText(disc.elo, x + barWidth / 2, y - 8);

            // Название дисциплины
            ctx.fillStyle = '#8b949e';
            ctx.font = '11px Segoe UI';
            ctx.save();
            ctx.translate(x + barWidth / 2, padding.top + chartHeight + 15);
            ctx.rotate(Math.PI / 4);
            ctx.textAlign = 'left';
            ctx.fillText(disc.name, 0, 0);
            ctx.restore();
        });
    }

    /**
     * Heatmap активности (как GitHub contributions)
     */
    drawActivityHeatmap(containerId, activityData) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const weeks = 52;
        const days = 7;
        const cellSize = 12;
        const cellGap = 3;

        container.style.overflowX = 'auto';

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', weeks * (cellSize + cellGap));
        svg.setAttribute('height', days * (cellSize + cellGap) + 20);

        // Месяцы
        const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
        months.forEach((month, i) => {
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', i * (cellSize + cellGap) * 4.3 + 20);
            text.setAttribute('y', 10);
            text.setAttribute('fill', '#8b949e');
            text.setAttribute('font-size', '10');
            text.textContent = month;
            svg.appendChild(text);
        });

        // Ячейки
        for (let week = 0; week < weeks; week++) {
            for (let day = 0; day < days; day++) {
                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', week * (cellSize + cellGap));
                rect.setAttribute('y', day * (cellSize + cellGap) + 15);
                rect.setAttribute('width', cellSize);
                rect.setAttribute('height', cellSize);
                rect.setAttribute('rx', 2);

                const dateKey = `${week}-${day}`;
                const value = activityData[dateKey] || 0;

                if (value === 0) {
                    rect.setAttribute('fill', '#161b22');
                } else if (value <= 2) {
                    rect.setAttribute('fill', '#0e4429');
                } else if (value <= 5) {
                    rect.setAttribute('fill', '#006d32');
                } else if (value <= 8) {
                    rect.setAttribute('fill', '#26a641');
                } else {
                    rect.setAttribute('fill', '#39d353');
                }

                svg.appendChild(rect);
            }
        }

        container.innerHTML = '';
        container.appendChild(svg);
    }
}

// Экспорт
window.StatsCharts = StatsCharts;
