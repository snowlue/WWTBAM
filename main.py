import functools
import random
import sqlite3
import sys

from datetime import datetime
from typing import List

from PyQt5 import QtCore, uic
from PyQt5.QtGui import QPixmap, QMouseEvent
from PyQt5.QtWidgets import (QApplication, QDialog, QHeaderView, QInputDialog,
                             QMainWindow, QTableWidget, QTableWidgetItem, QWidget)

from ui import (Ui_About, Ui_ConfirmAgain, Ui_ConfirmClearAll, Ui_ConfirmExit, Ui_ConfirmLeave,
                Ui_DeleteResult, Ui_GameOver, Ui_ResultsTable, Ui_WinLeave)

PRICES = [
    '0', '500', '1 000', '2 000', '3 000', '5 000', '10 000',
    '15 000', '25 000', '50 000', '100 000', '200 000',
    '400 000', '800 000', '1 500 000', '3 000 000'
]
GUARANTEED_PRICES = ['0'] * 5 + ['5 000'] * 5 + ['100 000'] * 5


def sql_request(request: str):
    with sqlite3.connect('database.sqlite3') as con:
        cur = con.cursor()
        if 'select' in request.lower():
            try:
                return cur.execute(request).fetchall()
            except Exception as ex:
                return 'ERROR: ' + str(ex)
        else:
            try:
                cur.execute(request)
                con.commit()
                return 'OK'
            except Exception as ex:
                return 'ERROR: ' + str(ex)


def get_questions():
    questions_data, questions = [sql_request(
        'SELECT * FROM "{}_questions"'.format(i)
    ) for i in range(1, 16)], []

    for q_unshuffled in questions_data:
        questions_set = []

        q_shuffled = q_unshuffled.copy()
        random.shuffle(q_shuffled)
        for q in q_shuffled[:2]:
            text, corr_answ, answs = q[1], q[2], list(q[2:])
            random.shuffle(answs)
            questions_set.append([text, corr_answ, answs])

        questions.append(questions_set)

    return questions


def makeTable(table: QTableWidget, header: List[str], data: List[List[str]]):
    table.setColumnCount(len(header))
    table.setHorizontalHeaderLabels(header)
    table.setRowCount(0)

    for i, rowlist in enumerate(data):
        table.setRowCount(table.rowCount() + 1)
        for j, elem in enumerate(rowlist):
            table.setItem(i, j, QTableWidgetItem(elem))
    table.resizeColumnsToContents()

    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    table.setEditTriggers(QTableWidget.NoEditTriggers)


class StartWindow(QInputDialog):
    '''
    StartWindow\n
    • type: QInputDialog\n
    • target: enter player's name 
    '''

    def __init__(self):
        super().__init__()
        self.getName('Введите ваше имя:')

    def getName(self, shown_text):
        name, is_accepted = self.getText(self, ' ', shown_text)
        self.saveGeometry
        if is_accepted:
            if not name:
                self.close()
                self.getName('Пожалуйста, введите имя:')
                return 0
            self.startGame(name)
        else:
            sys.exit()

    def startGame(self, name):
        self.game = GameWindow(name)
        self.game.show()

        self.game.lost_change.hide()
        self.game.lost_5050.hide()
        self.game.lost_x2.hide()

        self.close()


class GameWindow(QMainWindow):
    '''
    GameWindow\n
    • type: QMainWindow\n
    • target: playing the game 
    '''

    def __init__(self, name=''):
        super().__init__()
        uic.loadUi('ui/layoutGame.ui', self)
        self.control, self.name, self.date = False, name, datetime.today().strftime('%d.%m.%Y %H:%M')

        self.timer = 900
        self.is_x2_now, self.non_active_answers = False, []
        self.lifelines = [True, True, True]

        self.new_game.triggered.connect(self.openConfirmAgain)
        self.close_game.triggered.connect(self.openConfirmClose)
        self.about.triggered.connect(self.openAbout)
        self.open_table.triggered.connect(self.openTable)
        self.clear_one.triggered.connect(self.openDeleteResultForm)
        self.clear_all.triggered.connect(self.openConfirmClearAll)
        self.setFixedSize(1100, 703)
    def user_control(func):
        def wrapper(self, *args, **kwargs):
            def f(x): self.control = x
            self.time_function(1, f, False)
            func(self, *args, **kwargs)
            self.time_function(1, f, True)

        return wrapper

    def time_function(self, time: int, func, *args):
        QtCore.QTimer.singleShot(self.timer + time, functools.partial(func, *args))
        self.timer += time


    def showGameOver(self, data):
        self.game_over = GameOverWindow(self, data)
        self.game_over.move(169 + self.x(), 210 + self.y())
        self.game_over.show()

    def openConfirmLeave(self):
        num_to_let = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
        letter = num_to_let[self.answers.index(self.correct_answer)]
        self.confirm_wndw = ConfirmLeaveWindow(self, letter)
        self.confirm_wndw.move(169 + self.x(), 210 + self.y())
        self.confirm_wndw.show()

    def openConfirmAgain(self):
        self.confirm_wndw = ConfirmAgainWindow(self)
        self.confirm_wndw.move(169 + self.x(), 210 + self.y())
        self.confirm_wndw.show()

    def openConfirmClose(self):
        self.confirm_wndw = ConfirmCloseWindow()
        self.confirm_wndw.move(169 + self.x(), 210 + self.y())
        self.confirm_wndw.show()

    def openTable(self):
        self.results_table = ResultsTableWindow()
        self.results_table.move(169 + self.x(), 93 + self.y())
        self.results_table.show()

    def openDeleteResultForm(self):
        self.delete_form = DeleteResultWindow()
        self.delete_form.move(150 + self.x(), 93 + self.y())
        self.delete_form.show()

    def openConfirmClearAll(self):
        self.confirm_wndw = ConfirmClearAll()
        self.confirm_wndw.move(169 + self.x(), 210 + self.y())
        self.confirm_wndw.show()

    def openAbout(self):
        self.about = AboutWindow()
        self.about.move(175 + self.x(), 180 + self.y())
        self.about.show()


