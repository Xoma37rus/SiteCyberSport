/**
 * Streaming — встраивание Twitch и YouTube плееров на страницы турниров
 */

class StreamingEmbed {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;
        this.channel = this.container.dataset.channel;
        this.platform = this.container.dataset.platform || 'twitch';
        this.height = this.container.dataset.height || 400;
        this.render();
    }

    render() {
        if (!this.channel) {
            this.container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 40px;">Стрим не настроен</p>';
            return;
        }

        let embedUrl = '';

        if (this.platform === 'twitch') {
            embedUrl = `https://player.twitch.tv/?channel=${this.channel}&parent=${window.location.hostname}&muted=true&autoplay=false`;
        } else if (this.platform === 'youtube') {
            embedUrl = `https://www.youtube.com/embed/${this.channel}?rel=0`;
        } else if (this.platform === 'trovo') {
            embedUrl = `https://player.trovo.live/player?channel=${this.channel}`;
        }

        this.container.innerHTML = `
            <div class="streaming-container" style="position: relative; width: 100%; padding-top: 56.25%; border-radius: 12px; overflow: hidden; background: #000;">
                <iframe
                    src="${embedUrl}"
                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;"
                    allowfullscreen
                    allow="autoplay; fullscreen"
                    loading="lazy"
                ></iframe>
                <div class="streaming-badge" style="
                    position: absolute;
                    top: 12px;
                    left: 12px;
                    background: ${this.platform === 'twitch' ? '#9146FF' : this.platform === 'youtube' ? '#FF0000' : '#00C2A8'};
                    color: white;
                    padding: 4px 12px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 700;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    z-index: 10;
                ">
                    <span style="
                        width: 8px;
                        height: 8px;
                        background: #f87171;
                        border-radius: 50%;
                        display: inline-block;
                        animation: pulse 1.5s infinite;
                    "></span>
                    LIVE
                </div>
            </div>
        `;
    }
}

/**
 * StreamingManager — управление несколькими стримами на странице
 */
class StreamingManager {
    constructor() {
        this.streams = [];
    }

    init() {
        document.querySelectorAll('.streaming-embed').forEach(container => {
            const stream = new StreamingEmbed(container.id);
            this.streams.push(stream);
        });
    }

    /**
     * Проверка, онлайн ли стрим (через Twitch API — нужен backend proxy)
     */
    async checkStreamStatus(channel, platform = 'twitch') {
        try {
            const response = await fetch(`/api/v1/streaming/status?channel=${channel}&platform=${platform}`);
            if (!response.ok) return { online: false };
            return await response.json();
        } catch (e) {
            return { online: false };
        }
    }

    /**
     * Переключение между несколькими стримами
     */
    switchStream(containerId, channel, platform = 'twitch') {
        const container = document.getElementById(containerId);
        if (container) {
            container.dataset.channel = channel;
            container.dataset.platform = platform;
            new StreamingEmbed(containerId);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.streamingManager = new StreamingManager();
    window.streamingManager.init();
});

window.StreamingEmbed = StreamingEmbed;
window.StreamingManager = StreamingManager;
