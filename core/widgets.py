import logging
import sys
from typing import TYPE_CHECKING

from PyQt5.QtGui import QCloseEvent, QIcon
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QWidget

from core.tools import decorate_audio, make_table, sql_request
from ui import Ui_About, Ui_DeleteResult, Ui_ResultsTable, Ui_Rules

if TYPE_CHECKING:
    from core.game import GameWindow


class GameRules(QWidget, Ui_Rules):
    """Окно для показа правил игры"""

    def __init__(self, player: QMediaPlayer):
        super().__init__()
        self.player = player
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
    
    def closeEvent(self, event: QCloseEvent):
        self.player.setMedia(decorate_audio('sounds/rules_stop.mp3'))
        self.player.play()
        return super().closeEvent(event)


class ResultsTableWindow(QWidget, Ui_ResultsTable):
    """Окно для отображения таблицы результатов"""

    def __init__(self, close_the_game: bool = False):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

        results = sql_request('SELECT * from results')[1]
        results = sorted(results, key=lambda x: int(str(x[2]).replace(' ', '')), reverse=True)  # сортируем по выигрышу
        results = [list(map(str, i[1:])) for i in results]

        make_table(self.tableWidget, ['Имя', 'Результат', 'Дата и время'], results)
        if close_the_game:
            self.okButton.clicked.connect(lambda: sys.exit(0))
        self.okButton.clicked.connect(self.close)


class DeleteResultWindow(QWidget, Ui_DeleteResult):
    """Окно для удаления одного результата из таблицы"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.refresh_table()
        self.deleteButton.clicked.connect(self.delete_action)

    def refresh_table(self):
        """Обновляет таблицу результатов после удаления одного результата"""

        results = sql_request('SELECT * from results')[1]
        results = sorted(results, key=lambda x: int(str(x[2]).replace(' ', '')), reverse=True)
        results = [list(map(str, i[1:])) for i in results]
        self.results = [list(map(str, [i + 1, results[i][2]])) for i in range(len(results))]

        self.deleteButton.setEnabled(bool(results))

        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(len(results))

        make_table(self.tableWidget, ['Имя', 'Результат', 'Дата и время'], results)

    def delete_action(self):
        """Удаляет один результат по id результата из спинбокса"""

        id_result = self.spinBox.text()
        result_date = list(filter(lambda x: x[0] == id_result, self.results))[0][1]
        result = sql_request(f'DELETE FROM results WHERE date = "{result_date}"')[0]
        if 'ERROR' in result:
            raise Exception(result)
        else:
            logging.info('R%d delete', id_result)
        self.refresh_table()


class AboutWindow(QWidget, Ui_About):
    """Окно для показа информации о программе и разработчике"""

    def __init__(self, parent: 'GameWindow', is_sound: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.enText.hide()
        self.parent_ = parent
        self.is_sound = is_sound
        self.ruButton.clicked.connect(self.show_ru_text)
        self.enButton.clicked.connect(self.show_en_text)
        self.okButton.clicked.connect(self.close_wndw)

    def show_ru_text(self):
        """Показывает русский текст информации о программе"""

        self.ruText.show()
        self.enText.hide()

    def show_en_text(self):
        """Показывает английский текст информации о программе"""

        self.enText.show()
        self.ruText.hide()

    def adjust_volume(self):
        """Регулирует громкость медиа-плееров при закрытии окна"""
        for player in (self.parent_.player1, self.parent_.player2, self.parent_.player4):
            player.setVolume(100 * self.is_sound)
        self.parent_.player3.stop()

    def close_wndw(self):
        """Закрывает окно при нажатии на кнопку «ОК»"""
        self.adjust_volume()
        self.close()

    def closeEvent(self, event: QCloseEvent):
        """Обрабатывает событие закрытия окна"""
        self.adjust_volume()
        return super().closeEvent(event)
