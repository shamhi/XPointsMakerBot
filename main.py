import asyncio
import sys
from config import settings
from config.settings import *
from core.registrator import *
from utils.launcher import *
from utils.logger import logger


async def main():

    global user_data
    global tasks
    logger.warning(
        f"System | <y>Random wait "
        f"{settings.WAIT_LOGIN[0]}-{settings.WAIT_LOGIN[1]} sec to authorization!</y>"
    )

    if not await get_session():
        logger.error(f"System | <r>Error load session...</r>")
        sys.exit(1)

    if not await get_proxies():
        logger.warning(f"System | <y>Error load proxy, use none</y>")

    if not await get_user_agent():
        logger.warning(f"System | <y>Randomize user-agent is loaded</y>")

    tasks = [start(index) for index in range(user_data["count_user"])]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        print(banner)
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("<r>Bot stopped by user...</r>")
        sys.exit(2)
