/**
 * Bracket Viewer - Компонент для визуализации турнирных сеток
 * Использование: new BracketViewer('.tournament-bracket', tournamentId);
 */

class BracketViewer {
    constructor(containerSelector, tournamentId = null) {
        this.container = document.querySelector(containerSelector);
        if (!this.container) {
            console.error('Bracket container not found');
            return;
        }
        
        this.tournamentId = tournamentId || this.container.dataset.tournamentId;
        this.zoom = 1;
        this.bracketData = null;
        
        this.init();
    }
    
    async init() {
        this.renderControls();
        await this.loadBracket();
        this.attachEventListeners();
        
        // Авто-обновление каждые 30 секунд
        this.autoRefreshInterval = setInterval(() => {
            this.loadBracket();
        }, 30000);
    }
    
    renderControls() {
        const controlsHtml = `
            <div class="bracket-controls">
                <button class="bracket-btn bracket-zoom-in" title="Увеличить">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        <line x1="11" y1="8" x2="11" y2="14"></line>
                        <line x1="8" y1="11" x2="14" y2="11"></line>
                    </svg>
                </button>
                <button class="bracket-btn bracket-zoom-out" title="Уменьшить">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        <line x1="8" y1="11" x2="14" y2="11"></line>
                    </svg>
                </button>
                <button class="bracket-btn bracket-reset" title="Сбросить масштаб">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
                        <path d="M3 3v5h5"></path>
                    </svg>
                </button>
                <button class="bracket-btn bracket-fullscreen" title="На весь экран">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
                    </svg>
                </button>
            </div>
        `;
        this.container.insertAdjacentHTML('afterbegin', controlsHtml);
    }
    
