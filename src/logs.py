
from loguru import logger
import sys



logger.remove()

logger.add(
    sys.stdout,
    # lambda x: print(x, end=''),
    format="<dim>[{time:YYYY-MM-DD HH:mm:ss}]</dim> <level>{message}</level>",
    colorize=True
)
