import functools
import random
import sqlite3
import sys

import logging
import traceback

from datetime import datetime
from typing import List

from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QKeyEvent, QPixmap, QMouseEvent
from PyQt5.QtWidgets import (QApplication, QDialog, QHeaderView, QMainWindow,
                             QMessageBox, QTableWidget, QTableWidgetItem, QWidget)

from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, Qt

from ui import (Ui_About, Ui_ConfirmAgain, Ui_ConfirmClearAll, Ui_ConfirmExit, Ui_ConfirmLeave, Ui_DeleteResult,
                Ui_GameOver, Ui_MainWindow, Ui_ResultsTable, Ui_StartDialog, Ui_Win, Ui_WinLeave)

PRICES = [
    '0', '500', '1 000', '2 000', '3 000', '5 000', '10 000',
    '15 000', '25 000', '50 000', '100 000', '200 000',
    '400 000', '800 000', '1 500 000', '3 000 000'
]
GUARANTEED_PRICES = ['0'] * 5 + ['5 000'] * 5 + ['100 000'] * 5
logging.basicConfig(filename='logs.txt', level=logging.DEBUG,
                    format='%(levelname)s: %(message)s')


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

    logging.info('Qs are gotten')
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


def decorate_audio(file):
    url = QUrl.fromLocalFile(file)
    content = QMediaContent(url)
    return content


