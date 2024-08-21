import json
import urllib.parse
from utils.logger import logger
from config import settings
from config.settings import user_data

banner = """

 ░▀▄ ▄▀ █   █ ▀▀▀█  ░█▀▄ ▄▀█ █▀▀█ ▀█ ▄▀ █▀▀▀ █▀▀█  ░█▀▀█ █▀▀█ ▀▀█▀▀
   ░█    ▀▄▀   ▄▀   ░█  ▀  █ █▄▄█  ██   █▀▀  █▄▄▀  ░█▀▀▄ █  █   █
 ░▄▀ ▀▄   █   █▄▄▄  ░█     █ ▀  ▀ ▄█ ▀▄ █▄▄█ ▀ ▀▀  ░█▄▄█ ▀▀▀▀   ▀

 X-Points Maker Bot                                          v.1.3 
"""


async def get_session():
    try:
        global user_data
        with open("config/data.txt", "r") as file:
            i = 0
            for line in file:
                user_data[i] = {}
                user_data[i]["init_data"] = line.strip()
                decoded_data = urllib.parse.parse_qs(line)
                decoded_data = json.loads(decoded_data["user"][0])
                user_data[i]["username"] = decoded_data["username"]
                user_data[i]["id"] = decoded_data["id"]
                i += 1

            user_data["count_user"] = i
            logger.info(f"System | List <c>[{i}]</c> session is loaded...")
            return True
    except Exception as e:
        logger.error(f"{e}")
        return False


async def get_user_agent():
    try:
        if settings.USE_UA:
            with open("config/user-agent.txt", "r") as file:
                i = 0
                for line in file:
                    user_data[i]["user-agent"] = line.strip()
                    i += 1
                    if i >= len(user_data) - 1:
                        break

                if user_data["count_user"] > i:
                    logger.error(
                        f"System | The number of user-agent is less than the number of sessions"
                    )
                    return False
                else:
                    logger.success(f"System | List <c>[{i}]</c> user-agent download...")
                    return True
        else:
            for i in range(user_data["count_user"]):
                user_data[i][
                    "user-agent"
                ] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0"
            logger.success(f"System | Default user-agent download...")
            return False

    except Exception as e:
        logger.error(f"{e}")
        return False


async def get_proxies():
    global user_data

    try:
        if settings.USE_PROXY:
            with open("config/proxies.txt", "r") as file:
                i = 0
                for line in file:
                    user_data[i]["proxy"] = line.strip()
                    i += 1

                if user_data["count_user"] > i:
                    logger.error(
                        f"System | The number of proxies is less than the number of sessions"
                    )
                    return False
                else:
                    logger.success(f"System | List <c>[{i}]</c> proxy  download...")
                    return True
        else:
            for i in range(user_data["count_user"]):
                user_data[i]["proxy"] = None
            logger.success(f"System | None proxy...")
            return False

    except Exception as e:
        logger.error(f"{e}")
        return False
