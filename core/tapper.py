import asyncio
import aiohttp
from parsel import Selector
from playwright.async_api import async_playwright
from w3lib.url import add_or_replace_parameter
import sys
import os
import random
import time
from datetime import datetime, timezone
from utils.logger import *
from config import settings
from config.settings import user_data, tasks


async def tap_tap(session: aiohttp.ClientSession, index):

    global user_data

    payload = {
        "webAppInitData": user_data[index]["init_data"],
        "userId": user_data[index]["id"],
    }
    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "Accept": "application/json",
        "User-Agent": user_data[index]["user-agent"],
    }
    url = f"https://points-bot-api.bookmaker.xyz/tap-coin?t="
    url += f"{int(time.time() * 1000)}"

    try:
        tap_wait_ms = random.randint(settings.WAIT_TAP[0], settings.WAIT_TAP[1])

        if user_data[index]["points"] > settings.MAX_TAP_POINT:
            await asyncio.sleep(3600)
            return

        if user_data[index]["proxy"].lower() == "none":
            async with session.post(
                url, headers=headers, json=payload, ssl=settings.ENABLED_SSL
            ) as response:
                result = await response.json()
        else:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                proxy=user_data[index]["proxy"],
                ssl=settings.ENABLED_SSL,
            ) as response:
                result = await response.json()

        if response.status == 200 and result["points"] > 0:
            user_data[index]["earn_point"] += int(result["points"])
            user_data[index]["time_elapsed"] += tap_wait_ms
            await asyncio.sleep(tap_wait_ms / 1000)

        await asyncio.sleep(tap_wait_ms / 1000)

        if user_data[index]["time_elapsed"] >= settings.CYCLE_PRINT_TAP * 1000:
            user_data[index]["points"] += user_data[index]["earn_point"]
            logger.success(
                f"{user_data[index]['username'][:15].ljust(15, ' ')} | Successful tapped!"
                f" | Balanc: <c>{user_data[index]['points']:,}</c>"
                f" (+<g>{user_data[index]['earn_point']}</g>)"
                f" of <y>{int(user_data[index]['time_elapsed']/1000)}</y> sec"
            )
            user_data[index]["earn_point"] = 0
            user_data[index]["time_elapsed"] = 0

    except Exception as e:
        logger.error(
            f"{user_data[index]['username'][:15].ljust(15, ' ')}" f" | Error: {e}"
        )
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.info(f"{exc_type}: {exc_obj} | {fname} | {exc_tb.tb_lineno}")