class StartWindow(QDialog, Ui_StartDialog):
    '''
    StartWindow\n
    • type: QInputDialog\n
    • target: enter player's name 
    '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.setFixedSize(361, 140)
        self.ok_button.clicked.connect(self.getName)
        self.exit_button.clicked.connect(sys.exit)

    def getName(self):
        name = self.lineEdit.text()
        if not name or any([(l in name) for l in '`~!@#$%^&*()_+{}|:"<>?[]\\;\',./№0123456789']):
            self.label.setText('Пожалуйста, введите корректное имя:')
            self.lineEdit.setText('')
        else:
            self.startGame(name)

    def startGame(self, name):
        self.game = GameWindow(name)
        self.game.show()

        self.game.lost_change.hide()
        self.game.lost_5050.hide()
        self.game.lost_x2.hide()
        self.game.double_dip.hide()

        self.close()


class GameWindow(QMainWindow, Ui_MainWindow):
    '''
    GameWindow\n
    • type: QMainWindow\n
    • target: playing the game 
    '''

    def __init__(self, name=''):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.control, self.name, self.date = False, name, datetime.today().strftime('%d.%m.%Y %H:%M')

        self.timer = 900
        self.is_x2_now, self.non_active_answers = False, []
        self.lifelines = [True, True, True]
        self.player1 = QMediaPlayer() # for bed and losing
        self.player2 = QMediaPlayer() # for intro and correct answer
        self.player3 = QMediaPlayer() # for lights down, 50:50 and change
        self.player4 = QMediaPlayer() # for ×2-lifeline
        self.new_game.triggered.connect(self.openConfirmAgain)
        self.close_game.triggered.connect(self.openConfirmClose)
        self.about.triggered.connect(self.openAbout)
        self.open_table.triggered.connect(self.openTable)
        self.clear_one.triggered.connect(self.openDeleteResultForm)
        self.clear_all.triggered.connect(self.openConfirmClearAll)
        self.setFixedSize(1100, 703)
        self.startGame()

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

    @user_control
    def startGame(self, repeat=False):
        self.player2.setMedia(decorate_audio('sounds/intro.mp3' if not repeat else 'sounds/new_start.mp3'))
        self.player2.play()

        self.questions = get_questions()
        self.current_number = 1

        for i in range(1, 16):
            self.time_function(
                200, self.current_state_t.setPixmap,
                QPixmap('images/money tree/{}.png'.format(i))
            )
        for i in 'A', 'B', 'C', 'D':
            self.time_function(
                400, self.current_state_q.setPixmap,
                QPixmap('images/question field/chosen_{}.png'.format(i))
            )

        self.time_function(500, self.current_state_q.setPixmap, QPixmap())
        self.time_function(
            700, self.current_state_t.setPixmap,
            QPixmap('images/money tree/{}.png'.format(self.current_number))
        )

        self.time_function(500, self.updateQuestionField)
        self.time_function(0, self.question.startFadeIn)
        for a in [self.answer_A, self.answer_B, self.answer_C, self.answer_D]:
            self.time_function(100, a.startFadeIn)
            self.time_function(0, a.show)
        
        n = '1-4' if self.current_number in [1, 2, 3, 4] else self.current_number
        self.player1.setMedia(decorate_audio('sounds/{}/bed.mp3'.format(n)))
        self.time_function(2500, self.player1.play)
        logging.info('Game is OK')

    def updateQuestionField(self, changer=False):
        self.non_active_answers = []
        text = self.questions[self.current_number - 1][int(changer)][0]
        self.answers = self.questions[self.current_number - 1][int(changer)][2]
        self.correct_answer = self.questions[self.current_number - 1][int(changer)][1]
        self.got_amount = PRICES[self.current_number - 1]
        for a in [self.answer_A, self.answer_B, self.answer_C, self.answer_D]:
            a.hide()
        self.question.setText(text)
        self.answer_A.setText(self.answers[0])
        self.answer_B.setText(self.answers[1])
        self.answer_C.setText(self.answers[2])
        self.answer_D.setText(self.answers[3])
        logging.info('Q{} set'.format(self.current_number))
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() < 1500:
            logging.info('KP {}'.format(event.key()))
        if event.key() in [Qt.Key_Q, 91, 1049, 1061]:
            self.checkPosition(285, 617)
        if event.key() in [Qt.Key_W, 93, 1062, 1066]:
            self.checkPosition(760, 617)
        if event.key() in [Qt.Key_A, 59, 1060, 1046]:
            self.checkPosition(285, 668)
        if event.key() in [Qt.Key_S, 39, 1067, 1069]:
            self.checkPosition(760, 668)
        if event.key() == Qt.Key_1:
            self.checkPosition(785, 113)
        if event.key() == Qt.Key_2:
            self.checkPosition(856, 113)
        if event.key() == Qt.Key_3:
            self.checkPosition(929, 113)
        if event.key() == Qt.Key_4:
            self.checkPosition(999, 113)

    def mousePressEvent(self, event: QMouseEvent):
        self.checkPosition(event.x(), event.y())
    
    def checkPosition(self, x, y):
        logging.info('MP ({}, {})'.format(x, y))
        if self.control:
            self.timer, n = 0, self.current_number

            if len(self.non_active_answers) in [1, 3]:
                self.player4.setMedia(decorate_audio('sounds/double/second_final.mp3'))
            elif not self.is_x2_now and n not in [1, 2, 3, 4, 5]:
                self.player4.setMedia(decorate_audio('sounds/{}/final_answer.mp3'.format(n)))
            elif self.is_x2_now:
                self.player4.setMedia(decorate_audio('sounds/double/first_final.mp3'))
            if 150 <= x <= 520 and 597 <= y <= 638:
                if 'A' not in self.non_active_answers:
                    self.current_state_q.setPixmap(QPixmap('images/question field/chosen_A.png'))
                    self.current_state_q.startFadeInImage()
                    if n not in [1, 2, 3, 4, 5] or self.is_x2_now:
                        self.player1.stop()
                        self.time_function(0, self.player4.play)
                    logging.info('Answ[A]')
                    self.checkAnswer(self.answer_A, 'A')
            elif 570 <= x <= 950 and 597 <= y <= 638:
                if 'B' not in self.non_active_answers:
                    self.current_state_q.setPixmap(QPixmap('images/question field/chosen_B.png'))
                    self.current_state_q.startFadeInImage()
                    if n not in [1, 2, 3, 4, 5] or self.is_x2_now:
                        self.player1.stop()
                        self.time_function(0, self.player4.play)
                    logging.info('Answ[B]')
                    self.checkAnswer(self.answer_B, 'B')
            elif 150 <= x <= 520 and 648 <= y <= 689:
                if 'C' not in self.non_active_answers:
                    self.current_state_q.setPixmap(QPixmap('images/question field/chosen_C.png'))
                    self.current_state_q.startFadeInImage()
                    if n not in [1, 2, 3, 4, 5] or self.is_x2_now:
                        self.player1.stop()
                        self.time_function(0, self.player4.play)
                    logging.info('Answ[C]')
                    self.checkAnswer(self.answer_C, 'C')
            elif 570 <= x <= 950 and 648 <= y <= 689:
                if 'D' not in self.non_active_answers:
                    self.current_state_q.setPixmap(QPixmap('images/question field/chosen_D.png'))
                    self.current_state_q.startFadeInImage()
                    if n not in [1, 2, 3, 4, 5] or self.is_x2_now:
                        self.player1.stop()
                        self.time_function(0, self.player4.play)
                    logging.info('Answ[D]')
                    self.checkAnswer(self.answer_D, 'D')

            if 765 <= x <= 805 and 101 <= y <= 126:
                self.lost_change.show()
                self.lost_change.startFadeInImage()
                self.useLifeline('change')
            elif 836 <= x <= 876 and 101 <= y <= 126:
                self.lost_5050.show()
                self.lost_5050.startFadeInImage()
                self.useLifeline('5050')
            elif 909 <= x <= 949 and 101 <= y <= 126:
                self.lost_x2.show()
                self.lost_x2.startFadeInImage()
                if self.lifelines[1]:
                    self.double_dip.show()
                    self.double_dip.startFadeInImage()
                self.useLifeline('x2')
            elif 979 <= x <= 1019 and 101 <= y <= 126:
                self.openConfirmLeave()

    def clear_all_labels(self):
        self.time_function(0, self.question.setText, '')
        self.time_function(0, self.answer_A.setText, '')
        self.time_function(0, self.answer_B.setText, '')
        self.time_function(0, self.answer_C.setText, '')
        self.time_function(0, self.answer_D.setText, '')
        self.time_function(0, self.current_state_q.setPixmap, QPixmap())
        self.time_function(0, self.current_state_q_2.setPixmap, QPixmap())
        self.time_function(0, self.current_state_q_3.setPixmap, QPixmap())

    @user_control
    def checkAnswer(self, label, letter):
        user_answer = label.text()
        if user_answer != self.correct_answer:
            num_to_let = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
            letter = num_to_let[self.answers.index(self.correct_answer)]
            x2_letter = num_to_let[self.answers.index(user_answer)]

        if self.current_number == 5:
            self.time_function(2000, lambda a: a, True)
        elif self.current_number in [6, 7, 8, 9]:
            self.time_function(2500, lambda a: a, True)
        elif self.current_number == 10:
            self.time_function(3000, lambda a: a, True)
        elif self.current_number in [11, 12]:
            self.time_function(3500, lambda a: a, True)
        elif self.current_number in [13, 14]:
            self.time_function(4500, lambda a: a, True)
        elif self.current_number == 15:
            self.time_function(5500, lambda a: a, True)

        if not self.is_x2_now or user_answer == self.correct_answer:
            n = '1-4' if self.current_number in [1, 2, 3, 4] else self.current_number
            if self.is_x2_now:
                self.time_function(0, self.double_dip.startFadeOutImage)
                self.is_x2_now = False
                logging.info('Answ incorrect (dd used)')
            if user_answer == self.correct_answer:
                self.player2.setMedia(decorate_audio('sounds/{}/correct.mp3'.format(n)))
                self.time_function(0, self.player4.stop)
                self.time_function(0, self.player2.play)
                logging.info('Answ correct')
            elif not self.is_x2_now:
                self.player1.setMedia(decorate_audio('sounds/{}/lose.mp3'.format(n)))
                self.time_function(0, self.player4.stop)
                self.time_function(0, self.player1.play)
                logging.info('Answ incorrect')
            self.time_function(
                0, self.current_state_q_2.setPixmap,
                QPixmap('images/question field/correct_{}.png'.format(letter))
            )
            self.time_function(0, self.current_state_q_2.startFadeInImage)
            self.time_function(0, self.current_state_q_2.show)
            for i in range(2):
                self.time_function(400, self.current_state_q_2.startFadeOutImage)
                self.time_function(400, self.current_state_q_2.startFadeInImage)

        else:
            self.time_function(
                1500, self.current_state_q_3.setPixmap,
                QPixmap('images/question field/wrong_{}.png'.format(x2_letter))
            )
            self.time_function(0, self.player4.stop)
            self.player1.setMedia(decorate_audio('sounds/double/first_wrong.mp3'))
            self.time_function(0, self.player1.play)
            self.time_function(0, self.double_dip.startFadeOutImage)
            self.non_active_answers.append(x2_letter)

        if user_answer == self.correct_answer:
            if self.current_number != 15:
                if self.current_number in [5, 10]:
                    self.time_function(0, self.player1.stop)
                    self.time_function(
                        5000, self.amount_q.setText,
                        PRICES[self.current_number]
                    )
                    self.clear_all_labels()
                    self.time_function(
                        0, self.layout_q.setPixmap,
                        QPixmap('images/sum/amount.png')
                    )
                    self.player3.setMedia(decorate_audio('sounds/lights_down.mp3'))
                    self.time_function(0, self.player3.play)
                    self.time_function(2000, self.amount_q.setText, '')
                    self.time_function(
                        0, self.layout_q.setPixmap,
                        QPixmap('images/question field/layout.png')
                    )
                    logging.info('{} got'.format(self.current_number))

                self.current_number += 1
                self.time_function(
                    800 * (self.current_number - 1 not in [5, 10]), self.current_state_t.setPixmap,
                    QPixmap('images/money tree/{}.png'.format(self.current_number))
                )
                self.clear_all_labels()
                self.time_function(0, self.current_state_q.setPixmap, QPixmap())
                self.time_function(0, self.current_state_q_2.setPixmap, QPixmap())
                self.time_function(0, self.current_state_q_3.setPixmap, QPixmap())
                if self.current_number - 1 not in [1, 2, 3, 4]:
                    self.time_function(
                        0, self.player1.setMedia,
                        decorate_audio('sounds/{}/bed.mp3'.format(self.current_number))
                    )
                    self.time_function(2500, self.player1.play)
                elif not self.lifelines[1]:
                    self.time_function(0, self.player1.setMedia, decorate_audio('sounds/1-4/bed.mp3'))
                    self.time_function(8, self.player1.play)
                self.time_function(8, self.updateQuestionField)
                self.time_function(0, self.question.startFadeIn)
                for a in [self.answer_A, self.answer_B, self.answer_C, self.answer_D]:
                    self.time_function(100, a.startFadeIn)
                    self.time_function(0, a.show)
                self.time_function(0, self.player2.stop)

            else:
                self.time_function(
                    1500, self.amount_q.setText,
                    PRICES[self.current_number]
                )
                self.time_function(
                    0, self.layout_q.setPixmap,
                    QPixmap('images/sum/amount.png')
                )
                self.clear_all_labels()
                sql_request('''INSERT INTO results
                            (name, result, date) 
                            VALUES ("{}", "{}", "{}")
                            '''.format(self.name, '3 000 000', self.date))
                self.time_function(0, self.showWin)

        if user_answer != self.correct_answer and not self.is_x2_now:
            result_game = GUARANTEED_PRICES[self.current_number - 1]
            self.time_function(0, self.showGameOver, [
                               letter, result_game])
            sql_request('''INSERT INTO results
                           (name, result, date) 
                           VALUES ("{}", "{}", "{}")
                        '''.format(self.name, result_game, self.date))
        if self.is_x2_now:
            self.is_x2_now = False

    @user_control
    def useLifeline(self, type_ll: str):
        if type_ll == 'change' and self.lifelines[0]:
            self.player3.setMedia(decorate_audio('sounds/change.mp3'))
            self.time_function(750, self.player3.play)
            self.time_function(800, self.updateQuestionField, True)
            if self.is_x2_now:
                self.time_function(0, self.double_dip.startFadeOutImage)
            self.time_function(0, self.question.startFadeIn)
            for a in [self.answer_A, self.answer_B, self.answer_C, self.answer_D]:
                self.time_function(100, a.startFadeIn)
                self.time_function(0, a.show)
            self.time_function(0, self.current_state_q.setPixmap, QPixmap())
            self.time_function(0, self.current_state_q_2.setPixmap, QPixmap())
            self.time_function(0, self.current_state_q_3.setPixmap, QPixmap())
            self.is_x2_now = False

            self.lifelines[0] = False
            logging.info('- Change-ll')

        elif type_ll == 'x2' and self.lifelines[1]:
            self.is_x2_now = True
            self.player1.setMedia(decorate_audio('sounds/double/start.mp3'))
            self.player1.play()
            self.lifelines[1] = False
            logging.info('- x2-ll')

        elif type_ll == '5050' and self.lifelines[2]:
            self.player3.setMedia(decorate_audio('sounds/50_50.mp3'))
            self.time_function(0, self.player3.play)
            answs = [self.answer_A, self.answer_B, self.answer_C, self.answer_D]
            answ_letters = ['A', 'B', 'C', 'D']
            if self.non_active_answers:
                indxs = set([0, 1, 2, 3]) - set([answ_letters.index(self.non_active_answers[0])])
            else:
                indxs = set([0, 1, 2, 3])
            indxs = list(indxs - set([self.answers.index(self.correct_answer)]))
            random.shuffle(indxs)
            answs[indxs[0]].setText('')
            answs[indxs[1]].setText('')
            self.non_active_answers += [answ_letters[indxs[0]], answ_letters[indxs[1]]]

            self.lifelines[2] = False
            logging.info('- 50:50-ll')

    def restartGame(self):
        self.control = True
        self.timer, self.is_x2_now = 900, False
        self.lifelines = [True, True, True]
        for ll in [self.lost_change, self.lost_x2, self.lost_5050]:
            ll.hide()
        self.clear_all_labels()
        for p in [self.player1, self.player2, self.player3, self.player4]:
            p.stop()
        self.layout_q.setPixmap(QPixmap('images/question field/layout.png'))
        self.amount_q.setText('')
        self.startGame(True)

    def showWin(self):
        self.win = WinWindow(self)
        self.control = False
        self.win.move(169 + self.x(), 210 + self.y())
        self.win.show()
        logging.info('Game over — player won')

    def showGameOver(self, data):
        self.control = False
        self.game_over = GameOverWindow(self, data)
        self.game_over.move(169 + self.x(), 210 + self.y())
        self.game_over.show()
        logging.info('Game over — player lost')

    def openConfirmLeave(self):
        self.control = False
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
        logging.info('Results table open')

    def openDeleteResultForm(self):
        self.delete_form = DeleteResultWindow()
        self.delete_form.move(150 + self.x(), 93 + self.y())
        self.delete_form.show()

    def openConfirmClearAll(self):
        self.confirm_wndw = ConfirmClearAll()
        self.confirm_wndw.move(169 + self.x(), 210 + self.y())
        self.confirm_wndw.show()

    def openAbout(self):
        self.about_wndw = AboutWindow(self)
        for p in [self.player1, self.player2, self.player4]:
            p.setVolume(20)
        self.player3.setMedia(decorate_audio('sounds/about.mp3'))
        self.player3.play()
        self.about_wndw.move(175 + self.x(), 180 + self.y())
        self.about_wndw.show()
        logging.info('About open')


class WinWindow(QDialog, Ui_Win):
    '''
    WinWindow\n
    • type: QDialog\n
    • target: asking about starting new game after win (passed 15 question)
    '''

    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

        self.parent = parent
        self.buttonBox.accepted.connect(self.restart)
        self.buttonBox.rejected.connect(self.exit)

    def restart(self):
        self.parent.restartGame()
        self.close()
        self.results = ResultsTableWindow()
        self.results.move(169 + self.parent.x(), 93 + self.parent.y())
        self.results.show()
        logging.info('Game restart')

    def exit(self):
        self.parent.close()
        self.close()
        self.player = QMediaPlayer()
        self.player.setMedia(decorate_audio('sounds/quit_game.mp3'))
        self.player.play()
        self.results = ResultsTableWindow()
        self.results.show()
        logging.info('Game close')


class GameOverWindow(QDialog, Ui_GameOver):
    '''
    GameOverWindow\n
    • type: QDialog\n
    • target: asking about starting new game after loss
    '''

    def __init__(self, parent, data):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

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
        logging.info('Game restart')

    def exit(self):
        self.parent.close()
        self.close()
        self.player = QMediaPlayer()
        self.player.setMedia(decorate_audio('sounds/quit_game.mp3'))
        self.player.play()
        self.results = ResultsTableWindow()
        self.results.show()
        logging.info('Game close')


class ConfirmLeaveWindow(QDialog, Ui_ConfirmLeave):
    '''
    ConfirmLeaveWindow\n
    • type: QDialog\n
    • target: сonfirm leaving current round
    '''

    def __init__(self, parent: GameWindow, letter):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

        self.parent = parent
        self.correct = letter
        self.label.setText(self.label.text().replace('{}', self.parent.got_amount))
        self.accepted.connect(self.leave)
        self.rejected.connect(self.close_wndw)

    def leave(self):
        sql_request('''INSERT INTO results
                       (name, result, date) 
                       VALUES ("{}", "{}", "{}")
                    '''.format(self.parent.name, self.parent.got_amount, self.parent.date))
        self.windialog = WinLeaveWindow(self.parent, [self.correct, self.parent.got_amount])
        self.windialog.move(169 + self.parent.x(), 210 + self.parent.y())
        self.windialog.show()
        
        for p in [self.parent.player1, self.parent.player2, self.parent.player3, self.parent.player4]:
            p.stop()
        self.parent.player1.setMedia(decorate_audio('sounds/walk_away.mp3'))
        self.parent.player1.play()
        self.parent.current_state_q_2.setPixmap(
            QPixmap('images/question field/correct_{}.png'.format(self.correct))
        )
        self.parent.current_state_q_2.startFadeInImage()
        self.parent.current_state_q_2.show()

        logging.info('Game over — leave game')

        self.close()
    
    def close_wndw(self):
        self.parent.control = True
        self.close()


class WinLeaveWindow(Ui_WinLeave, GameOverWindow):
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
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.parent = parent
        self.accepted.connect(self.restart)
        self.rejected.connect(self.close)

    def restart(self):
        self.parent.restartGame()
        logging.info('Game restart')
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
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.accepted.connect(self.exit)
        self.rejected.connect(self.close)
        self.setFixedSize(400, 140)
    
    def exit(self):
        logging.info('Game close')
        sys.exit()


class ResultsTableWindow(QWidget, Ui_ResultsTable):
    '''
    ResultsTableWindow\n
    • type: QWidget\n
    • target: show the results
    '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

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
        self.setWindowIcon(QIcon('images/app_icon.ico'))
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
            raise Exception(result)
        else:
            logging.info('R{} delete'.format(id_result))
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
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.accepted.connect(self.deleteAllData)
        self.rejected.connect(self.close)
        self.setFixedSize(400, 140)

    def deleteAllData(self):
        result = sql_request('DELETE FROM results')
        self.results_table = ResultsTableWindow()
        self.results_table.show()
        logging.info('AllR delete')
        self.close()


