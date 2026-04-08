"""
WebSocket Manager — real-time уведомления и обновления
"""
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket
import json
import asyncio

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Управление WebSocket соединениями"""

    def __init__(self):
        # user_id -> set of WebSocket
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # tournament_id -> set of user_id (подписчики турнира)
        self.tournament_subscribers: Dict[int, Set[int]] = {}
        # match_id -> set of user_id (подписчики матча)
        self.match_subscribers: Dict[int, Set[int]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        """Подключить пользователя"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")

    def disconnect(self, user_id: int, websocket: WebSocket):
        """Отключить пользователя"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_personal_message(self, user_id: int, message: dict):
        """Отправить сообщение конкретному пользователю"""
        if user_id in self.active_connections:
            disconnected = set()
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.add(ws)
            # Удаляем мёртвые соединения
            for ws in disconnected:
                self.disconnect(user_id, ws)

    async def broadcast_tournament(self, tournament_id: int, message: dict):
        """Отправить обновление всем подписчикам турнира"""
        subscribers = self.tournament_subscribers.get(tournament_id, set())
        for user_id in subscribers:
            await self.send_personal_message(user_id, message)

    async def broadcast_match(self, match_id: int, message: dict):
        """Отправить обновление всем подписчикам матча"""
        subscribers = self.match_subscribers.get(match_id, set())
        for user_id in subscribers:
            await self.send_personal_message(user_id, message)

    def subscribe_tournament(self, user_id: int, tournament_id: int):
        """Подписаться на обновления турнира"""
        if tournament_id not in self.tournament_subscribers:
            self.tournament_subscribers[tournament_id] = set()
        self.tournament_subscribers[tournament_id].add(user_id)

    def unsubscribe_tournament(self, user_id: int, tournament_id: int):
        """Отписаться от турнира"""
        if tournament_id in self.tournament_subscribers:
            self.tournament_subscribers[tournament_id].discard(user_id)

    def subscribe_match(self, user_id: int, match_id: int):
        """Подписаться на обновления матча"""
        if match_id not in self.match_subscribers:
            self.match_subscribers[match_id] = set()
        self.match_subscribers[match_id].add(user_id)

    def get_online_users(self) -> Set[int]:
        """Получить список онлайн пользователей"""
        return set(self.active_connections.keys())

    def is_online(self, user_id: int) -> bool:
        """Проверить, онлайн ли пользователь"""
        return user_id in self.active_connections

    async def send_notification(self, user_id: int, notification_type: str, data: dict):
        """Универсальная отправка уведомления"""
        message = {
            "type": "notification",
            "notification_type": notification_type,
            "data": data,
            "timestamp": int(__import__('time').time())
        }
        await self.send_personal_message(user_id, message)


# Глобальный менеджер
ws_manager = WebSocketManager()
