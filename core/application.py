import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox

app = QApplication(sys.argv)

msg = QMessageBox()
msg.setWindowTitle('Упс, ошибка...')
msg.setWindowIcon(QIcon('images/app_icon.ico'))
msg.setIcon(QMessageBox.Critical)
msg.setText(
    '<html><body><p>Кажется, мы споткнулись об какую-то ошибку.\nЧтобы прокачать игру, отправьте файл logs.txt '
    '<a href="https://t.me/snowlue"><span style="text-decoration: underline; color:#3454D1; font-weight:600;">'
    'разработчику</span></a>.</p></body></html>'
)