class AboutWindow(QWidget, Ui_About):
    '''
    AboutWindow\n
    • type: QWidget\n
    • target: tell about app's author
    '''

    def __init__(self, parent: GameWindow):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.enText.hide()
        self.parent = parent
        self.ruButton.clicked.connect(self.showRuText)
        self.enButton.clicked.connect(self.showEnText)
        self.okButton.clicked.connect(self.close_wndw)
        self.setFixedSize(380, 222)

    def showRuText(self):
        self.ruText.show()
        self.enText.hide()

    def showEnText(self):
        self.enText.show()
        self.ruText.hide()
    
    def close_wndw(self):
        for p in [self.parent.player1, self.parent.player2, self.parent.player4]:
            p.setVolume(100)
        self.parent.player3.stop()
        self.close()
    
    def closeEvent(self, a0):
        for p in [self.parent.player1, self.parent.player2, self.parent.player4]:
            p.setVolume(100)
        self.parent.player3.stop()


def excepthook(exc_type, exc_value, exc_tb):
    global app, msg
    logging.error(
        str(exc_value) + '\n' + 
        ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    )
    msg.show()
    msg.buttonClicked.connect(app.quit)


if __name__ == '__main__':
    sys.excepthook = excepthook
    
    app = QApplication(sys.argv)
    logging.info(datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ': Session start')
    wndw = StartWindow()
    wndw.show()

    msg = QMessageBox()
    msg.setWindowTitle("Упс, ошибка...")
    msg.setWindowIcon(QIcon('images/app_icon.ico'))
    msg.setIcon(QMessageBox.Critical)
    msg.setText('<html><body><p>Кажется, мы споткнулись об какую-то ошибку.\n'
                'Чтобы прокачать игру, отправьте файл logs.txt <a href="https://t.me/pavetranquil">'
                '<span style="text-decoration: underline; color:#005ffe;">разработчику</span></a>.</p></body></html>')

    app.exec()
    logging.info('Session finish\n\n')
