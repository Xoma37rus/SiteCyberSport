"""
Комплексные тесты для новой функциональности EasyCyberPro v2.0

Тестируются:
1. Система рейтинга ELO
2. API endpoints для лидерборда
3. Матчмейкинг
4. Интеграция моделей
"""

import pytest
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    PlayerRating, RatingChange, MatchmakingQueue,
    User, Discipline, get_db, engine, Base
)
from utils import (
    get_level_by_elo, get_k_factor, calculate_expected_score,
    calculate_elo_change, calculate_team_elo_change,
    update_player_rating, get_or_create_rating, BASE_ELO,
    ELO_LEVELS
)
from schemas import (
    PlayerRatingResponse, RatingChangeResponse, LeaderboardResponse,
    LeaderboardItem, UserRatingsResponse, MatchmakingQueueResponse
)
from sqlalchemy.orm import Session
from datetime import datetime


# ==================== ТЕСТЫ ФОРМУЛ ELO ====================

class TestELOFormulas:
    """Тесты для функций расчёта ELO"""
    
    def test_get_level_by_elo_boundaries(self):
        """Проверка границ уровней"""
        assert get_level_by_elo(0) == 1
        assert get_level_by_elo(199) == 1
        assert get_level_by_elo(200) == 2
        assert get_level_by_elo(999) == 5
        assert get_level_by_elo(1000) == 6
        assert get_level_by_elo(1199) == 6
        assert get_level_by_elo(1200) == 7
        assert get_level_by_elo(1999) == 9
        assert get_level_by_elo(2000) == 10
        assert get_level_by_elo(3000) == 10
    
    def test_get_k_factor(self):
        """Проверка K-фактора"""
        assert get_k_factor(0) == 48    # Новый игрок
        assert get_k_factor(5) == 48    # Новый игрок
        assert get_k_factor(9) == 48    # Новый игрок
        assert get_k_factor(10) == 32   # Базовый
        assert get_k_factor(50) == 32   # Базовый
        assert get_k_factor(100) == 32  # Базовый (граничное значение)
        assert get_k_factor(101) == 16  # Опытный
        assert get_k_factor(200) == 16  # Опытный
    
    def test_calculate_expected_score(self):
        """Проверка расчёта ожидаемого счёта"""
        # Равные соперники
        assert abs(calculate_expected_score(1200, 1200) - 0.5) < 0.01
        
        # Игрок сильнее на 400 ELO
        assert abs(calculate_expected_score(1400, 1000) - 0.91) < 0.01
        
        # Игрок слабее на 400 ELO
        assert abs(calculate_expected_score(1000, 1400) - 0.09) < 0.01
        
        # Разница 200 ELO
        assert abs(calculate_expected_score(1200, 1000) - 0.76) < 0.01
    
    def test_calculate_elo_change_win_equal_opponent(self):
        """Победа над равным соперником"""
        change = calculate_elo_change(
            player_elo=1200,
            opponent_elo=1200,
            won=True,
            games_played=50
        )
        assert change > 0  # Положительное изменение
        assert change <= 32  # Не больше K-фактора
    
    def test_calculate_elo_change_loss_equal_opponent(self):
        """Поражение от равного соперника"""
        change = calculate_elo_change(
            player_elo=1200,
            opponent_elo=1200,
            won=False,
            games_played=50
        )
        assert change < 0  # Отрицательное изменение
        assert change >= -32  # Не больше K-фактора по модулю
    
    def test_calculate_elo_change_win_stronger_opponent(self):
        """Победа над более сильным соперником"""
        change = calculate_elo_change(
            player_elo=1000,
            opponent_elo=1400,
            won=True,
            games_played=50
        )
        assert change > 16  # Больше чем за победу над равным
        # Бонус за победу над сильным (+200 ELO разница)
        change_with_bonus = calculate_elo_change(
            player_elo=1000,
            opponent_elo=1300,
            won=True,
            games_played=50
        )
        assert change_with_bonus > change or change_with_bonus >= 25
    
    def test_calculate_elo_change_new_player(self):
        """Изменение для нового игрока (< 10 игр)"""
        change_new = calculate_elo_change(
            player_elo=1000,
            opponent_elo=1000,
            won=True,
            games_played=5  # Новый игрок
        )
        change_exp = calculate_elo_change(
            player_elo=1000,
            opponent_elo=1000,
            won=True,
            games_played=50  # Опытный игрок
        )
        assert change_new > change_exp  # Новый игрок получает больше ELO
    
    def test_calculate_team_elo_change(self):
        """Расчёт для командной игры"""
        team_change = calculate_team_elo_change(
            team_avg_elo=1200,
            opponent_avg_elo=1200,
            won=True
        )
        # Для командной игры изменение меньше (делится на 5)
        individual_change = calculate_elo_change(
            player_elo=1200,
            opponent_elo=1200,
            won=True,
            is_team_game=False
        )
        assert abs(team_change) < abs(individual_change)


