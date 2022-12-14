import os

from apscheduler.schedulers.blocking import BlockingScheduler

from config import SETTINGS
from sources.meteosat import MeteosatSource

from logger import get_logger

MINUTES_UPDATE_INTERVAL = int(SETTINGS.get("MINUTES_UPDATE_INTERVAL"))
EUMETSAT_CONSUMER_KEY = SETTINGS.get("EUMETSAT_CONSUMER_KEY")
EUMETSAT_CONSUMER_SECRET = SETTINGS.get("EUMETSAT_CONSUMER_SECRET")
STATE_DIR = SETTINGS.get("STATE_DIR")
OUTPUT_DIR = SETTINGS.get("OUTPUT_DIR")

logger = get_logger(__name__)


def update_source():
    meteosat_source = MeteosatSource(consumer_key=EUMETSAT_CONSUMER_KEY, consumer_secret=EUMETSAT_CONSUMER_SECRET,
                                     state_directory=STATE_DIR,
                                     output_dir=OUTPUT_DIR)

    meteosat_source.update()


if __name__ == '__main__':
    scheduler = BlockingScheduler(logger=logger)
    scheduler.add_job(update_source, 'interval', minutes=MINUTES_UPDATE_INTERVAL, max_instances=1)
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
