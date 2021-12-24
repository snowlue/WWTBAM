import logging
import sys
from datetime import datetime  # обозначить время начало игры
from functools import partial  # для передачи аргументов в функцию без её вызова
from os.path import realpath  # возвращает глобальный путь
from random import shuffle
from typing import Callable

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QIcon, QKeyEvent, QMouseEvent, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QDialog, QMainWindow, QMessageBox, QWidget

from application import app
from funcs import (decorate_audio, excepthook, get_questions, makeTable,
                   sql_request)
from ui import (AnimationLabel, Ui_About, Ui_ConfirmAgain, Ui_ConfirmClearAll,
                Ui_ConfirmExit, Ui_ConfirmLeave, Ui_DeleteResult, Ui_GameOver,
                Ui_MainWindow, Ui_ResultsTable, Ui_Rules, Ui_StartDialog,
                Ui_Win, Ui_WinLeave)

PRICES = [
    '0', '500', '1 000', '2 000', '3 000', '5 000', '10 000',
    '15 000', '25 000', '50 000', '100 000', '200 000',
    '400 000', '800 000', '1 500 000', '3 000 000'
]  # суммы денежного дерева
GUARANTEED_PRICES = ['0'] * 5 + ['5 000'] * 5 + ['100 000'] * 5  # несгораемые суммы
logging.basicConfig(filename=realpath('logs.txt'), level=logging.DEBUG,
                    format='%(levelname)s: %(message)s')  # конфиг логгирования


class StartWindow(QDialog, Ui_StartDialog):
    '''Класс типа QDialog, использующийся для ввода имени игрока и показа правил игр

    Примечание:
        правила игры пока не прописаны

    Методы
    ------
    getName()
        Получает имя игрока
    showRules()
        Показывает правила игры
    startGame()
        Начинает игру, инициализируя GameWindow
    '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.ok_button.clicked.connect(self.getName)
        self.rulebook_button.clicked.connect(self.showRules)
        self.exit_button.clicked.connect(sys.exit)
        self.msg = QMessageBox()
        self.msg.setWindowTitle("Некорректное имя")
        self.msg.setWindowIcon(QIcon('images/app_icon.ico'))
        self.msg.setIcon(QMessageBox.Warning)

    def getName(self) -> None:
        '''Метод, получающий имя игрока
        '''

        name = self.lineEdit.text()
        if not name:
            self.msg.setText('Введите имя, чтобы учитываться в таблице рекордов.\n'
                             'Не оставляйте поле пустым.')
            self.msg.show()
        elif any([(le in name) for le in '`~!@#$%^&*()_+{}|:"<>?[]\\;\',./№0123456789']):
            self.msg.setText('Введите корректное имя, состоящее только из букв и пробелов. '
                             'Не используйте цифры или спецсимволы.')
            self.msg.show()
            self.lineEdit.setText('')
        else:
            self.startGame(name.capitalize())

    def showRules(self):
        '''Метод, показывающий правила игры
        '''

        self.rules_wndw = GameRules()
        self.rules_wndw.show()

    def startGame(self, name: str) -> None:
        '''Метод, начинающий игру с заданным именем игрока name

        Параметры
        ---------
        name: str
            имя игрока
        '''

        self.game = GameWindow(name)
        self.game.show()

        self.game.lost_change.hide()
        self.game.lost_5050.hide()
        self.game.lost_x2.hide()
        self.game.double_dip.hide()

        self.close()


class GameRules(QWidget, Ui_Rules):
    '''Класс типа QWidget, показывающий правила игры
    '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))


