import logging
from typing import TYPE_CHECKING

from PyQt5.QtGui import QCloseEvent, QIcon
from PyQt5.QtWidgets import QWidget

from core.tools import makeTable, sql_request
from ui import Ui_About, Ui_DeleteResult, Ui_ResultsTable, Ui_Rules

if TYPE_CHECKING:
    from core.game import GameWindow


class GameRules(QWidget, Ui_Rules):
    """Класс типа QWidget, показывающий правила игры"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))


class ResultsTableWindow(QWidget, Ui_ResultsTable):
    """Класс типа QWidget, отображающий таблицу результатов"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

        results = sql_request('SELECT * from results')[1]  # запрашиваем результаты
        results = sorted(results, key=lambda x: int(str(x[2]).replace(' ', '')), reverse=True)  # сортируем по выигрышу
        results = [list(map(str, i[1:])) for i in results]

        makeTable(self.tableWidget, ['Имя', 'Результат', 'Дата и время'], results)
        self.okButton.clicked.connect(self.close)


class DeleteResultWindow(QWidget, Ui_DeleteResult):
    """Класс типа QWidget, отображающий форму для удаления одного результата из таблицы

    Методы
    ------
    refreshTable()
        Обновляет таблицу после удаления одного результата
    deleteAction()
        Удаляет один результат по id из спинбокса
    """

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.refreshTable()
        self.deleteButton.clicked.connect(self.deleteAction)

    def refreshTable(self):
        """Метод, обновляющий таблицу результатов после удаления одного результата"""

        results = sql_request('SELECT * from results')[1]
        results = sorted(results, key=lambda x: int(str(x[2]).replace(' ', '')), reverse=True)
        results = [list(map(str, i[1:])) for i in results]
        self.results = [list(map(str, [i + 1, results[i][2]])) for i in range(len(results))]

        self.deleteButton.setEnabled(bool(results))  # активируем кнопку удаления только при наличии результатов

        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(len(results))

        makeTable(self.tableWidget, ['Имя', 'Результат', 'Дата и время'], results)

    def deleteAction(self):
        """Метод, удаляющий один результат по id результата из спинбокса

        Исключения
        ----------
        Exception
            если запрос через sql_request() вернулся с ошибкой
        """

        id_result = self.spinBox.text()  # берём id результата из спинбокса
        result_date = list(filter(lambda x: x[0] == id_result, self.results))[0][1]
        result = sql_request(f'DELETE FROM results WHERE date = "{result_date}"')[0]
        if 'ERROR' in result:
            raise Exception(result)
        else:
            logging.info('R%d delete', id_result)
        self.refreshTable()


class AboutWindow(QWidget, Ui_About):
    """Класс типа QWidget, показывающий информацию о программе и разработчике

    Атрибуты
    --------
    parent: GameWindow
        класс основного окна игры
    is_sound: bool
        определяет, включён или отключён ли звук

    Методы
    ------
    showRuText()
        Показать русский текст
    showEnText()
        Показать английский текст
    close_wndw()
        Закрывает окно
    closeEvent(event: QCloseEvent)
        Вызывается при событии закрытия окна
    """

    def __init__(self, parent: 'GameWindow', is_sound: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.enText.hide()
        self.parent_ = parent  # родительское окно
        self.is_sound = is_sound
        self.ruButton.clicked.connect(self.showRuText)
        self.enButton.clicked.connect(self.showEnText)
        self.okButton.clicked.connect(self.close_wndw)

    def showRuText(self):
        """Метод, показывающий русский текст информации о программе"""

        self.ruText.show()
        self.enText.hide()

    def showEnText(self):
        """Метод, показывающий английский текст информации о программе"""

        self.enText.show()
        self.ruText.hide()

    def close_wndw(self):
        """Метод, закрывающий окно при нажатии на кнопку «ОК»"""

        for player in (self.parent_.player1, self.parent_.player2, self.parent_.player4):
            player.setVolume(100 * self.is_sound)
        self.parent_.player3.stop()
        self.close()

    def closeEvent(self, event: QCloseEvent):
        """Метод, вызывающийся при закрытии окна"""

        for player in (self.parent_.player1, self.parent_.player2, self.parent_.player4):
            player.setVolume(100 * self.is_sound)
        self.parent_.player3.stop()
        return super().closeEvent(event)