    async loadBracket() {
        if (!this.tournamentId) {
            this.container.querySelector('.bracket-container').innerHTML = 
                '<p style="color: var(--text-secondary); text-align: center;">Tournament ID not specified</p>';
            return;
        }
        
        try {
            const response = await fetch(`/api/v1/tournaments/${this.tournamentId}/bracket`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.bracketData = await response.json();
            this.render();
        } catch (error) {
            console.error('Failed to load bracket:', error);
            this.container.querySelector('.bracket-container').innerHTML = 
                `<p style="color: #f87171; text-align: center;">Ошибка загрузки сетки: ${error.message}</p>`;
        }
    }
    
    render() {
        if (!this.bracketData || !this.bracketData.rounds || this.bracketData.rounds.length === 0) {
            this.container.querySelector('.bracket-container').innerHTML = 
                '<p style="color: var(--text-secondary); text-align: center; padding: 40px;">🎮 Турнирная сетка ещё не сформирована</p>';
            return;
        }
        
        const container = this.container.querySelector('.bracket-container');
        if (!container) {
            const newContainer = document.createElement('div');
            newContainer.className = 'bracket-container';
            this.container.appendChild(newContainer);
        }
        
        let html = '';
        
        this.bracketData.rounds.forEach((round, roundIndex) => {
            html += `
                <div class="bracket-round">
                    <h4 class="round-name">${this.escapeHtml(round.name)}</h4>
                    <div class="round-matches">
            `;
            
            round.matches.forEach(match => {
                const team1 = match.team1;
                const team2 = match.team2;
                const isWinner1 = match.winner_id && team1 && match.winner_id === team1.id;
                const isWinner2 = match.winner_id && team2 && match.winner_id === team2.id;
                const isCompleted = match.status === 'completed';
                const isPending = match.status === 'pending';
                
                html += `
                    <div class="match ${match.status}" data-match-id="${match.id}">
                        <div class="match-team team-1 ${isWinner1 ? 'winner' : ''}">
                            <span class="team-name">${team1 ? this.escapeHtml(team1.name) : 'TBD'}</span>
                            <span class="team-score">${team1 ? team1.score : '-'}</span>
                        </div>
                        <div class="match-team team-2 ${isWinner2 ? 'winner' : ''}">
                            <span class="team-name">${team2 ? this.escapeHtml(team2.name) : 'TBD'}</span>
                            <span class="team-score">${team2 ? team2.score : '-'}</span>
                        </div>
                        ${match.next_match_id ? `<div class="match-connector" data-next="${match.next_match_id}"></div>` : ''}
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    attachEventListeners() {
        // Зум
        this.container.querySelector('.bracket-zoom-in').addEventListener('click', () => {
            this.zoom = Math.min(this.zoom * 1.2, 3);
            this.applyZoom();
        });
        
        this.container.querySelector('.bracket-zoom-out').addEventListener('click', () => {
            this.zoom = Math.max(this.zoom / 1.2, 0.5);
            this.applyZoom();
        });
        
        this.container.querySelector('.bracket-reset').addEventListener('click', () => {
            this.zoom = 1;
            this.applyZoom();
        });
        
        this.container.querySelector('.bracket-fullscreen').addEventListener('click', () => {
            this.toggleFullscreen();
        });
        
        // Клик на матч - показать детали
        this.container.querySelectorAll('.match').forEach(match => {
            match.addEventListener('click', (e) => {
                const matchId = e.currentTarget.dataset.matchId;
                this.showMatchDetails(matchId);
            });
        });
    }
    
    applyZoom() {
        const container = this.container.querySelector('.bracket-container');
        if (container) {
            container.style.transform = `scale(${this.zoom})`;
            container.style.transformOrigin = 'left center';
        }
    }
    
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            this.container.requestFullscreen().catch(err => {
                console.error('Error attempting to enable fullscreen:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }
    
    async showMatchDetails(matchId) {
        try {
            const response = await fetch(`/api/v1/matches/${matchId}`);
            if (!response.ok) return;
            
            const match = await response.json();
            
            // Создаём модалку
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
            `;
            
            modal.innerHTML = `
                <div class="modal-content" style="
                    background: var(--bg-card);
                    border-radius: 16px;
                    padding: 32px;
                    max-width: 500px;
                    width: 90%;
                    position: relative;
                ">
                    <button class="modal-close" style="
                        position: absolute;
                        top: 16px;
                        right: 16px;
                        background: none;
                        border: none;
                        color: var(--text-secondary);
                        font-size: 24px;
                        cursor: pointer;
                    ">&times;</button>
                    
                    <h3 style="color: var(--text-primary); margin-bottom: 20px;">
                        🎮 Детали матча
                    </h3>
                    
                    <div style="color: var(--text-secondary); margin-bottom: 16px;">
                        <div><strong>Раунд:</strong> ${this.escapeHtml(match.round)}</div>
                        <div><strong>Статус:</strong> ${this.escapeHtml(match.status)}</div>
                        ${match.scheduled_at ? `<div><strong>Запланирован:</strong> ${new Date(match.scheduled_at).toLocaleString()}</div>` : ''}
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 20px; background: var(--bg-secondary); border-radius: 12px;">
                        <div style="text-align: center;">
                            <div style="font-size: 24px; font-weight: 700; color: var(--accent-cyan);">${match.team1_score}</div>
                            <div style="color: var(--text-secondary); font-size: 14px;">Команда 1</div>
                        </div>
                        <div style="color: var(--text-secondary);">VS</div>
                        <div style="text-align: center;">
                            <div style="font-size: 24px; font-weight: 700; color: var(--accent-cyan);">${match.team2_score}</div>
                            <div style="color: var(--text-secondary); font-size: 14px;">Команда 2</div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Закрытие по клику на крестик или фон
            modal.querySelector('.modal-close').addEventListener('click', () => {
                modal.remove();
            });
            
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                }
            });
            
        } catch (error) {
            console.error('Failed to load match details:', error);
        }
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    destroy() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
    }
}

// Авто-инициализация для элементов с data-tournament-id
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.tournament-bracket[data-tournament-id]').forEach(container => {
        new BracketViewer(container);
    });
});

// Экспорт для использования в других скриптах
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BracketViewer;
}
