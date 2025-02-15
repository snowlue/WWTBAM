import sys

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon

from core import constants

app = QApplication(sys.argv)

constants.APP_ICON = QIcon('images/app_icon.ico')

msg = QMessageBox()
msg.setWindowTitle('Упс, ошибка...')
msg.setWindowIcon(constants.APP_ICON)
msg.setIcon(QMessageBox.Critical)
msg.setText(
    '<html><body><p>Кажется, мы споткнулись об какую-то ошибку.\nЧтобы прокачать игру, отправьте файл logs.txt '
    '<a href="https://t.me/snowlue"><span style="text-decoration: underline; color:#3454D1; font-weight:600;">'
    'разработчику</span></a>.</p></body></html>'
)
