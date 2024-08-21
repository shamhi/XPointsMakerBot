import asyncio
import aiohttp
import requests
import random
from core.tapper import tap_tap, get_active_event, boost_level
from utils.logger import logger
from config import settings
from config.settings import *
import utils.geoip as geoip


async def get_profile(session, index):
    global user_data
    payload = {
        "webAppInitData": user_data[index]['init_data'],
        "userId": user_data[index]['id'],
    }
    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "Accept": "application/json",
        "User-Agent": user_data[index]['user-agent']
    }
    if user_data[index]['proxy'].lower() == "none":
        async with session.post("https://points-bot-api.bookmaker.xyz/get-profile", json=payload, headers=headers) as response:
            return await response.json()
    else:
        async with session.post("https://points-bot-api.bookmaker.xyz/get-profile", json=payload, headers=headers, proxy=user_data[index]['proxy']) as response:
            return await response.json()


async def login(session, index):
    url = "https://points-bot-api.bookmaker.xyz/start"
    payload = {
        "webAppInitData": user_data[index]['init_data'],
        "userId": user_data[index]['id'],
        "referralId": None,
        "username": user_data[index]['username']
    }
    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "Accept": "application/json",
        "User-Agent": user_data[index]['user-agent']
    }

    if user_data[index]['proxy'].lower() == "none":
        async with session.post(url, json=payload, headers=headers):
            ...
    else:
        async with session.post(url, json=payload, headers=headers, proxy=user_data[index]['proxy']):
            ...


async def parse_profile(profile_data, index):
    global user_data

    user_data[index]['level'] = profile_data['currentLevel']['level']
    user_data[index]['maxLevel'] = profile_data['maxLevel']
    user_data[index]['points'] = profile_data['points']
    # суммарное время ожиданий до вывод статистики
    user_data[index]['time_elapsed'] = 0
    user_data[index]['earn_point'] = 0  # добытые поинты за это время

    # nextLevel не существует если аккаунт прокачан до максимального уровня
    if profile_data['nextLevel']:
        user_data[index]['upgradeCost'] = profile_data['nextLevel']['upgradeCost']
    else:
        user_data[index]['upgradeCost'] = 0

    logger.success(f"{user_data[index]['username'][:15].ljust(15, ' ')} | <g>Get profile - ok.</g>"
                   f" | Balance: <c>{user_data[index]['points']:,}</c>"
                   f" | Level: <e>{user_data[index]['level']}/"
                   f"{user_data[index]['maxLevel']}</e>"
                   f" | Next: <y>{user_data[index]['upgradeCost']:,}</y>")


async def start(index):

    global tasks
    global user_data

    async with aiohttp.ClientSession() as session:

        tm_s = random.randint(settings.WAIT_LOGIN[0], settings.WAIT_LOGIN[1])

        if user_data[index]['proxy'].lower() != "none":
            ip_list = geoip.extract_ip_addresses(user_data[index]['proxy'])
            ip = ip_list[0]
        else:
            response = requests.get('https://ifconfig.me')
            ip = response.text
            await asyncio.sleep(3)

        geo_info = geoip.get_geo_info(ip)
        await asyncio.sleep(3)

        logger.info(f"{user_data[index]['username'][:15].ljust(15, ' ')} | <c>id [{index}]</c>"
                    f" | IP: {ip} - "
                    f"{geo_info.get('city')},{geo_info.get('country')}"
                    f" | <y>wait {tm_s} sec</y>")

        await asyncio.sleep(tm_s)

        await login(session, index)

        logger.success(
            f"{user_data[index]['username'][:15].ljust(15, ' ')} | <g>Authorization successful.</g>")

        profile_data = await get_profile(session, index)
        await asyncio.sleep(5)
        await parse_profile(profile_data, index)

        # добавим задачу проверки события и выполнение автоставок
        if settings.AUTO_BET == True:
            tasks.append(asyncio.create_task(
                loop_get_active_event(session, index)))

        # добавим задачу проверки и повышения уровня
        if settings.AUTO_UPGRADE == True and user_data[index]['level'] < 30:
            tasks.append(asyncio.create_task(loop_boost_level(session, index)))

        while True:
            # logger.info(f"[{index}] tap_tap")
            await tap_tap(session, index)


async def loop_get_active_event(session, index):
    while True:
        logger.info(f"{user_data[index]['username'][:15].ljust(15, ' ')}"
                    f" | Checking the possibility of making bets")
        await get_active_event(session, index)


async def loop_boost_level(session, index):
    while True:
        logger.info(f"{user_data[index]['username'][:15].ljust(15, ' ')}"
                    f" | Checking the possibility of level up")
        await boost_level(session, index)
