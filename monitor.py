import asyncio
import aiohttp
from aiogram import Bot


def _format_date_for_api(iso_date: str) -> str:
    """2026-05-30 → 30.05.2026"""
    y, m, d = iso_date.split("-")
    return f"{d}.{m}.{y}"


async def _fetch_schedule(session: aiohttp.ClientSession, url: str) -> dict[str, int] | None:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            print(f"[FETCH] {url} → HTTP {resp.status}")
            if resp.status != 200:
                return None
            data = await resp.json(content_type=None)
            if data.get("result") != "success":
                print(f"[FETCH] result != success: {data.get('result')}")
                return None
            schedule = {item["time"]: int(item["count"]) for item in data.get("schedule", [])}
            print(f"[FETCH] Расписание получено: {schedule}")
            return schedule
    except Exception as e:
        print(f"[FETCH] Ошибка запроса {url}: {e}")
        return None


async def run_monitor(bot: Bot, get_db_func) -> None:
    print("[MONITOR] Монитор запущен")
    snapshots: dict[tuple, dict[str, int]] = {}

    async with aiohttp.ClientSession() as http:
        while True:
            print("[MONITOR] Новый цикл проверки")

            all_params = []
            async for session in get_db_func():
                try:
                    from repositories.user_requests import UserRequestsRepository
                    all_params = await UserRequestsRepository.get_monitor_params(session)
                    print(f"[MONITOR] Активных заявок: {len(all_params)}")
                    for p in all_params:
                        print(
                            f"[MONITOR] Заявка: telegram_id={p['telegram_id']}, "
                            f"dates={p['dates']}, slots={p['time_slots']}, "
                            f"seats={p['seats_count']}, url={p['base_url']}")
                except Exception as e:
                    print(f"[MONITOR] Ошибка получения заявок: {e}")

            if not all_params:
                print("[MONITOR] Нет активных заявок, жду...")
                await asyncio.sleep(30)
                continue

            for entry in all_params:
                telegram_id = entry["telegram_id"]
                base_url    = entry["base_url"]
                time_slots  = set(entry["time_slots"])
                seats_needed = entry["seats_count"]

                print(f"[MONITOR] Обрабатываю telegram_id={telegram_id}, слоты={time_slots}")

                for iso_date in entry["dates"]:
                    url = base_url + _format_date_for_api(iso_date)
                    key = (telegram_id, url)

                    print(f"[MONITOR] Запрашиваю: {url}")
                    current = await _fetch_schedule(http, url)

                    if current is None:
                        print(f"[MONITOR] Пустой ответ для {url}, пропускаю")
                        continue

                    prev = snapshots.get(key)
                    if prev is None:
                        print(f"[MONITOR] Первый снимок для {url}, запоминаю")
                        snapshots[key] = current

                        # Сразу уведомляем если места уже есть в нужных слотах
                        for time_str in time_slots:
                            count = current.get(time_str)
                            if count and count >= seats_needed:
                                msg = (
                                    f"🟢 Места уже есть!\n"
                                    f"📅 {iso_date}  🕐 {time_str}\n"
                                    f"💺 Мест: {count}\n\n"
                                    f"🔕 /stop — остановить уведомления\n"
                                    f"🔄 /start — изменить заявку"
                                )
                                print(f"[MONITOR] Уведомление о существующих местах: {msg}")
                                try:
                                    await bot.send_message(chat_id=telegram_id, text=msg)
                                except Exception as e:
                                    print(f"[MONITOR] Ошибка отправки {telegram_id}: {e}")
                        continue

                    print(f"[MONITOR] Сравниваю снимки для {url}")
                    for time_str in time_slots:
                        old_count = prev.get(time_str)
                        new_count = current.get(time_str)

                        if old_count is None:
                            print(f"[MONITOR] Слот {time_str} отсутствует в предыдущем снимке")
                            continue
                        if new_count is None:
                            print(f"[MONITOR] Слот {time_str} отсутствует в текущем снимке")
                            continue

                        print(f"[MONITOR] {time_str}: было={old_count}, стало={new_count}")

                        if new_count != old_count:
                            if new_count > old_count and new_count >= seats_needed:
                                msg = (
                                    f"🟢 Появились места!\n"
                                    f"📅 {iso_date}  🕐 {time_str}\n"
                                    f"💺 Мест: {old_count} → {new_count}\n\n"
                                    f"🔕 /stop — остановить уведомления\n"
                                    f"🔄 /start — изменить заявку"
                                )
                            else:
                                msg = (
                                    f"🔴 Место занято!\n"
                                    f"📅 {iso_date}  🕐 {time_str}\n"
                                    f"💺 Мест: {old_count} → {new_count}\n\n"
                                    f"🔕 /stop — остановить уведомления\n"
                                    f"🔄 /start — изменить заявку"
                                )
                            print(f"[MONITOR] Отправляю уведомление: {msg}")
                            try:
                                await bot.send_message(chat_id=telegram_id, text=msg)
                            except Exception as e:
                                print(f"[MONITOR] Ошибка отправки {telegram_id}: {e}")

                    snapshots[key] = current

            # Чистим старые снимки
            active_keys = {
                (e["telegram_id"], e["base_url"] + _format_date_for_api(d))
                for e in all_params
                for d in e["dates"]
            }
            for key in list(snapshots):
                if key not in active_keys:
                    del snapshots[key]

            print("[MONITOR] Цикл завершён, жду 30 сек")
            await asyncio.sleep(30)