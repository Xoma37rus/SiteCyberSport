"""
Нагрузочное тестирование EasyCyberPro

Тестирует:
1. Главную страницу
2. API endpoints
3. Таблицу лидеров
4. Профиль пользователя
"""

import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

BASE_URL = "http://localhost:8000"

# Endpoints для тестирования
ENDPOINTS = [
    ("GET", "/"),
    ("GET", "/health"),
    ("GET", "/news"),
    ("GET", "/tournaments"),
    ("GET", "/leaderboard?discipline=dota2"),
    ("GET", "/api/v1/disciplines"),
    ("GET", "/api/v1/tournaments"),
    ("GET", "/api/v1/leaderboard?discipline=dota2"),
    ("GET", "/docs"),
]


def make_request(method, endpoint):
    """Выполнение одного запроса"""
    url = f"{BASE_URL}{endpoint}"
    try:
        start_time = time.time()
        if method == "GET":
            response = requests.get(url, timeout=10)
        elapsed = time.time() - start_time
        return {
            "endpoint": endpoint,
            "status": response.status_code,
            "time": elapsed,
            "success": response.status_code == 200
        }
    except Exception as e:
        return {
            "endpoint": endpoint,
            "status": 0,
            "time": 0,
            "success": False,
            "error": str(e)
        }


def load_test(num_requests=100, concurrent_users=10):
    """Нагрузочное тестирование"""
    print(f"\n🚀 Нагрузочное тестирование")
    print(f"   Запросов: {num_requests}")
    print(f"   Параллельных пользователей: {concurrent_users}")
    print(f"   URL: {BASE_URL}")
    print("="*60)
    
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = []
        for i in range(num_requests):
            method, endpoint = ENDPOINTS[i % len(ENDPOINTS)]
            futures.append(executor.submit(make_request, method, endpoint))
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)
            
            if i % 20 == 0:
                print(f"   Прогресс: {i}/{num_requests} запросов")
    
    total_time = time.time() - start_time
    
    # Статистика
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    times = [r["time"] for r in successful]
    
    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТА")
    print("="*60)
    
    print(f"\n⏱️  Время выполнения: {total_time:.2f} сек")
    print(f"📈 Запросов в секунду: {num_requests/total_time:.2f} req/s")
    
    print(f"\n✅ Успешных: {len(successful)} ({len(successful)/num_requests*100:.1f}%)")
    print(f"❌ Ошибок: {len(failed)} ({len(failed)/num_requests*100:.1f}%)")
    
    if times:
        print(f"\n📊 Статистика времени ответа:")
        print(f"   Мин: {min(times)*1000:.2f} мс")
        print(f"   Макс: {max(times)*1000:.2f} мс")
        print(f"   Среднее: {statistics.mean(times)*1000:.2f} мс")
        print(f"   Медиана: {statistics.median(times)*1000:.2f} мс")
        print(f"   95-й перцентиль: {statistics.quantiles(times, n=100)[94]*1000:.2f} мс")
    
    # Статистика по endpoint'ам
    print("\n📊 По endpoint'ам:")
    endpoint_stats = {}
    for r in results:
        ep = r["endpoint"]
        if ep not in endpoint_stats:
            endpoint_stats[ep] = {"success": 0, "failed": 0, "times": []}
        if r["success"]:
            endpoint_stats[ep]["success"] += 1
            endpoint_stats[ep]["times"].append(r["time"])
        else:
            endpoint_stats[ep]["failed"] += 1
    
    for ep, stats in sorted(endpoint_stats.items()):
        avg_time = statistics.mean(stats["times"])*1000 if stats["times"] else 0
        print(f"   {ep}: ✅{stats['success']} ❌{stats['failed']} ({avg_time:.0f} мс)")
    
    if failed:
        print("\n❌ Ошибки:")
        for f in failed[:5]:
            error_msg = f.get('error', f"status={f['status']}")
            print(f"   {f['endpoint']}: {error_msg}")
    
    print("\n" + "="*60)
    
    # Оценка результата
    success_rate = len(successful)/num_requests*100
    avg_response = statistics.mean(times)*1000 if times else 0
    
    if success_rate >= 95 and avg_response < 500:
        print("✅ ОТЛИЧНО: Все тесты пройдены успешно!")
    elif success_rate >= 90 and avg_response < 1000:
        print("✅ ХОРОШО: Незначительные задержки")
    elif success_rate >= 80:
        print("⚠️  НОРМАЛЬНО: Есть проблемы с производительностью")
    else:
        print("❌ ПЛОХО: Критические проблемы с доступностью")
    
    return {
        "total_requests": num_requests,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": success_rate,
        "requests_per_second": num_requests/total_time,
        "avg_response_ms": avg_response,
        "total_time": total_time
    }


if __name__ == "__main__":
    # Проверка доступности сервера
    print("🔍 Проверка доступности сервера...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Сервер доступен")
        else:
            print(f"❌ Сервер вернул статус {response.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ Сервер недоступен: {e}")
        print("   Убедитесь что сервер запущен: uvicorn main:app --host 0.0.0.0 --port 8000")
        exit(1)
    
    # Запуск теста
    load_test(num_requests=100, concurrent_users=10)
    
    print("\n💡 Для более серьёзного теста используйте:")
    print("   pip install locust")
    print("   locust -f locustfile.py --host=http://localhost:8000")