# ==================== ТЕСТЫ СХЕМ PYDANTIC ====================

class TestPydanticSchemas:
    """Тесты для Pydantic схем"""
    
    def test_player_rating_response(self):
        """Проверка схемы PlayerRatingResponse"""
        rating = PlayerRatingResponse(
            id=1,
            user_id=1,
            discipline_id=1,
            elo=1200,
            level=7,
            games_played=50,
            wins=30,
            losses=20,
            draws=0,
            peak_elo=1250,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            win_rate=60.0,
            progress_to_next_level=50.0
        )
        assert rating.elo == 1200
        assert rating.level == 7
        assert rating.win_rate == 60.0
    
    def test_leaderboard_item(self):
        """Проверка схемы LeaderboardItem"""
        item = LeaderboardItem(
            rank=1,
            user_id=1,
            username="ProPlayer",
            elo=2000,
            level=10,
            games_played=100,
            wins=70,
            losses=30,
            win_rate=70.0,
            peak_elo=2100
        )
        assert item.rank == 1
        assert item.level == 10
        assert item.win_rate == 70.0
    
    def test_matchmaking_queue_response(self):
        """Проверка схемы MatchmakingQueueResponse"""
        response = MatchmakingQueueResponse(
            status="waiting",
            game_type="1v1",
            elo=1200,
            queued_at=datetime.utcnow(),
            wait_time=0,
            estimated_time=300
        )
        assert response.status == "waiting"
        assert response.game_type == "1v1"


# ==================== ТЕСТЫ УРОВНЕЙ ====================

class TestLevels:
    """Тесты для системы уровней"""
    
    def test_all_levels_defined(self):
        """Проверка что все 10 уровней определены"""
        assert len(ELO_LEVELS) == 10
        assert 1 in ELO_LEVELS
        assert 10 in ELO_LEVELS
    
    def test_level_ranges_continuous(self):
        """Проверка непрерывности диапазонов уровней"""
        prev_max = -1
        for level in range(1, 11):
            min_elo, max_elo = ELO_LEVELS[level]
            assert min_elo == prev_max + 1, f"Gap before level {level}"
            prev_max = max_elo
    
    def test_level_10_infinite(self):
        """Проверка что Level 10 бесконечный"""
        min_elo, max_elo = ELO_LEVELS[10]
        assert min_elo == 2000
        assert max_elo == float('inf')


# ==================== ИНТЕГРАЦИОННЫЕ ТЕСТЫ ====================

class TestIntegration:
    """Интеграционные тесты"""
    
    def test_database_models_creation(self):
        """Проверка создания моделей БД"""
        # Проверяем что таблицы существуют
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        assert 'player_ratings' in tables
        assert 'rating_changes' in tables
        assert 'matchmaking_queue' in tables
    
    def test_player_rating_properties(self):
        """Проверка свойств PlayerRating"""
        rating = PlayerRating(
            user_id=1,
            discipline_id=1,
            elo=1500,
            level=8,
            games_played=100,
            wins=60,
            losses=40,
            draws=0
        )
        
        # Проверяем вычисляемые свойства
        assert rating.win_rate == 60.0
        assert rating.progress_to_next_level == (1500 % 200) / 2  # 100/200 = 50%
    
    def test_rating_change_creation(self):
        """Проверка создания RatingChange"""
        change = RatingChange(
            user_id=1,
            discipline_id=1,
            elo_before=1200,
            elo_after=1216,
            elo_change=16,
            reason="win"
        )
        
        assert change.elo_change == 16
        assert change.reason == "win"
        assert change.elo_after > change.elo_before


# ==================== ТЕСТЫ API ENDPOINTS (MOCK) ====================

class TestAPIEndpoints:
    """Тесты для API endpoints (без запуска сервера)"""
    
    def test_leaderboard_endpoint_exists(self):
        """Проверка что endpoint лидерборда существует"""
        from api import router
        routes = [route.path for route in router.routes]
        
        assert '/api/v1/leaderboard' in routes
        assert '/api/v1/leaderboards' in routes
        assert '/api/v1/users/{user_id}/ratings' in routes
    
    def test_matchmaking_endpoints_exist(self):
        """Проверка что endpoints матчмейкинга существуют"""
        from api import router
        routes = [route.path for route in router.routes]
        
        assert '/api/v1/matchmaking/queue' in routes
        assert '/api/v1/matchmaking/status' in routes
    
    def test_bracket_endpoint_exists(self):
        """Проверка что endpoint bracket существует"""
        from api import router
        routes = [route.path for route in router.routes]
        
        assert '/api/v1/tournaments/{tournament_id}/bracket' in routes


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
