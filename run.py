import logging
from datetime import datetime

from schwordcloud import SCHWordCloud

logger = logging.getLogger(__name__)

LOG_TS_FORMAT = "%d/%m/%Y %H:%M:%S"

if __name__ == "__main__":
    logging.basicConfig(filename="schwordcloud.log", level=logging.INFO)
    start_time = datetime.now().strftime(LOG_TS_FORMAT)
    logger.info(f"Starting SCHWordCloud at {start_time}...")
    schwc = SCHWordCloud()
    schwc.generate_wordcloud()
    end_time = datetime.now().strftime(LOG_TS_FORMAT)
    logger.info(f"SCHWordCloud finished at {end_time}.")