async def get_active_event(session: aiohttp.ClientSession, index):
    payload = {
        "webAppInitData": user_data[index]["init_data"],
        "userId": user_data[index]["id"],
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": user_data[index]["user-agent"],
    }
    url = f"https://points-bot-api.bookmaker.xyz/get-active-event"

    if user_data[index]["proxy"].lower() == "none":
        async with session.post(
            url, headers=headers, json=payload, ssl=settings.ENABLED_SSL
        ) as response:
            result = await response.json()
    else:
        async with session.post(
            url,
            headers=headers,
            json=payload,
            proxy=user_data[index]["proxy"],
            ssl=settings.ENABLED_SSL,
        ) as response:
            result = await response.json()

    if response.status == 200:
        if result["event"] == None:
            # Преобразуем время в тайм-штамп
            time_obj = datetime.strptime(
                result["nextBetAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
            ).astimezone(None)
            # Получаем текущее время по UTC
            time_utc = datetime.now().astimezone(timezone.utc)
            # Считаем дельту учитывая время вашей таймзоны
            time_sleep = int(
                time_obj.timestamp()
                - time_utc.timestamp()
                + time_obj.utcoffset().total_seconds()
            )

            # Добавим еще 10 минут к ожиданию для подстраховки
            time_sleep += 600

            logger.info(
                f"{user_data[index]['username'][:15].ljust(15, ' ')}"
                f" | Sleep {time_sleep:,} sec of bet..."
            )
            await asyncio.sleep(time_sleep)

        else:

            user_data[index]["event"] = result["event"]

            sport = user_data[index]["event"]["sport"]["name"]
            league = user_data[index]["event"]["league"]["name"]
            p1 = user_data[index]["event"]["participants"][0]["name"]
            p2 = user_data[index]["event"]["participants"][1]["name"]

            logger.info(
                f"{user_data[index]['username'][:15].ljust(15, ' ')} | <g>Event:</g> {sport} - {league} / "
                f"<c>{p1} : {p2}</c>"
            )

            await set_place_bet(session, index)
            await asyncio.sleep(17)


async def get_url_event(index):

    global user_data

    # Пример ссылки события https://bookmaker.xyz/polygon/sports/football/argentina/liga-pro/1001000000001595064468
    url = f"https://bookmaker.xyz/polygon/sports"
    url += f"/{user_data[index]['event']['sport']['slug']}"
    url += f"/{user_data[index]['event']['league']['country']['slug']}"
    url += f"/{user_data[index]['event']['league']['slug']}"
    url += f"/{user_data[index]['event']['gameId']}"

    # Данные, которые будут отправлены вместе с запросом
    data = {
        "utm_source": "tgbot",
        "utm_medium": "tgbot",
        "utm_campaign": "xpointmaker",
        "utm_content": "bottom",
    }

    for key, value in data.items():
        url = add_or_replace_parameter(url, key, value)

    try:
        if settings.BET_PROXY != None:
            proxy = {"server": settings.BET_PROXY}
            if settings.BET_PROXY_LOGIN:
                proxy["username"] = settings.BET_PROXY_LOGIN
            if settings.BET_PROXY_PASS:
                proxy["password"] = settings.BET_PROXY_PASS

        async with async_playwright() as p:

            if settings.BET_PROXY != None:
                browser = await p.chromium.launch(headless=True, proxy=proxy)
            else:
                browser = await p.chromium.launch(headless=True)

            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_load_state("networkidle")

            bet_id = user_data[index]["event"]["conditionId"]

            html_content = await page.content()
            selector = Selector(html_content)
            data = (
                selector.xpath(f'//button[contains(@data-condition-id, "{bet_id}")]')
                .xpath(".//span/text()")
                .getall()
            )
            await browser.close()

        bet_outcomes = user_data[index]["event"]["outcomesIds"]
        bet_outcomes.sort()
        bet_coeff = data[0 : len(bet_outcomes) : 1]
        outcomeId = bet_outcomes[bet_coeff.index(min(bet_coeff))]

        logger.info(
            f"{user_data[index]['username'][:15].ljust(15, ' ')}"
            f" | <g>Event:</g> Bet to outcome ID=<c>{outcomeId}</c> best Coeff=<c>{min(bet_coeff)}</c>"
        )

        return outcomeId

    except Exception as e:
        logger.error(
            f"{user_data[index]['username'][:15].ljust(15, ' ')}" f" | Error: {e}"
        )
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.info(f"{exc_type}: {exc_obj} | {fname} | {exc_tb.tb_lineno}")
        return None


async def set_place_bet(session: aiohttp.ClientSession, index):

    outcomeId = await get_url_event(index)
    if not outcomeId:
        # случайная ставка
        n = random.randint(0, len(user_data[index]["event"]["outcomesIds"]) - 1)
        outcomeId = user_data[index]["event"]["outcomesIds"][n]

    payload = {
        "webAppInitData": user_data[index]["init_data"],
        "userId": user_data[index]["id"],
        "conditionId": user_data[index]["event"]["conditionId"],
        "outcomeId": outcomeId,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": user_data[index]["user-agent"],
    }

    url = f"https://points-bot-api.bookmaker.xyz/place-bet"

    if user_data[index]["proxy"].lower() == "none":
        async with session.post(
            url, headers=headers, json=payload, ssl=settings.ENABLED_SSL
        ) as response:
            ...
    else:
        async with session.post(
            url,
            headers=headers,
            json=payload,
            proxy=user_data[index]["proxy"],
            ssl=settings.ENABLED_SSL,
        ) as response:
            ...

    if response.status == 200:
        logger.success(
            f"{user_data[index]['username'][:15].ljust(15, ' ')} | <g>Bet is accept server</g>"
            f" | ID: <c>{user_data[index]['event']['conditionId']}</c>"
        )
    else:
        logger.error(
            f"{user_data[index]['username'][:15].ljust(15, ' ')} | <r>Bet is disabled on server</r>"
            f" | <c>Response status: {response.status}</c>"
        )


async def boost_level(session: aiohttp.ClientSession, index):

    from core.registrator import get_profile, parse_profile

    global tasks

    if settings.AUTO_UPGRADE != True or user_data[index]["level"] == 30:
        await asyncio.sleep(600)
        return

    if user_data[index]["points"] < user_data[index]["upgradeCost"]:
        await asyncio.sleep(settings.CYCLE_PRINT_TAP * 10)
        return

    payload = {
        "webAppInitData": user_data[index]["init_data"],
        "userId": user_data[index]["id"],
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": user_data[index]["user-agent"],
    }

    url = f"https://points-bot-api.bookmaker.xyz/boost-level"

    if user_data[index]["proxy"].lower() == "none":
        async with session.post(
            url, headers=headers, json=payload, ssl=settings.ENABLED_SSL
        ) as response:
            ...
    else:
        async with session.post(
            url,
            headers=headers,
            json=payload,
            proxy=user_data[index]["proxy"],
            ssl=settings.ENABLED_SSL,
        ) as response:
            ...

    await asyncio.sleep(15)

    if response.status == 200:
        logger.success(
            f"{user_data[index]['username'][:15].ljust(15, ' ')} | <g>Level up</g>"
        )
        # Обновим данные профиля
        profile_data = await get_profile(session, index)
        await asyncio.sleep(15)
        await parse_profile(profile_data, index)
        await asyncio.sleep(60)

        # Сделаем ставки
        for _ in range(4):
            await get_active_event(session, index)
            await asyncio.sleep(15)

    else:
        logger.error(
            f"{user_data[index]['username'][:15].ljust(15, ' ')}"
            f" | <r>Level up is disabled on server</r>"
        )
