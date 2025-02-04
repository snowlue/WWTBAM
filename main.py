import logging
import sys
from datetime import datetime
from os.path import realpath

from core import StartWindow, app, excepthook

if __name__ == '__main__':
    logging.basicConfig(filename=realpath('logs.txt'), level=logging.INFO, format='%(levelname)s: %(message)s')
    sys.excepthook = excepthook

    logging.info(datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ': Session start')
    wndw = StartWindow()
    wndw.show()

    app.exec()
    logging.info('Session finish\n\n')