class GameWindow(QMainWindow, Ui_MainWindow):
    '''Класс типа QMainWindow, использующийся для отображения основного игрового контента

    Атрибуты
    --------
    name: str
        имя игрока

    Методы
    ------
    user_control(func)
        Декоратор, деактивирующий управление игрой во время выполнения анимации
    time_function(time, func, *args)
        Активирует таймер для выполнения анимаций (обёртка)
    startGame(repeat)
        Активирует анимацию начала игры и показывает первый вопрос
    updateQuestionField(changer)
        Обновляет текстовые поля вопроса и ответов
    keyPressEvent(event)
        Срабатывает при нажатии клавиши клавиатуры
    mousePressEvent(event)
        Срабатывает при нажатии кнопки мыши
    checkPosition(x, y)
        Обрабатывает переданные координаты в действие
    clear_all_labels()
        Подчищает все слои состояния и текстовые блоки
    checkAnswer(label, letter)
        Обрабатывает ответ игрока и проверяет правильность ответа
    useLifeline(type_ll)
        Использует подсказку
    restartGame()
        Перезапускает игру и возвращает все значения в начальное состояние
    showWin()
        Показывает окно для победы
    showGameOver(data)
        Показывает окно для поражения
    openConfirmLeave()
        Показывает форму для подтверждения кнопки «забрать деньги»
    openConfirmAgain()
        Показывает форму для подтверждения перезапуска игры
    openConfirmClose()
        Показывает форму для подтверждения завершения игры
    openTable()
        Показывает таблицу результатов
    openDeleteResultForm()
        Показывает форму для удаления одного результата из таблицы результатов
    openConfirmClearAll()
        Показывает форму для очистки таблицы результатов
    openAbout()
        Показывает информацию об игре и разработчике
    checkSound()
        Переключает звук (т.е. включает или отключает)
    '''

    def __init__(self, name: str = ''):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.control, self.name = False, name  # control — реагирует ли игра на действия игрока

        self.timer = 900  # таймер для поочерёдного воспроизведения событий
        # 900 для синхронизации анимации и звука
        self.is_x2_now, self.non_active_answers = False, []
        # is_x2_now — активно ли «право на ошибку» прямо сейчас,
        # non_active_answers — неактивные кнопки ответов после 50:50 и «права на ошибку»
        self.lifelines = {'change': True, '50:50': True, 'x2': True}

        self.player1 = QMediaPlayer()  # для музыки во время вопроса и неправильных ответов
        self.player2 = QMediaPlayer()  # для интро и правильных ответов
        self.player3 = QMediaPlayer()  # для музыки перед вопросм, подсказки 50:50 и смены вопроса
        self.player4 = QMediaPlayer()  # для подсказки ×2
        self.is_sound = True

        self.new_game.triggered.connect(self.openConfirmAgain)
        self.close_game.triggered.connect(self.openConfirmClose)
        self.about.triggered.connect(self.openAbout)
        self.open_table.triggered.connect(self.openTable)
        self.clear_one.triggered.connect(self.openDeleteResultForm)
        self.clear_all.triggered.connect(self.openConfirmClearAll)
        self.sound_btn.triggered.connect(self.checkSound)
        self.startGame()

    def user_control(func: Callable):
        '''Декоратор, деактивирующий управление игрой во время выполнения анимации

        Параметры
        ---------
        func: Callable
            функция с анимацией
        '''

        def wrapper(self, *args, **kwargs):
            def f(x): self.control = x
            self.time_function(1, f, False)
            func(self, *args, **kwargs)
            self.time_function(1, f, True)

        return wrapper

    def time_function(self, time: int, func: Callable, *args):
        '''Метод, активирующий таймер для выполнения анимации

        Метод аналогичен time.sleep(), но не вызывает зависания в потоке Qt

        Параметры
        ---------
        time: int
            время выполнения анимации
        func: Callable
            запускаемая функция
        *args
            аргументы для func
        '''

        QTimer.singleShot(self.timer + time, partial(func, *args))
        # запускаем Qt-таймер с временем, через которое функция запустится
        # partial определяет функцию func с переданными аргументами args, но не выполняет её
        # singleShot черезе self.timer+time миллисекунд выполнит фунцию func
        self.timer += time

    @user_control
    def startGame(self, repeat: bool = False):
        '''Метод, запускающий анимацию начала игры и показывающий первый вопрос

        Параметры
        ---------
        repeat: bool = False
            первая ли эта игра в рамках сессии или нет (True, если не первая)
        '''

        self.date = datetime.today().strftime('%d.%m.%Y %H:%M')  # дата игры
        self.player2.setMedia(decorate_audio('sounds/intro.mp3' if not repeat else 'sounds/new_start.mp3'))
        self.time_function(0, self.layout_q.setPixmap, QPixmap("animations/question field/1.png"))
        self.player2.play()  # проигрываем саундтрек

        self.questions = get_questions()  # получаем вопросы для игры
        self.current_number = 1  # номер вопроса

        for i in range(1, 24):
            self.time_function(20, self.layout_q.setPixmap, QPixmap('animations/question field/{}.png'.format(i)))
        self.time_function(0, self.layout_q.setPixmap, QPixmap("images/question field/layout.png"))

        for i in range(1, 16):
            self.time_function(
                200, self.current_state_t.setPixmap,
                QPixmap('images/money tree/{}.png'.format(i))
            )  # анимация денежного дерева
        for i in 'A', 'B', 'C', 'D':
            self.time_function(
                360, self.current_state_q.setPixmap,
                QPixmap('images/question field/chosen_{}.png'.format(i))
            )  # анимация 4 ответов

        self.time_function(300, self.current_state_q.setPixmap, QPixmap())
        self.time_function(
            200, self.current_state_t.setPixmap,
            QPixmap('images/money tree/{}.png'.format(self.current_number))
        )  # стираем слои после проигравшейся анимации и переводим в начальное положение

        self.time_function(500, self.updateQuestionField)  # обновляем текстовые блоки вопроса и ответов
        self.time_function(0, self.question.startFadeIn)  # показываем вопрос
        for a in [self.answer_A, self.answer_B, self.answer_C, self.answer_D]:  # показываем ответы
            self.time_function(100, a.startFadeIn)
            self.time_function(0, a.show)

        n = '1-4' if self.current_number in [1, 2, 3, 4] else self.current_number
        self.player1.setMedia(decorate_audio('sounds/{}/bed.mp3'.format(n)))
        self.time_function(2500, self.player1.play)  # задаём фоновый трек и проигрываем
        logging.info('Game is OK. Username: %s', self.name)

    def updateQuestionField(self, changer: bool = False):
        '''Метод, обновляющий текстовые поля вопроса и ответов

        Параметры
        ---------
        changer: bool = False
            активна ли подсказка «замена вопроса» прямо сейчас
        '''

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
        logging.info('Q%d set', self.current_number)

    def keyPressEvent(self, event: QKeyEvent):
        '''Метод, обрабатывающий нажатия клавиши клавиатуры

        Параметры
        ---------
        event: QKeyEvent
            содержит в себе объект события с подробным описанием нажатой клавиши/комбинации
        '''

        if event.key() < 1500:  # логирование только для клавиш клавиатуры
            logging.info('KP %d', event.key())
        if event.key() in [Qt.Key_Q, 91, 1049, 1061]:  # Q, Й, [, Х
            self.checkPosition(200, 601)  # эмулируем выбор ответа A
        if event.key() in [Qt.Key_W, 93, 1062, 1066]:  # W, Ц, ], Ъ
            self.checkPosition(568, 601)  # эмулируем выбор ответа В
        if event.key() in [Qt.Key_A, 59, 1060, 1046]:  # A, Ф, ;, Ж
            self.checkPosition(200, 653)  # эмулируем выбор ответа С
        if event.key() in [Qt.Key_S, 39, 1067, 1069]:  # S, Ы, ', Э
            self.checkPosition(568, 653)  # эмулируем выбор ответа D
        if event.key() == Qt.Key_1:
            self.checkPosition(766, 100)  # эмулируем выбор «замены вопроса»
        if event.key() == Qt.Key_2:
            self.checkPosition(835, 100)  # эмулируем выбор 50:50
        if event.key() == Qt.Key_3:
            self.checkPosition(902, 100)  # эмулируем выбор «права на ошибку»
        if event.key() == Qt.Key_4:
            self.checkPosition(970, 100)  # эмулируем выбор «забрать деньги»
        if event.key() in [Qt.Key_M, 1068]:  # M, Ь
            self.is_sound = not self.is_sound  # переключаем звук
            self.sound_btn.setChecked(self.is_sound)
            for p in [self.player1, self.player2, self.player3, self.player4]:
                p.setVolume(100 * self.is_sound)

    def mousePressEvent(self, event: QMouseEvent):
        '''Метод, обрабатывающий нажатия клавиши клавиатуры

        Параметры
        ---------
        event: QMouseEvent
            содержит в себе объект события с подробным описанием нажатой кнопки мыши
        '''

        self.checkPosition(event.x(), event.y())  # делегируем обработку события на checkPosition

    def checkPosition(self, x: int, y: int):
        '''Метод, обрабатывающий переданные координаты в действие

        Параметры
        ---------
        x: int
            x-координата
        y: int
            y-координата
        '''

        logging.info('MP (%d, %d)', x, y)
        if self.control:
            self.timer, n = 0, self.current_number
            # каждое действие можно совершать при отработанной анимации,
            # поэтому таймер для time_function можно сбрасывать

            if len(self.non_active_answers) in [1, 3]:
                # 1 неактивный ответ — после использования «права на ошибку»
                # 3 неактивных ответа — после использования 50:50 и «права на ошибку»
                self.player4.setMedia(decorate_audio('sounds/double/second_final.mp3'))
            elif not self.is_x2_now and n not in [1, 2, 3, 4, 5]:
                # после пятого вопроса каждый ответ озвучивается отдельным треком
                self.player4.setMedia(decorate_audio('sounds/{}/final_answer.mp3'.format(n)))
            elif self.is_x2_now:
                self.player4.setMedia(decorate_audio('sounds/double/first_final.mp3'))
            if 200 <= x <= 538 and 601 <= y <= 642:  # ответ А
                if 'A' not in self.non_active_answers:
                    self.current_state_q.setPixmap(QPixmap('images/question field/chosen_A.png'))
                    self.current_state_q.startFadeInImage()
                    if n not in [1, 2, 3, 4, 5] or self.is_x2_now:
                        self.player1.stop()
                        self.time_function(0, self.player4.play)
                    logging.info('Answ[A]')
                    self.time_function(400, self.checkAnswer, self.answer_A, 'A')
            elif 568 <= x <= 915 and 601 <= y <= 642:  # ответ В
                if 'B' not in self.non_active_answers:
                    self.current_state_q.setPixmap(QPixmap('images/question field/chosen_B.png'))
                    self.current_state_q.startFadeInImage()
                    if n not in [1, 2, 3, 4, 5] or self.is_x2_now:
                        self.player1.stop()
                        self.time_function(0, self.player4.play)
                    logging.info('Answ[B]')
                    self.time_function(400, self.checkAnswer, self.answer_B, 'B')
            elif 200 <= x <= 538 and 653 <= y <= 693:  # ответ С
                if 'C' not in self.non_active_answers:
                    self.current_state_q.setPixmap(QPixmap('images/question field/chosen_C.png'))
                    self.current_state_q.startFadeInImage()
                    if n not in [1, 2, 3, 4, 5] or self.is_x2_now:
                        self.player1.stop()
                        self.time_function(0, self.player4.play)
                    logging.info('Answ[C]')
                    self.time_function(400, self.checkAnswer, self.answer_C, 'C')
            elif 568 <= x <= 915 and 653 <= y <= 693:  # ответ D
                if 'D' not in self.non_active_answers:
                    self.current_state_q.setPixmap(QPixmap('images/question field/chosen_D.png'))
                    self.current_state_q.startFadeInImage()
                    if n not in [1, 2, 3, 4, 5] or self.is_x2_now:
                        self.player1.stop()
                        self.time_function(0, self.player4.play)
                    logging.info('Answ[D]')
                    self.time_function(400, self.checkAnswer, self.answer_D, 'D')

            if 766 <= x <= 816 and 99 <= y <= 129:  # смена вопроса
                self.lost_change.show()
                self.lost_change.startFadeInImage()
                self.useLifeline('change')
            elif 835 <= x <= 885 and 99 <= y <= 129:  # 50:50
                self.lost_5050.show()
                self.lost_5050.startFadeInImage()
                self.useLifeline('50:50')
            elif 902 <= x <= 952 and 99 <= y <= 129:  # право на ошибку
                self.lost_x2.show()
                self.lost_x2.startFadeInImage()
                if self.lifelines['x2']:
                    self.double_dip.show()
                    self.double_dip.startFadeInImage()
                self.useLifeline('x2')
            elif 970 <= x <= 1020 and 99 <= y <= 129:  # забрать деньги
                self.openConfirmLeave()

    def clear_all_labels(self):
        '''Метод, подчищающий все слои состояния и текстовые блоки
        '''

        self.time_function(0, self.question.setText, '')
        self.time_function(0, self.answer_A.setText, '')
        self.time_function(0, self.answer_B.setText, '')
        self.time_function(0, self.answer_C.setText, '')
        self.time_function(0, self.answer_D.setText, '')
        self.time_function(0, self.current_state_q.setPixmap, QPixmap())
        self.time_function(0, self.current_state_q_2.setPixmap, QPixmap())
        self.time_function(0, self.current_state_q_3.setPixmap, QPixmap())

    @user_control
    def checkAnswer(self, label: AnimationLabel, letter: str):
        '''Метод, обрабатывающий ответ игрока и проверяющий правильность ответа

        Декорирован user_control

        Параметры
        ---------
        label: AnimationLabel (наследован от QLabel)
            текстовое поле, содержащее текст ответа
        letter: str
            буква ответа
        '''

        user_answer = label.text()  # получаем из текстового поля текст ответа
        if user_answer != self.correct_answer:  # если ответа игрока не совпадает с правильным
            num_to_let = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
            x2_letter = letter  # задаём в x2_letter букву ответа игрока
            letter = num_to_let[self.answers.index(self.correct_answer)]
            # задаём в letter вместо буквы ответа игрока букву правильного ответа

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
        # для каждого из номеров вопроса выставляем паузу (задаёт интригу)

        if not self.is_x2_now or user_answer == self.correct_answer:
            n = '1-4' if self.current_number in [1, 2, 3, 4] else self.current_number
            if self.is_x2_now:  # убираем использованное «право на ошибку»
                self.time_function(0, self.double_dip.startFadeOutImage)
                self.is_x2_now = False
                logging.info('Answ correct (dd used)')
            if user_answer == self.correct_answer:  # правильный ответ без «права на ошибку» — играем музыку
                self.player2.setMedia(decorate_audio('sounds/{}/correct.mp3'.format(n)))
                self.time_function(0, self.player4.stop)
                self.time_function(0, self.player2.play)
                logging.info('Answ correct')
            else:  # неправильный ответ без «права на ошибку»
                self.player1.setMedia(decorate_audio('sounds/{}/lose.mp3'.format(n)))
                self.time_function(0, self.player4.stop)
                self.time_function(0, self.player1.play)
                logging.info('Answ incorrect')
            self.time_function(
                0, self.current_state_q_2.setPixmap,
                QPixmap('images/question field/correct_{}.png'.format(letter))
            )  # зажигаем правильный ответ
            self.time_function(0, self.current_state_q_2.startFadeInImage)
            self.time_function(0, self.current_state_q_2.show)
            for _ in range(2):
                self.time_function(400, self.current_state_q_2.startFadeOutImage)
                self.time_function(400, self.current_state_q_2.startFadeInImage)

        else:  # если используется «право на ошибку» и неправильный ответ игрока
            self.time_function(
                1500, self.current_state_q_3.setPixmap,
                QPixmap('images/question field/wrong_{}.png'.format(x2_letter))
            )  # зажигаем серым неправильный ответ
            self.time_function(0, self.player4.stop)
            self.player1.setMedia(decorate_audio('sounds/double/first_wrong.mp3'))
            self.time_function(0, self.player1.play)
            self.time_function(0, self.double_dip.startFadeOutImage)
            self.non_active_answers.append(x2_letter)  # добавляем неправильный ответ в список неактивных ответов

        if user_answer == self.correct_answer:  # правильный ответ — играем анимации
            if self.current_number != 15:  # для 15 вопроса отдельные анимации
                if self.current_number in [5, 10]:
                    self.time_function(0, self.player1.stop)
                    self.clear_all_labels()
                    self.time_function(0, self.layout_q.setPixmap, QPixmap('animations/sum/1.png'))
                    for i in range(1, 38):  # анимация показа суммы выигрыша
                        self.time_function(20, self.layout_q.setPixmap,
                                           QPixmap('animations/sum/{}.png'.format(i)))
                    self.time_function(
                        0, self.amount_q.setText,
                        PRICES[self.current_number]
                    )  # после 5 и 10 вопросов показываем сумму выигрыша
                    self.time_function(
                        3700, self.layout_q.setPixmap,
                        QPixmap('images/sum/amount.png')
                    )
                    self.player3.setMedia(decorate_audio('sounds/lights_down.mp3'))  # играем трек перед вопросом
                    self.time_function(0, self.player3.play)
                    self.time_function(750, self.amount_q.setText, '')  # зачищаем всё после показа суммы выигрыша
                    self.time_function(0, self.layout_q.setPixmap, QPixmap('animations/sum/37.png'))
                    for i in range(37, 0, -1):  # анимация показа блока с вопросом и ответами
                        self.time_function(20, self.layout_q.setPixmap,
                                           QPixmap('animations/sum/{}.png'.format(i)))
                    self.time_function(
                        0, self.layout_q.setPixmap,
                        QPixmap('images/question field/layout.png')
                    )
                    logging.info('%d got', self.current_number)

                self.current_number += 1  # поднимаем номер вопроса
                if self.current_number - 1 not in [1, 2, 3, 4]:
                    # для всех вопросов с 6-го свой бэкграунд-трек
                    self.time_function(
                        0, self.player1.setMedia,
                        decorate_audio('sounds/{}/bed.mp3'.format(self.current_number))
                    )
                    self.time_function(2500, self.player1.play)
                elif not self.lifelines['x2']:
                    # возвращаем предыдущий трек, если было «право на ошибку» в 1-5 вопросах
                    self.time_function(0, self.player1.setMedia, decorate_audio('sounds/1-4/bed.mp3'))
                    self.time_function(8, self.player1.play)

                self.time_function(
                    800 * (self.current_number - 1 not in [5, 10]), self.current_state_t.setPixmap,
                    QPixmap('images/money tree/{}.png'.format(self.current_number))
                )  # поднимаем уровень на денежном дереве
                self.time_function(0, self.current_state_q.setPixmap, QPixmap())
                self.time_function(0, self.current_state_q_2.setPixmap, QPixmap())
                self.time_function(0, self.current_state_q_3.setPixmap, QPixmap())
                self.time_function(0, self.updateQuestionField)  # обновляем текстовые поля для нового вопроса
                self.time_function(0, self.question.startFadeIn)  # показываем вопрос
                for a in [self.answer_A, self.answer_B, self.answer_C, self.answer_D]:
                    # показываем 4 ответа на новый вопрос
                    self.time_function(100, a.startFadeIn)
                    self.time_function(0, a.show)
                self.time_function(0, self.player2.stop)

            else:  # если дошли до 15 вопроса
                self.time_function(1000, self.layout_q.setPixmap, QPixmap('animations/sum/1.png'))
                self.clear_all_labels()
                for i in range(1, 38):  # анимация показа суммы выигрыша
                    self.time_function(20, self.layout_q.setPixmap,
                                       QPixmap('animations/sum/{}.png'.format(i)))
                self.time_function(0, self.amount_q.setText, PRICES[self.current_number])
                sql_request('''INSERT INTO results
                            (name, result, date)
                            VALUES ("{}", "{}", "{}")
                            '''.format(self.name, '3 000 000', self.date))  # записываем в бд выигрыш
                self.time_function(1000, self.showWin)  # показываем окно победы

        if user_answer != self.correct_answer and not self.is_x2_now:
            # если ответ неправильный и не было активно «право на ошибку»
            result_game = GUARANTEED_PRICES[self.current_number - 1]
            self.time_function(0, self.showGameOver,
                               [letter, result_game, self.is_sound])  # показываем проигрыш
            self.time_function(1000, self.layout_q.setPixmap, QPixmap('animations/sum/1.png'))
            self.clear_all_labels()
            for i in range(1, 38):  # анимация показа суммы выигрыша
                self.time_function(20, self.layout_q.setPixmap,
                                   QPixmap('animations/sum/{}.png'.format(i)))
            self.time_function(0, self.amount_q.setText, result_game)  # показываем сумму выигрыша
            sql_request('''INSERT INTO results
                           (name, result, date)
                           VALUES ("{}", "{}", "{}")
                        '''.format(self.name, result_game, self.date))  # записываем в бд выигрыш

        if self.is_x2_now:  # если было активно «право на ошибку», то со следующим вопросом снимаем его
            self.is_x2_now = False

    @user_control
    def useLifeline(self, type_ll: str):
        '''Метод, использующий подсказку type_ll

        Параметры
        ---------
        type_ll: str
            тип подсказки ("50:50", "x2" или "change")
        '''

        if self.lifelines[type_ll]:
            if type_ll == 'change':  # замена вопроса
                self.player3.setMedia(decorate_audio('sounds/change.mp3'))  # запускаем трек
                self.time_function(750, self.player3.play)
                self.time_function(800, self.updateQuestionField, True)
                if self.is_x2_now:  # на смене вопроса отменяем «право на ошибку»
                    self.time_function(0, self.double_dip.startFadeOutImage)
                self.time_function(0, self.question.startFadeIn)
                for a in [self.answer_A, self.answer_B, self.answer_C, self.answer_D]:
                    self.time_function(100, a.startFadeIn)
                    self.time_function(0, a.show)
                self.time_function(0, self.current_state_q.setPixmap, QPixmap())
                self.time_function(0, self.current_state_q_2.setPixmap, QPixmap())
                self.time_function(0, self.current_state_q_3.setPixmap, QPixmap())
                self.is_x2_now = False

            elif type_ll == 'x2':  # право на ошибку
                self.is_x2_now = True  # активируем подсказку
                self.player1.setMedia(decorate_audio('sounds/double/start.mp3'))  # запускаем трек
                self.player1.play()

            elif type_ll == '50:50':  # 50:50
                self.player3.setMedia(decorate_audio('sounds/50_50.mp3'))  # запускаем трек
                self.time_function(0, self.player3.play)
                answs = [self.answer_A, self.answer_B, self.answer_C, self.answer_D]
                answ_letters = ['A', 'B', 'C', 'D']
                if self.non_active_answers:  # неактивные ответы от «права на ошибку»
                    indxs = set([0, 1, 2, 3]) - set([answ_letters.index(self.non_active_answers[0])])
                else:
                    indxs = set([0, 1, 2, 3])
                indxs = list(indxs - set([self.answers.index(self.correct_answer)]))
                # из индексов вырезаем индекс правильного ответа
                shuffle(indxs)  # перемешиваем индекс, чтобы убрать два неверных ответа СЛУЧАЙНО
                answs[indxs[0]].setText('')
                answs[indxs[1]].setText('')
                self.non_active_answers += [answ_letters[indxs[0]], answ_letters[indxs[1]]]
                # добавляем ещё 2 неактивных ответа

            self.lifelines[type_ll] = False  # деактивируем дальнейший доступ к подсказке
            logging.info('- {}-ll'.format(type_ll))

    def restartGame(self):
        '''Метод, перезапускающий игру и возвращающий все значения в начальное состояние
        '''

        self.control = True
        self.timer, self.is_x2_now = 900, False  # 900 для синхронизации анимации и звука
        self.lifelines = {'change': True, '50:50': True, 'x2': True}
        for ll in [self.lost_change, self.lost_x2, self.lost_5050]:
            ll.hide()
        self.clear_all_labels()
        for p in [self.player1, self.player2, self.player3, self.player4]:
            p.stop()  # останавливаем все музыкальные плееры
        self.layout_q.setPixmap(QPixmap('images/question field/layout.png'))
        self.amount_q.setText('')
        self.startGame(True)  # начинаем игру с repeat = True

    def showWin(self):
        '''Метод, показывающий окно для победы
        '''

        self.win = WinWindow(self, self.is_sound)
        self.control = False  # отключаем управление в игре, чтобы игрок не продолжил игру после победы
        self.win.move(169 + self.x(), 210 + self.y())
        self.win.show()
        logging.info('Game over - player won')

    def showGameOver(self, data: list[str, str, bool]):
        '''Метод, показывающий окно для поражения

        Параметры
        ---------
        data: list[str, str, bool]
            содержит в себе правильный ответ, несгораемую сумму и is_sound (переключатель звука)
        '''

        self.control = False  # отключаем управление в игре, чтобы игрок не продолжил игру после победы
        self.game_over = GameOverWindow(self, data)
        self.game_over.move(169 + self.x(), 210 + self.y())
        self.game_over.show()
        logging.info('Game over - player lost')

    def openConfirmLeave(self):
        '''Метод, показывающий форму для подтверждения кнопки «забрать деньги»
        '''

        self.control = False
        num_to_let = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
        letter = num_to_let[self.answers.index(self.correct_answer)]  # получаем букву правильного ответа
        self.confirm_wndw = ConfirmLeaveWindow(self, letter, self.is_sound)
        # и передаём его, чтобы показать правильный ответ после взятия денег
        self.confirm_wndw.move(168 + self.x(), 216 + self.y())
        self.confirm_wndw.show()

    def openConfirmAgain(self):
        '''Метод, показывающий форму для подтверждения перезапуска игры
        '''

        self.confirm_wndw = ConfirmAgainWindow(self)
        self.confirm_wndw.move(168 + self.x(), 216 + self.y())
        self.confirm_wndw.show()

    def openConfirmClose(self):
        '''Метод, показывающий форму для подтверждения закрытия игры
        '''

        self.confirm_wndw = ConfirmCloseWindow()
        self.confirm_wndw.move(168 + self.x(), 216 + self.y())
        self.confirm_wndw.show()

    def openTable(self):
        '''Метод, показывающий таблицу результатов
        '''

        self.results_table = ResultsTableWindow()
        self.results_table.move(170 + self.x(), 93 + self.y())
        self.results_table.show()
        logging.info('Results table open')

    def openDeleteResultForm(self):
        '''Метод, показывающий форму для удаления одного результата из таблицы результатов
        '''

        self.delete_form = DeleteResultWindow()
        self.delete_form.move(147 + self.x(), 93 + self.y())
        self.delete_form.show()

    def openConfirmClearAll(self):
        '''Метод, показывающий форму для очистки таблицы результатов
        '''

        self.confirm_wndw = ConfirmClearAll()
        self.confirm_wndw.move(168 + self.x(), 216 + self.y())
        self.confirm_wndw.show()

    def openAbout(self):
        '''Метод, показывающий информацию об игре и разработчике
        '''

        self.about_wndw = AboutWindow(self, self.is_sound)
        for p in [self.player1, self.player2, self.player4]:
            p.setVolume(20 * self.is_sound)  # приглушаем треки из игры
        self.player3.setMedia(decorate_audio('sounds/about.mp3'))
        self.player3.play()  # включаем трек для этого онка
        self.about_wndw.move(178 + self.x(), 175 + self.y())
        self.about_wndw.show()
        logging.info('About open')

    def checkSound(self):
        '''Метод, переключающий звук (т.е. включает или отключает)
        '''

        if self.sender().isChecked():  # если галочка активна
            self.is_sound = True  # включаем музыку
        else:  # иначе
            self.is_sound = False  # отключаем

        for p in [self.player1, self.player2, self.player3, self.player4]:
            p.setVolume(100 * self.is_sound)  # устанавливаем звук на основе self.is_sound


