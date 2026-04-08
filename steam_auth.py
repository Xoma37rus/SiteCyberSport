"""
Steam Authentication Integration
Авторизация через Steam OpenID + получение данных из Steam Web API
"""
import hashlib
import time
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode, parse_qs

import httpx
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from jose import jwt

from models import User, get_db
from config import settings
from auth import create_access_token, get_current_user_from_cookie

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/steam", tags=["steam-auth"])

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
STEAM_API_BASE = "https://api.steampowered.com"


def get_steam_api_key() -> str:
    """Получить Steam API ключ из настроек"""
    return getattr(settings, 'steam_api_key', '')


@router.get("/login")
async def steam_login(request: Request):
    """Перенаправление на Steam OpenID для авторизации"""
    return_url = str(request.url_for('steam_callback'))

    params = {
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.mode': 'checkid_setup',
        'openid.return_to': return_url,
        'openid.realm': settings.app_url,
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
    }

    steam_url = f"{STEAM_OPENID_URL}?{urlencode(params)}"
    return RedirectResponse(url=steam_url)


@router.get("/callback")
async def steam_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """Обработка ответа от Steam OpenID"""
    params = dict(request.query_params)

    # Проверяем валидность ответа
    is_valid = await verify_steam_openid(params)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Неверный ответ от Steam")

    # Извлекаем Steam ID
    steam_id_64 = extract_steam_id(params)
    if not steam_id_64:
        raise HTTPException(status_code=400, detail="Не удалось получить Steam ID")

    # Получаем информацию о пользователе из Steam API
    steam_user_info = await get_steam_user_info(steam_id_64)

    # Ищем или создаём пользователя
    user = db.query(User).filter(
        User.steam_id_64 == steam_id_64
    ).first()

    if not user:
        # Проверяем, привязан ли этот Steam ID к другому аккаунту
        from models import SteamUser as SteamUserModel
        steam_link = db.query(SteamUserModel).filter(
            SteamUserModel.steam_id_64 == steam_id_64
        ).first()

        if steam_link:
            user = db.query(User).filter(User.id == steam_link.user_id).first()
        else:
            # Создаём нового пользователя
            username = steam_user_info.get('personaname', f'steam_{steam_id_64[-6:]}')
            user = User(
                email=f"steam_{steam_id_64}@easycyberpro.local",
                username=username,
                hashed_password="",  # Steam auth — без пароля
                is_verified=True,
                is_active=True,
                steam_id_64=steam_id_64,
                avatar_url=steam_user_info.get('avatarfull', ''),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    # Создаём JWT токен
    access_token = create_access_token(
        data={"sub": user.email, "type": "access"}
    )

    response = RedirectResponse(url="/dashboard")
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,
        path="/",
        samesite="lax"
    )
    return response


@router.get("/link")
async def link_steam_account(
    request: Request,
    db: Session = Depends(get_db)
):
    """Привязка Steam аккаунта к существующему пользователю"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    return_url = f"{settings.app_url}/auth/steam/link-callback"
    params = {
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.mode': 'checkid_setup',
        'openid.return_to': return_url,
        'openid.realm': settings.app_url,
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
    }

    steam_url = f"{STEAM_OPENID_URL}?{urlencode(params)}"
    return RedirectResponse(url=steam_url)


@router.get("/link-callback")
async def steam_link_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """Обработка привязки Steam аккаунта"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    params = dict(request.query_params)
    steam_id_64 = extract_steam_id(params)

    if not steam_id_64:
        return RedirectResponse(url="/settings?error=steam_id_not_found")

    # Проверяем, не привязан ли к другому пользователю
    existing = db.query(User).filter(
        User.steam_id_64 == steam_id_64,
        User.id != current_user.id
    ).first()

    if existing:
        return RedirectResponse(url="/settings?error=steam_already_linked")

    # Привязываем
    current_user.steam_id_64 = steam_id_64
    db.commit()

    return RedirectResponse(url="/settings?success=steam_linked")


async def verify_steam_openid(params: Dict[str, str]) -> bool:
    """Верификация OpenID ответа от Steam"""
    verification_params = {
        'openid.assoc_handle': params.get('openid.assoc_handle', ''),
        'openid.signed': params.get('openid.signed', ''),
        'openid.sig': params.get('openid.sig', ''),
        'openid.ns': params.get('openid.ns', ''),
        'openid.mode': 'check_authentication',
    }

    signed_fields = params.get('openid.signed', '').split(',')
    for field in signed_fields:
        key = f'openid.{field}'
        if key in params:
            verification_params[key] = params[key]

    async with httpx.AsyncClient() as client:
        response = await client.post(STEAM_OPENID_URL, data=verification_params)
        return 'is_valid:true' in response.text


def extract_steam_id(params: Dict[str, str]) -> Optional[str]:
    """Извлечение Steam ID 64 из OpenID ответа"""
    claimed_id = params.get('openid.claimed_id', '')
    if '/id/' in claimed_id:
        return claimed_id.split('/id/')[-1]
    return None


async def get_steam_user_info(steam_id_64: str) -> Dict[str, Any]:
    """Получение информации о пользователе из Steam API"""
    api_key = get_steam_api_key()
    if not api_key:
        return {'personaname': f'Steam_{steam_id_64[-6:]}', 'avatarfull': ''}

    url = f"{STEAM_API_BASE}/ISteamUser/GetPlayerSummaries/v0002/"
    params = {
        'key': api_key,
        'steamids': steam_id_64,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

    players = data.get('response', {}).get('players', [])
    if players:
        return players[0]

    return {'personaname': f'Steam_{steam_id_64[-6:]}', 'avatarfull': ''}


async def get_cs2_match_history(steam_id_64: str, match_id: str = None) -> Dict[str, Any]:
    """Получение истории матчей CS2"""
    api_key = get_steam_api_key()
    if not api_key:
        return {}

    url = f"{STEAM_API_BASE}/IPlayerService/GetRecentlyPlayedGames/v0001/"
    params = {'key': api_key, 'steamid': steam_id_64}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()


async def get_dota2_match_history(steam_id_64: str, hero_id: int = None) -> Dict[str, Any]:
    """Получение истории матчей Dota 2"""
    api_key = get_steam_api_key()
    if not api_key:
        return {}

    url = f"{STEAM_API_BASE}/IDOTA2Match_570/GetMatchHistory/V001/"
    params = {'key': api_key, 'account_id': int(steam_id_64) & 0xFFFFFFFF}
    if hero_id:
        params['hero_id'] = hero_id

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()


async def get_match_details_dota2(match_id: str) -> Dict[str, Any]:
    """Получение деталей матча Dota 2"""
    api_key = get_steam_api_key()
    if not api_key:
        return {}

    url = f"{STEAM_API_BASE}/IDOTA2Match_570/GetMatchDetails/V001/"
    params = {'key': api_key, 'match_id': match_id}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()


async def verify_dota2_match_result(
    match_id: str,
    team1_steam_ids: list,
    team2_steam_ids: list,
    expected_winner_team: int
) -> bool:
    """Верификация результата матча Dota 2 через Steam API"""
    details = await get_match_details_dota2(match_id)
    if not details or 'result' not in details.get('result', {}):
        return False

    match = details['result']
    radiant_win = match.get('radiant_win', False)

    # Проверяем, совпадает ли победитель
    # team 2 = Radiant, team 3 = Dire
    actual_winner = 2 if radiant_win else 3
    return actual_winner == expected_winner
