import logging
import os
import sys

logger = logging.getLogger(__name__)

logger.setLevel(logging.getLevelName(os.environ.get("LOG_LEVEL", "DEBUG")))
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
