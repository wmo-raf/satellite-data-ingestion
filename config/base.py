import logging
import os

from dotenv import load_dotenv

load_dotenv()

log_level = logging.getLevelName(os.getenv('LOG', "INFO"))

SETTINGS = {
    'logging': {
        'level': log_level
    },
    'MINUTES_UPDATE_INTERVAL': os.getenv('MINUTES_UPDATE_INTERVAL', 15),
    "EUMETSAT_CONSUMER_KEY": os.getenv('EUMETSAT_CONSUMER_KEY'),
    "EUMETSAT_CONSUMER_SECRET": os.getenv('EUMETSAT_CONSUMER_SECRET'),
    "STATE_DIR": os.getenv('STATE_DIR'),
    "OUTPUT_DIR": os.getenv('OUTPUT_DIR'),
}
