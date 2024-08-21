import sys
from loguru import logger


logger.remove()
logger.add(
    sink=sys.stdout,
    format="<white>{time:YY-MM-DD HH:mm:ss}</white>"
    " | <level>{level: <8}</level>"
    " | <cyan><b>{line: <4}</b></cyan>"
    " - <white><b>{message}</b></white>",
)
logger = logger.opt(colors=True)
