"""
Discord Bot Integration — уведомления, авторизация, команды
"""
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DiscordBotService:
    """Сервис для работы с Discord"""

    def __init__(self, token: str = "", client_id: str = "", client_secret: str = ""):
        self.token = token
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://discord.com/api/v10"

    @property
    def is_configured(self) -> bool:
        return bool(self.token)

    def get_oauth_url(self, redirect_uri: str, state: str = "") -> str:
        """URL для авторизации через Discord OAuth2"""
        from urllib.parse import urlencode
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "identify email",
            "state": state,
        }
        return f"{self.base_url}/oauth2/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Optional[dict]:
        """Обмен кода авторизации на токен доступа"""
        import httpx
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/oauth2/token", data=data)
            if resp.status_code == 200:
                return resp.json()
        return None

    async def get_user_info(self, access_token: str) -> Optional[dict]:
        """Получение информации о Discord пользователе"""
        import httpx
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/users/@me", headers=headers)
            if resp.status_code == 200:
                return resp.json()
        return None

    async def send_tournament_announcement(self, channel_id: str, tournament: dict):
        """Отправить анонс турнира в Discord канал"""
        if not self.is_configured:
            return
        import httpx
        embed = {
            "title": f"🏆 {tournament['name']}",
            "description": tournament.get('description', ''),
            "color": 0x00f0ff,
            "fields": [
                {"name": "Дисциплина", "value": tournament.get('discipline', 'N/A'), "inline": True},
                {"name": "Дата", "value": tournament.get('start_date', 'TBD'), "inline": True},
                {"name": "Команды", "value": f"{tournament.get('teams', 0)}/{tournament.get('max_teams', 0)}", "inline": True},
                {"name": "Призовой фонд", "value": tournament.get('prize_pool', 'N/A'), "inline": False},
            ],
            "footer": {"text": "EasyCyberPro"}
        }
        headers = {"Authorization": f"Bot {self.token}", "Content-Type": "application/json"}
        payload = {"embeds": [embed]}
        async with httpx.AsyncClient() as client:
            await client.post(f"{self.base_url}/channels/{channel_id}/messages", headers=headers, json=payload)

    async def send_match_notification(self, channel_id: str, match: dict):
        """Уведомление о результате матча"""
        if not self.is_configured:
            return
        import httpx
        winner = match.get('winner_name', 'N/A')
        score = f"{match.get('team1_score', 0)} - {match.get('team2_score', 0)}"
        embed = {
            "title": "⚔️ Результат матча",
            "description": f"**{match.get('team1', '?')}** {score} **{match.get('team2', '?')}**",
            "color": 0x34d399 if match.get('status') == 'completed' else 0xfbbf24,
            "fields": [
                {"name": "Победитель", "value": winner, "inline": True},
                {"name": "Турнир", "value": match.get('tournament', ''), "inline": True},
            ],
        }
        headers = {"Authorization": f"Bot {self.token}", "Content-Type": "application/json"}
        payload = {"embeds": [embed]}
        async with httpx.AsyncClient() as client:
            await client.post(f"{self.base_url}/channels/{channel_id}/messages", headers=headers, json=payload)

    async def send_rank_up_notification(self, channel_id: str, user: dict, new_level: int):
        """Поздравление с повышением уровня"""
        if not self.is_configured:
            return
        import httpx
        embed = {
            "title": "🎉 Новый уровень!",
            "description": f"**{user.get('username', 'Игрок')}** достиг **Level {new_level}**!",
            "color": 0xfbbf24,
            "thumbnail": {"url": user.get('avatar_url', '')},
            "fields": [
                {"name": "ELO", "value": str(user.get('elo', 0)), "inline": True},
                {"name": "Дисциплина", "value": user.get('discipline', ''), "inline": True},
            ],
        }
        headers = {"Authorization": f"Bot {self.token}", "Content-Type": "application/json"}
        payload = {"embeds": [embed]}
        async with httpx.AsyncClient() as client:
            await client.post(f"{self.base_url}/channels/{channel_id}/messages", headers=headers, json=payload)


# Глобальный экземпляр
discord_bot: Optional[DiscordBotService] = None

def init_discord_bot(token: str = "", client_id: str = "", client_secret: str = ""):
    """Инициализация Discord бота"""
    global discord_bot
    discord_bot = DiscordBotService(token=token, client_id=client_id, client_secret=client_secret)
    return discord_bot