class WinWindow(QDialog, Ui_Win):
    '''Класс типа QDialog, использующийся для отображения окна победы в игре

    Атрибуты
    --------
    parent: GameWindow
        класс основного окна игры
    is_sound
        определяет, включён или отключён ли звук

    Методы
    ------
    restart()
        Перезапускает игру и показывает таблицу результатов
    exit()
        Завершает игру и показывает таблицу результатов
    '''

    def __init__(self, parent: GameWindow, is_sound: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

        self.parent = parent  # родительское окно
        self.is_sound = is_sound

        self.buttonBox.accepted.connect(self.restart)
        self.buttonBox.rejected.connect(self.exit)

    def restart(self):
        '''Метод, перезапускающий игру и показывающий таблицу результатов
        '''

        self.parent.restartGame()  # перезапускаем игру в родительском окне
        self.close()
        self.results = ResultsTableWindow()
        self.results.move(170 + self.parent.x(), 93 + self.parent.y())
        self.results.show()  # показываем таблицу результатов
        logging.info('Game restart')

    def exit(self):
        '''Метод, завершающий игру и показывающий таблицу результатов
        '''

        self.parent.close()
        self.close()
        self.player = QMediaPlayer()
        self.player.setMedia(decorate_audio('sounds/quit_game.mp3'))  # запускаем трек конца игры
        if self.is_sound:
            self.player.play()
        self.results = ResultsTableWindow()
        self.results.show()
        logging.info('Game close\n')


class GameOverWindow(QDialog, Ui_GameOver):
    '''Класс типа QDialog, использующийся для отображения окна поражения в игре

    Атрибуты
    --------
    parent: GameWindow
        класс основного окна игры
    data: list[str, str, bool]
        содержит правильный ответ, несгораемую сумму и is_sound (переключатель звука)

    Методы
    ------
    restart()
        Перезапускает игру и показывает таблицу результатов
    exit()
        Завершает игру и показывает таблицу результатов
    '''

    def __init__(self, parent: GameWindow, data: list[str, str, bool]):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

        self.parent = parent  # родительское окно
        self.is_sound = data[2]
        self.buttonBox.accepted.connect(self.restart)
        self.buttonBox.rejected.connect(self.exit)
        self.label.setText(self.label.text().replace('{0}', data[0]).replace('{1}', data[1]))
        # заменяем плейсхолдеры на правильный ответ и выигрыш

    def restart(self):
        '''Метод, перезапускающий игру и показывающий таблицу результатов
        '''

        self.parent.restartGame()
        self.close()
        self.results = ResultsTableWindow()
        self.results.move(170 + self.parent.x(), 93 + self.parent.y())
        self.results.show()
        logging.info('Game restart')

    def exit(self):
        '''Метод, завершающий игру и показывающий таблицу результатов
        '''

        self.parent.close()
        self.close()
        self.player = QMediaPlayer()
        self.player.setMedia(decorate_audio('sounds/quit_game.mp3'))
        if self.is_sound:
            self.player.play()
        self.results = ResultsTableWindow()
        self.results.show()
        logging.info('Game close')


class ConfirmLeaveWindow(QDialog, Ui_ConfirmLeave):
    '''Класс типа QDialog, необходимый для подтверждения «забрать деньги»

    Атрибуты
    --------
    parent: GameWindow
        класс основного окна игры
    letter: str
        буква правильного ответа
    is_sound: bool
        определяет, включён или отключён ли звук

    Методы
    ------
    leave()
        Покидает игру и забирает деньги, предлагая сыграть ещё раз
    close_wndw()
        Закрывает окно подтверждения при отмене действия
    '''

    def __init__(self, parent: GameWindow, letter: str, is_sound: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

        self.parent = parent  # родительское окно
        self.correct = letter  # правильный ответ
        self.is_sound = is_sound
        self.label.setText(self.label.text().replace('{}', self.parent.got_amount))
        # заменяем плейсхолдер на сумму, с которой игрок хочет уйти
        self.buttonBox.accepted.connect(self.leave)
        self.buttonBox.rejected.connect(self.close_wndw)

    def leave(self):
        '''Метод, покидающий игру, забирающий деньги и предлагающий сыграть ещё раз
        '''

        sql_request('''INSERT INTO results
                       (name, result, date)
                       VALUES ("{}", "{}", "{}")
                    '''.format(self.parent.name, self.parent.got_amount, self.parent.date))
        # вставляем результат игры в таблицы
        self.windialog = WinLeaveWindow(self.parent, [self.correct, self.parent.got_amount, self.is_sound])
        # инициализируем окно после «забрать деньги»
        self.windialog.move(169 + self.parent.x(), 210 + self.parent.y())
        self.windialog.show()

        for p in [self.parent.player1, self.parent.player2, self.parent.player3, self.parent.player4]:
            p.stop()  # стопим все плееры
        self.parent.player1.setMedia(decorate_audio('sounds/walk_away.mp3'))  # запускаем музыку на «забрать деньги»
        self.parent.player1.play()
        self.parent.current_state_q_2.setPixmap(
            QPixmap('images/question field/correct_{}.png'.format(self.correct))
        )  # показываем правильный ответ
        self.parent.current_state_q_2.startFadeInImage()
        self.parent.current_state_q_2.show()

        logging.info('Game over — leave game')

        self.close()

    def close_wndw(self):
        '''Метод, закрывающий окно подтверждения при отмене действия
        '''

        self.parent.control = True
        self.close()


class WinLeaveWindow(Ui_WinLeave, GameOverWindow):
    '''Класс, наследующийся от GameOverWindow — необходим для подтверждения выхода из игры при забранных деньгах

    Атрибуты
    --------
    parent: GameWindow
        класс основного окна игры
    data: list[str, str, bool]
        содержит (по очереди) правильный ответ, выигрыш и булево, определяющее, включён ли звук или нет

    Методы
    ------
    restart()
        Перезапускает игру и показывает таблицу результатов
    exit()
        Завершает игру и показывает таблицу результатов
    '''

    pass


class ConfirmAgainWindow(QDialog, Ui_ConfirmAgain):
    '''Класс типа QDialog, необходим для подтверждения к кнопке «Начать новую игру»

    Атрибуты
    --------
    parent: GameWindow
        класс основного окна игры

    Методы
    ------
    restart()
        Перезапускает игру
    '''

    def __init__(self, parent: GameWindow):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.parent = parent  # родительское окно
        self.buttonBox.accepted.connect(self.restart)
        self.buttonBox.rejected.connect(self.close)

    def restart(self):
        '''Метод, перезапускающий игру
        '''

        self.parent.restartGame()
        logging.info('Game restart')
        self.close()


class ConfirmCloseWindow(QDialog, Ui_ConfirmExit):
    '''Класс типа QDialog, подтверждающий закрытие игры после нажатия кнопки «Закрыть игру» в экшнбаре

    Методы
    ------
    exit()
        Завершает игру и закрывает приложение
    '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.buttonBox.accepted.connect(self.exit)
        self.buttonBox.rejected.connect(self.close)

    def exit(self):
        '''Метод, завершающий игру и закрывающий приложение
        '''

        logging.info('Game close')
        sys.exit()


class ResultsTableWindow(QWidget, Ui_ResultsTable):
    '''Класс типа QWidget, отображающий таблицу результатов
    '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

        results = sql_request('SELECT * from results')  # запрашиваем результаты
        results = sorted(results, key=lambda x: int(str(x[2]).replace(' ', '')), reverse=True)  # сортируем по выигрышу
        results = [list(map(str, i[1:])) for i in results]

        makeTable(self.tableWidget, ['Имя', 'Результат', 'Дата и время'], results)
        self.okButton.clicked.connect(self.close)


class DeleteResultWindow(QWidget, Ui_DeleteResult):
    '''Класс типа QWidget, отображающий форму для удаления одного результата из таблицы

    Методы
    ------
    refreshTable()
        Обновляет таблицу после удаления одного результата
    deleteAction()
        Удаляет один результат по id из спинбокса
    '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.refreshTable()
        self.deleteButton.clicked.connect(self.deleteAction)

    def refreshTable(self):
        '''Метод, обновляющий таблицу результатов после удаления одного результата
        '''

        results = sql_request('SELECT * from results')
        results = sorted(results, key=lambda x: int(str(x[2]).replace(' ', '')), reverse=True)
        results = [list(map(str, i[1:])) for i in results]
        self.results = [list(map(str, [i + 1, results[i][2]])) for i in range(len(results))]

        self.deleteButton.setEnabled(bool(results))  # активируем кнопку удаления только при наличии результатов

        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(len(results))

        makeTable(self.tableWidget, ['Имя', 'Результат', 'Дата и время'], results)

    def deleteAction(self):
        '''Метод, удаляющий один результат по id результата из спинбокса

        Исключения
        ----------
        Exception
            если запрос через sql_request() вернулся с ошибкой
        '''

        id_result = self.spinBox.text()  # берём id результата из спинбокса
        result_date = list(filter(lambda x: x[0] == id_result, self.results))[0][1]
        result = sql_request('DELETE FROM results WHERE date = "{}"'.format(result_date))
        if 'ERROR' in result:
            raise Exception(result)
        else:
            logging.info('R%d delete', id_result)
        self.refreshTable()


class ConfirmClearAll(QDialog, Ui_ConfirmClearAll):
    '''Класс типа QDialog, использующийся для очистки всей таблицы результатов

    Методы
    -----
    deleteAllData()
        Очищает всю таблицу результатов
    '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.buttonBox.accepted.connect(self.deleteAllData)
        self.buttonBox.rejected.connect(self.close)

    def deleteAllData(self):
        '''Метод, очищающий всю таблицу результатов
        '''

        sql_request('DELETE FROM results')
        self.results_table = ResultsTableWindow()
        self.results_table.move(self.x(), self.y() - 117)
        self.results_table.show()
        logging.info('AllR delete')
        self.close()


class AboutWindow(QWidget, Ui_About):
    '''Класс типа QWidget, показывающий информацию о программе и разработчике

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
    '''

    def __init__(self, parent: GameWindow, is_sound: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.enText.hide()
        self.parent = parent  # родительское окно
        self.is_sound = is_sound
        self.ruButton.clicked.connect(self.showRuText)
        self.enButton.clicked.connect(self.showEnText)
        self.okButton.clicked.connect(self.close_wndw)

    def showRuText(self):
        '''Метод, показывающий русский текст информации о программе
        '''

        self.ruText.show()
        self.enText.hide()

    def showEnText(self):
        '''Метод, показывающий английский текст информации о программе
        '''

        self.enText.show()
        self.ruText.hide()

    def close_wndw(self):
        '''Метод, закрывающий окно при нажатии на кнопку «ОК»
        '''

        for p in [self.parent.player1, self.parent.player2, self.parent.player4]:
            p.setVolume(100 * self.is_sound)
        self.parent.player3.stop()
        self.close()

    def closeEvent(self, event: QCloseEvent):
        '''Метод, вызывающийся при закрытии окна
        '''

        for p in [self.parent.player1, self.parent.player2, self.parent.player4]:
            p.setVolume(100 * self.is_sound)
        self.parent.player3.stop()
        return super().closeEvent(event)


if __name__ == '__main__':
    sys.excepthook = excepthook

    logging.info(datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ': Session start')
    wndw = StartWindow()
    wndw.show()

    app.exec()
    logging.info('Session finish\n\n')