class GameOverWindow(QDialog, Ui_GameOver):
    '''
    GameOverWindow\n
    • type: QDialog\n
    • target: asking about starting new game after loss
    '''

    def __init__(self, parent, data):
        super().__init__()
        self.setupUi(self)
        self.parent = parent
        self.buttonBox.accepted.connect(self.restart)
        self.buttonBox.rejected.connect(self.exit)
        self.label.setText(self.label.text().replace('{0}', data[0]).replace('{1}', data[1]))

    def restart(self):
        self.parent.restartGame()
        self.close()
        self.results = ResultsTableWindow()
        self.results.move(169 + self.parent.x(), 93 + self.parent.y())
        self.results.show()

    def exit(self):
        self.parent.close()
        self.close()
        self.results = ResultsTableWindow()
        self.results.show()


class ConfirmLeaveWindow(QDialog, Ui_ConfirmLeave):
    '''
    ConfirmLeaveWindow\n
    • type: QDialog\n
    • target: сonfirm leaving current round
    '''

    def __init__(self, parent: GameWindow, letter):
        super().__init__()
        self.setupUi(self)
        self.parent = parent
        self.correct = letter
        self.label.setText(self.label.text().replace('{}', self.parent.got_amount))
        self.accepted.connect(self.leave)
        self.rejected.connect(self.close)

    def leave(self):
        sql_request('''INSERT INTO results
                       (name, result, date) 
                       VALUES ("{}", "{}", "{}")
                    '''.format(self.parent.name, self.parent.got_amount, self.parent.date))
        self.windialog = WinLeaveWindow(self.parent, [self.correct, self.parent.got_amount])
        self.windialog.move(169 + self.parent.x(), 210 + self.parent.y())
        self.windialog.show()
        self.close()


class WinLeaveWindow(GameOverWindow, Ui_WinLeave):
    '''
    WinLeaveWindow\n
    • type: QDialog\n
    • target: сonfirm restarting game after leaving current round
    '''

    pass


class ConfirmAgainWindow(QDialog, Ui_ConfirmAgain):
    '''
    ConfirmAgainWindow\n
    • type: QDialog\n
    • target: сonfirm restarting game
    '''

    def __init__(self, parent: GameWindow):
        super().__init__()
        self.setupUi(self)
        self.parent = parent
        self.accepted.connect(self.restart)
        self.rejected.connect(self.close)

    def restart(self):
        self.parent.restartGame()
        self.close()


class ConfirmCloseWindow(QDialog, Ui_ConfirmExit):
    '''
    ConfirmCloseWindow\n
    • type: QDialog\n
    • target: сonfirm player's exit from the app
    '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.accepted.connect(sys.exit)
        self.rejected.connect(self.close)
        self.setFixedSize(400, 140)


class ResultsTableWindow(QWidget, Ui_ResultsTable):
    '''
    ResultsTableWindow\n
    • type: QWidget\n
    • target: show the results
    '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        results = sql_request('SELECT * from results')
        results = sorted(results, key=lambda x: int(str(x[2]).replace(' ', '')), reverse=True)
        results = [list(map(str, i[1:])) for i in results]

        makeTable(self.tableWidget, ['Имя', 'Результат', 'Дата и время'], results)
        self.okButton.clicked.connect(self.close)


class DeleteResultWindow(QWidget, Ui_DeleteResult):
    '''
    DeleteResultWindow\n
    • type: QWidget\n
    • target: delete one result from the result's table
    '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.refreshTable()
        self.deleteButton.clicked.connect(self.deleteAction)

    def refreshTable(self):
        results = sql_request('SELECT * from results')
        results = sorted(results, key=lambda x: int(str(x[2]).replace(' ', '')), reverse=True)
        results = [list(map(str, i[1:])) for i in results]
        self.results = [list(map(str, [i + 1, results[i][2]])) for i in range(len(results))]

        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(len(results))

        makeTable(self.tableWidget, ['Имя', 'Результат', 'Дата и время'], results)

    def deleteAction(self):
        id_result = self.spinBox.text()
        result_date = list(filter(lambda x: x[0] == id_result, self.results))[0][1]
        result = sql_request('DELETE FROM results WHERE date = "{}"'.format(result_date))
        if 'ERROR' in result:
            print(result)
        self.refreshTable()


class ConfirmClearAll(QDialog, Ui_ConfirmClearAll):
    '''
    ConfirmDeleteAll\n
    • type: QDialog\n
    • target: сonfirm deleting all data from the result's table
    '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.accepted.connect(self.deleteAllData)
        self.rejected.connect(self.close)
        self.setFixedSize(400, 140)

    def deleteAllData(self):
        result = sql_request('DELETE FROM results')
        self.results_table = ResultsTableWindow()
        self.results_table.show()
        self.close()


class AboutWindow(QWidget, Ui_About):
    '''
    AboutWindow\n
    • type: QWidget\n
    • target: tell about app's author
    '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.enText.hide()
        self.ruButton.clicked.connect(self.showRuText)
        self.enButton.clicked.connect(self.showEnText)
        self.okButton.clicked.connect(self.hide)
        self.setFixedSize(380, 222)

    def showRuText(self):
        self.ruText.show()
        self.enText.hide()

    def showEnText(self):
        self.enText.show()
        self.ruText.hide()


def main():
    app = QApplication(sys.argv)
    wndw = StartWindow()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
