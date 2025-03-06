import logging
import sys
from datetime import datetime
from os.path import realpath

from core import StartWindow, app, except_hook, create_database_if_not_exists

if __name__ == '__main__':
    logging.basicConfig(filename=realpath('logs.txt'), level=logging.INFO, format='%(levelname)s: %(message)s')
    sys.excepthook = except_hook

    logging.info(datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ': Session start')
    main_window = StartWindow()
    main_window.show()

    create_database_if_not_exists()
    app.exec()
    logging.info('Session finish\n\n')
