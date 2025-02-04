import logging
from datetime import datetime
from random import shuffle

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QKeyEvent, QMouseEvent, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QMainWindow

from core.constants import GUARANTEED_PRICES, PRICES
from core.dialogs import (ConfirmAgainWindow, ConfirmClearAll, ConfirmCloseWindow, ConfirmLeaveWindow, GameOverWindow,
                          WinWindow)
from core.tools import AnimationScheduler, decorate_audio, get_questions, sql_request
from core.widgets import AboutWindow, DeleteResultWindow, ResultsTableWindow
from ui import AnimationLabel, Ui_MainWindow


class GameWindow(QMainWindow, Ui_MainWindow):
    """Класс типа QMainWindow, использующийся для отображения основного игрового контента

    Атрибуты
    --------
    name: str
        имя игрока
    mode: str
        режим игры (принимает значения "classic" и "clock")

    Методы
    ------
    user_control(func)
        Декоратор, деактивирующий управление игрой во время выполнения анимации
    time_function(time, func, *args)
        Активирует таймер для выполнения анимаций (обёртка)
    startGame(repeat)
        Активирует анимацию начала игры и показывает первый вопрос
    showAnswers()
        Показывает ответы на вопрос
    mergeTheTimer()
        Отсчитывает секунду от таймера в режиме на время
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
    """

    def __init__(self, name: str = '', mode: str = 'classic'):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.user_control = False  # реагирует ли игра на действия игрока
        self.name = name
        self.mode = mode
        self.has_shown = True if self.mode == 'classic' else False

        self.is_x2_now = False
        self.non_active_answers = []
        self.lifelines = {'change': True, '50:50': True, 'x2': True}

        self.player1 = QMediaPlayer()  # для музыки во время вопроса и неправильных ответов
        self.player2 = QMediaPlayer()  # для интро и правильных ответов
        self.player3 = QMediaPlayer()  # для музыки перед вопросом, подсказки 50:50 и смены вопроса
        self.player4 = QMediaPlayer()  # для подсказки x2
        self.is_sound = True
        self.scheduler1 = AnimationScheduler(self)
        self.scheduler2 = AnimationScheduler(self)  # для анимации ответов, запасной

        self.new_game.triggered.connect(self.openConfirmAgain)
        self.close_game.triggered.connect(self.openConfirmClose)
        self.about.triggered.connect(self.openAbout)
        self.open_table.triggered.connect(self.openTable)
        self.clear_one.triggered.connect(self.openDeleteResultForm)
        self.clear_all.triggered.connect(self.openConfirmClearAll)
        self.sound_btn.triggered.connect(self.checkSound)
        self.startGame()

    def switch_user_control(self, is_available_to_control: bool):
        self.user_control = is_available_to_control

    def startGame(self, repeat: bool = False):
        """Метод, запускающий анимацию начала игры и показывающий первый вопрос

        Параметры
        ---------
        repeat: bool = False
            первая ли эта игра в рамках сессии или нет (True, если не первая)
        """

        self.date = datetime.today().strftime('%d.%m.%Y %H:%M')  # дата игры

        self.scheduler1.schedule(1000, lambda a: a, True)
        if self.mode == 'classic':
            self.player2.setMedia(decorate_audio('sounds/intro.mp3' if not repeat else 'sounds/new_start.mp3'))
        else:
            self.player2.setMedia(
                decorate_audio('sounds/intro_clock.mp3' if not repeat else 'sounds/new_start_clock.mp3')
            )
            if repeat:
                self.timer_view.setPixmap(QPixmap())
                self.timer_text.setText('')
                self.double_dip.setPixmap(QPixmap('images/double-dip.png'))
        if repeat:
            self.double_dip.hide()

        self.scheduler1.schedule(0, self.layout_q.setPixmap, QPixmap('animations/question field/1.png'))
        self.scheduler1.schedule(0, self.player2.play)  # проигрываем саундтрек

        self.questions = get_questions()  # получаем вопросы для игры
        self.current_question_num = 1  # God mode

        for i in range(1, 24):
            self.scheduler1.schedule(30, self.layout_q.setPixmap, QPixmap(f'animations/question field/{i}.png'))
        self.scheduler1.schedule(0, self.layout_q.setPixmap, QPixmap('images/question field/layout.png'))
        self.scheduler1.schedule(600 - 150 * int(self.mode == 'clock'), lambda a: a, True)

        for i in range(1, 16):
            self.scheduler1.schedule(
                220 + 32 * int(self.mode == 'clock'),
                self.current_state_t.setPixmap,
                QPixmap(f'images/money tree/{i}.png'),
            )  # анимация денежного дерева
        if self.mode == 'clock':
            self.scheduler1.schedule(500, lambda a: a, True)
        for i in ('A', 'B', 'C', 'D'):
            self.scheduler1.schedule(
                450, self.current_state_q.setPixmap, QPixmap(f'images/question field/chosen_{i}.png')
            )  # анимация 4 ответов

        self.scheduler1.schedule(500, self.current_state_q.setPixmap, QPixmap())
        self.scheduler1.schedule(
            1000 + 600 * int(self.mode == 'clock'),
            self.current_state_t.setPixmap,
            QPixmap(f'images/money tree/{self.current_question_num}.png'),
        )  # стираем слои после проигравшейся анимации и переводим в начальное положение

        if self.mode == 'classic':
            self.scheduler1.schedule(500, self.updateQuestionField)  # обновляем текстовые блоки вопроса и ответов
            self.scheduler1.schedule(0, self.question.startFadeIn)  # показываем вопрос
            self.scheduler1.schedule(0, self.showAnswers)

        n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
        self.player1.setMedia(decorate_audio(f'sounds/{n}/bed.mp3'))
        self.scheduler1.schedule(2500 if self.mode != 'clock' else 0, self.player1.play)
        if not self.is_sound:
            self.scheduler1.schedule(0, self.player1.setVolume, 30 if self.mode == 'clock' else 100)
            # задаём фоновый трек и проигрываем его

        if self.mode == 'clock':
            self.player3.setMedia(decorate_audio('sounds/question_show_clock.mp3'))
            self.scheduler1.schedule(500, self.player3.play)
            self.scheduler1.schedule(300, self.updateQuestionField)  # обновляем текстовые блоки вопроса и ответов
            self.scheduler1.schedule(0, self.question.startFadeIn)  # показываем вопрос
            self.scheduler1.schedule(300, lambda a: a, True)
            for i in range(1, 19):  # показываем таймер
                self.scheduler1.schedule(30, self.timer_view.setPixmap, QPixmap(f'animations/timer/{i}.png'))
            for i in range(0, 16):  # анимируем его пополнение
                dial = 1 if n in ('1-4', 5) else (2 if n in range(6, 11) else (3 if n in range(11, 15) else 6))
                self.scheduler1.schedule(0, self.timer_text.setText, str(i * dial))
                self.scheduler1.schedule(50, self.timer_view.setPixmap, QPixmap(f'images/timer/{i}.png'))
            self.scheduler1.schedule(0, self.double_dip.setPixmap, QPixmap('images/show-button.png'))
            self.scheduler1.schedule(0, self.double_dip.show)  # подменяем кнопку по центру на кнопку показа ответа
            self.scheduler1.schedule(0, self.double_dip.startFadeInImage)

        self.scheduler1.start()

        logging.info('Game is OK. Mode: %s. Username: %s', self.mode, self.name)

    def showAnswers(self):
        """Метод, показывающий ответы на вопрос"""

        for answer_text_field in (self.answer_A, self.answer_B, self.answer_C, self.answer_D):
            self.scheduler2.schedule(100, answer_text_field.startFadeIn)
            self.scheduler2.schedule(0, answer_text_field.show)

        if self.mode == 'clock':
            self.has_shown = True
            n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
            self.scheduler2.schedule(0, self.double_dip.startFadeOutImage)
            self.scheduler2.schedule(200, self.double_dip.setPixmap, QPixmap('images/double-dip.png'))
            self.scheduler2.schedule(0, self.double_dip.hide)

            self.qttimer = QTimer(self)
            self.qttimer.timeout.connect(self.mergeTimer)
            self.qttimer.start(1000)

            if n in ('1-4', 5):
                self.player2.setMedia(decorate_audio(f'sounds/{n}/clock.mp3'))
                self.scheduler2.schedule(500, self.player2.play)
                self.seconds_left = 15
            else:
                self.player1.setMedia(decorate_audio(f'sounds/{n}/bed_clock.mp3'))
                self.scheduler2.schedule(500, self.player1.play)
                self.scheduler2.schedule(0, self.player3.stop)
                if n in range(6, 11):
                    self.seconds_left = 30
                elif n in range(11, 15):
                    self.seconds_left = 45
                elif n == 15:
                    self.seconds_left = 90
        self.scheduler2.start()

    def mergeTimer(self):
        """Метод, отсчитывающий секунду от таймера в режиме на время"""

        n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
        dial = 1 if n in ('1-4', 5) else (2 if n in range(6, 11) else (3 if n in range(11, 15) else 6))
        dial = self.seconds_left // dial + 1 * (self.seconds_left % dial in range(1, dial))
        # синхронизирует анимацию таймера и секундомер
        self.scheduler1.schedule(0, self.timer_view.setPixmap, QPixmap(f'images/timer/{dial}.png'))
        self.scheduler1.schedule(0, self.timer_text.setText, str(self.seconds_left))

        if self.seconds_left == 0:  # если ответ не был дан
            self.qttimer.stop()

            result_game = GUARANTEED_PRICES[self.current_question_num - 1]
            num_to_let = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
            letter = num_to_let[self.answers.index(self.correct_answer)]

            self.scheduler1.schedule(2000 + 1000 * (n == 15), lambda a: a, True)

            self.player3.setMedia(decorate_audio(f'sounds/{n}/lose.mp3'))
            self.scheduler1.schedule(0, self.player1.stop)
            self.scheduler1.schedule(0, self.player2.stop)
            self.scheduler1.schedule(0, self.player3.play)
            logging.info("Time's up")

            self.scheduler1.schedule(
                0, self.current_state_q_2.setPixmap, QPixmap(f'images/question field/correct_{letter}.png')
            )  # зажигаем правильный ответ
            self.scheduler1.schedule(0, self.current_state_q_2.startFadeInImage)
            self.scheduler1.schedule(0, self.current_state_q_2.show)
            for _ in range(2):
                self.scheduler1.schedule(400, self.current_state_q_2.startFadeOutImage)
                self.scheduler1.schedule(400, self.current_state_q_2.startFadeInImage)

            self.scheduler1.schedule(3000, self.layout_q.setPixmap, QPixmap('animations/sum/1.png'))
            self.clear_all_labels()

            for i in range(18, 0, -1):  # скрываем таймер
                self.scheduler1.schedule(30, self.timer_view.setPixmap, QPixmap(f'animations/timer/{i}.png'))
            self.scheduler1.schedule(30, self.timer_view.setPixmap, QPixmap())
            self.scheduler1.schedule(0, self.showGameOver, [letter, result_game, self.is_sound])  # показываем проигрыш

            for i in range(1, 38):  # анимация показа суммы выигрыша
                self.scheduler1.schedule(30, self.layout_q.setPixmap, QPixmap(f'animations/sum/{i}.png'))
            self.scheduler1.schedule(0, self.amount_q.setText, result_game)  # показываем сумму выигрыша
            sql_request(
                f'INSERT INTO results (name, result, date) VALUES ("{self.name}", "{result_game}", "{self.date}")'
            )  # записываем в бд выигрыш
        self.scheduler1.start()
        self.seconds_left -= 1

    def updateQuestionField(self, changer: bool = False):
        """Метод, обновляющий текстовые поля вопроса и ответов

        Параметры
        ---------
        changer: bool = False
            активна ли подсказка «замена вопроса» прямо сейчас
        """

        self.non_active_answers = []
        text = self.questions[self.current_question_num - 1][int(changer)][0]
        self.answers = list(map(str, self.questions[self.current_question_num - 1][int(changer)][2]))
        self.correct_answer = str(self.questions[self.current_question_num - 1][int(changer)][1])
        # print(self.correct_answer)  # God mode
        self.got_amount = PRICES[self.current_question_num - 1]
        for answer_text_field in (self.answer_A, self.answer_B, self.answer_C, self.answer_D):
            answer_text_field.hide()
        self.question.setText(text)
        for i, answer_text_field in enumerate((self.answer_A, self.answer_B, self.answer_C, self.answer_D)):
            answer_text_field.setText(self.answers[i])
        logging.info('Q%d set', self.current_question_num)

    def keyPressEvent(self, event: QKeyEvent):
        """Метод, обрабатывающий нажатия клавиши клавиатуры

        Параметры
        ---------
        event: QKeyEvent
            содержит в себе объект события с подробным описанием нажатой клавиши/комбинации
        """

        if event.key() < 1500:  # логирование только для клавиш клавиатуры
            logging.info('KP %d', event.key())
        if event.key() in (Qt.Key.Key_Q, 91, 1049, 1061):  # Q, Й, [, Х
            self.checkPosition(200, 601)  # эмулируем выбор ответа A
        if event.key() in (Qt.Key.Key_W, 93, 1062, 1066):  # W, Ц, ], Ъ
            self.checkPosition(568, 601)  # эмулируем выбор ответа В
        if event.key() in (Qt.Key.Key_A, 59, 1060, 1046):  # A, Ф, ;, Ж
            self.checkPosition(200, 653)  # эмулируем выбор ответа С
        if event.key() in (Qt.Key.Key_S, 39, 1067, 1069):  # S, Ы, ', Э
            self.checkPosition(568, 653)  # эмулируем выбор ответа D
        if event.key() == Qt.Key.Key_1:
            self.checkPosition(766, 100)  # эмулируем выбор «замены вопроса»
        if event.key() == Qt.Key.Key_2:
            self.checkPosition(835, 100)  # эмулируем выбор 50:50
        if event.key() == Qt.Key.Key_3:
            self.checkPosition(902, 100)  # эмулируем выбор «права на ошибку»
        if event.key() == Qt.Key.Key_4:
            self.checkPosition(970, 100)  # эмулируем выбор «забрать деньги»
        if event.key() in (Qt.Key.Key_M, 1068):  # M, Ь
            self.is_sound = not self.is_sound  # переключаем звук
            self.sound_btn.setChecked(self.is_sound)
            for p in (self.player1, self.player2, self.player3, self.player4):
                p.setVolume(100 * self.is_sound)

    def mousePressEvent(self, event: QMouseEvent):
        """Метод, обрабатывающий нажатия клавиши клавиатуры

        Параметры
        ---------
        event: QMouseEvent
            содержит в себе объект события с подробным описанием нажатой кнопки мыши
        """

        self.checkPosition(event.x(), event.y())  # делегируем обработку события на checkPosition

    def checkPosition(self, x: int, y: int):
        """Метод, обрабатывающий переданные координаты в действие

        Параметры
        ---------
        x: int
            x-координата
        y: int
            y-координата
        """

        logging.info('MP (%d, %d)', x, y)

        if all((self.user_control, self.mode == 'clock', 521 <= x <= 584, 627 <= y <= 665)):
            self.timer = 0
            self.showAnswers()

        if not self.user_control or not (self.has_shown or self.mode == 'classic'):
            return

        if len(self.non_active_answers) in (1, 3):
            # 1 неактивный ответ — после использования «права на ошибку»
            # 3 неактивных ответа — после использования 50:50 и «права на ошибку»
            self.player4.setMedia(decorate_audio('sounds/double/second_final.mp3'))
        elif not self.is_x2_now and self.current_question_num not in range(1, 6):
            # после пятого вопроса каждый ответ озвучивается отдельным треком
            self.player4.setMedia(decorate_audio(f'sounds/{self.current_question_num}/final_answer.mp3'))
        elif self.is_x2_now:
            self.player4.setMedia(decorate_audio('sounds/double/first_final.mp3'))
        if 200 <= x <= 538 and 601 <= y <= 642:
            self.chooseAnswer('A')
        elif 568 <= x <= 915 and 601 <= y <= 642:
            self.chooseAnswer('B')
        elif 200 <= x <= 538 and 653 <= y <= 693:
            self.chooseAnswer('C')
        elif 568 <= x <= 915 and 653 <= y <= 693:
            self.chooseAnswer('D')
        self.scheduler1.start()

        if 766 <= x <= 816 and 99 <= y <= 129:
            self.showLostLifeline(self.lost_change)
            self.useLifeline('change')
        elif 835 <= x <= 885 and 99 <= y <= 129:
            self.showLostLifeline(self.lost_5050)
            self.useLifeline('50:50')
        elif 902 <= x <= 952 and 99 <= y <= 129:
            self.showLostLifeline(self.lost_x2)
            if self.lifelines['x2']:
                self.double_dip.show()
                self.double_dip.startFadeInImage()
            self.useLifeline('x2')
        elif 970 <= x <= 1020 and 99 <= y <= 129:  # забрать деньги
            self.openConfirmLeave()

    def showLostLifeline(self, ll_button):
        ll_button.show()
        ll_button.startFadeInImage()

    def chooseAnswer(self, letter: str):
        if letter not in self.non_active_answers:
            self.current_state_q.setPixmap(QPixmap(f'images/question field/chosen_{letter}.png'))
            self.current_state_q.startFadeInImage()
            if self.mode == 'clock':
                self.player2.stop()
                self.qttimer.stop()
            if self.current_question_num not in range(1, 6) or self.is_x2_now:
                self.scheduler1.schedule(0, self.player1.stop)
                self.scheduler1.schedule(0, self.player4.play)
            logging.info(f'Answ[{letter}]')
            letter_to_button = {'A': self.answer_A, 'B': self.answer_B, 'C': self.answer_C, 'D': self.answer_D}
            self.scheduler1.schedule(400, self.checkAnswer, letter_to_button[letter], letter)

    def clear_all_labels(self):
        """Метод, подчищающий все слои состояния и текстовые блоки"""

        self.scheduler1.schedule(0, self.timer_text.setText, '')
        self.scheduler1.schedule(0, self.question.setText, '')
        self.scheduler1.schedule(0, self.answer_A.setText, '')
        self.scheduler1.schedule(0, self.answer_B.setText, '')
        self.scheduler1.schedule(0, self.answer_C.setText, '')
        self.scheduler1.schedule(0, self.answer_D.setText, '')
        self.scheduler1.schedule(0, self.current_state_q.setPixmap, QPixmap())
        self.scheduler1.schedule(0, self.current_state_q_2.setPixmap, QPixmap())
        self.scheduler1.schedule(0, self.current_state_q_3.setPixmap, QPixmap())
        self.scheduler1.start()

    def checkAnswer(self, label: AnimationLabel, letter: str):
        """Метод, обрабатывающий ответ игрока и проверяющий правильность ответа

        Декорирован user_control

        Параметры
        ---------
        label: AnimationLabel (наследован от QLabel)
            текстовое поле, содержащее текст ответа
        letter: str
            буква ответа
        """

        user_answer = label.text()  # получаем из текстового поля текст ответа
        if user_answer != self.correct_answer:  # если ответа игрока не совпадает с правильным
            num_to_let = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
            x2_letter = letter  # задаём в x2_letter букву ответа игрока
            letter = num_to_let[self.answers.index(self.correct_answer)]
            # задаём в letter вместо буквы ответа игрока букву правильного ответа

        if self.current_question_num in range(1, 5):
            self.scheduler1.schedule(2000 * self.is_x2_now, lambda a: a, True)
        elif self.current_question_num == 5:
            self.scheduler1.schedule(2000, lambda a: a, True)
            self.scheduler1.schedule(0, self.player1.setVolume, 100)
        elif self.current_question_num in range(6, 10):
            self.scheduler1.schedule(2500, lambda a: a, True)
        elif self.current_question_num == 10:
            self.scheduler1.schedule(3000, lambda a: a, True)
        elif self.current_question_num in (11, 12):
            self.scheduler1.schedule(3500, lambda a: a, True)
        elif self.current_question_num in (13, 14):
            self.scheduler1.schedule(4500, lambda a: a, True)
        elif self.current_question_num == 15:
            self.scheduler1.schedule(5500, lambda a: a, True)
        # для каждого из номеров вопроса выставляем паузу (задаёт интригу)

        if not self.is_x2_now or user_answer == self.correct_answer:
            n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
            if self.is_x2_now:  # убираем использованное «право на ошибку»
                self.scheduler1.schedule(0, self.double_dip.startFadeOutImage)
                logging.info('Answ correct (dd used)')
            if user_answer == self.correct_answer:  # правильный ответ без «права на ошибку» — играем музыку
                self.scheduler1.schedule(0, self.player2.setMedia, decorate_audio(f'sounds/{n}/correct.mp3'))
                self.scheduler1.schedule(0, self.player4.stop)
                self.scheduler1.schedule(0, self.player2.play)
                logging.info('Answ correct')
            else:  # неправильный ответ без «права на ошибку»
                self.scheduler1.schedule(0, self.player1.setMedia, decorate_audio(f'sounds/{n}/lose.mp3'))
                self.scheduler1.schedule(0, self.player4.stop)
                self.scheduler1.schedule(0, self.player2.stop)
                self.scheduler1.schedule(0, self.player1.play)
                logging.info('Answ incorrect')
            self.scheduler1.schedule(
                0, self.current_state_q_2.setPixmap, QPixmap(f'images/question field/correct_{letter}.png')
            )  # зажигаем правильный ответ
            self.scheduler1.schedule(0, self.current_state_q_2.startFadeInImage)
            self.scheduler1.schedule(0, self.current_state_q_2.show)
            for _ in range(2):
                self.scheduler1.schedule(400, self.current_state_q_2.startFadeOutImage)
                self.scheduler1.schedule(400, self.current_state_q_2.startFadeInImage)
            self.has_shown = False

        else:  # если используется «право на ошибку» и неправильный ответ игрока
            self.scheduler1.schedule(
                1500, self.current_state_q_3.setPixmap, QPixmap(f'images/question field/wrong_{x2_letter}.png')
            )  # зажигаем серым неправильный ответ
            self.scheduler1.schedule(0, self.player4.stop)
            self.scheduler1.schedule(0, self.player1.setMedia, decorate_audio('sounds/double/first_wrong.mp3'))
            self.scheduler1.schedule(0, self.player1.play)
            self.scheduler1.schedule(0, self.double_dip.startFadeOutImage)
            self.non_active_answers.append(x2_letter)  # добавляем неправильный ответ в список неактивных ответов

        if user_answer == self.correct_answer:  # правильный ответ — играем анимации
            if self.current_question_num != 15:
                if self.current_question_num in (5, 10):
                    self.scheduler1.schedule(0, self.player1.stop)
                    self.clear_all_labels()
                    self.scheduler1.schedule(0, self.layout_q.setPixmap, QPixmap('animations/sum/1.png'))
                    if self.mode == 'clock':
                        dial = 1 if n in ('1-4', 5) else (2 if n in range(6, 11) else (3 if n in range(11, 15) else 6))
                        for i in range(self.seconds_left // dial, -1, -1):  # анимируем опустошение таймера
                            self.scheduler1.schedule(0, self.timer_text.setText, str(i * dial))
                            self.scheduler1.schedule(30, self.timer_view.setPixmap, QPixmap(f'images/timer/{i}.png'))
                        self.scheduler1.schedule(0, self.timer_text.setText, '')
                        for i in range(18, 0, -1):  # скрываем его
                            self.scheduler1.schedule(
                                30, self.timer_view.setPixmap, QPixmap(f'animations/timer/{i}.png')
                            )
                        self.scheduler1.schedule(30, self.timer_view.setPixmap, QPixmap())
                    for i in range(1, 38):  # анимация показа суммы выигрыша
                        self.scheduler1.schedule(30, self.layout_q.setPixmap, QPixmap(f'animations/sum/{i}.png'))
                    self.scheduler1.schedule(
                        0, self.amount_q.setText, PRICES[self.current_question_num]
                    )  # после 5 и 10 вопросов показываем сумму выигрыша
                    self.scheduler1.schedule(3700, self.layout_q.setPixmap, QPixmap('images/sum/amount.png'))
                    self.scheduler1.schedule(
                        750 + 1000 * int(self.current_question_num == 10), self.amount_q.setText, ''
                    )
                    self.player3.setMedia(decorate_audio('sounds/lights_down.mp3'))  # играем трек перед вопросом
                    self.scheduler1.schedule(0, self.player3.play)
                    # зачищаем всё после показа суммы выигрыша
                    self.scheduler1.schedule(0, self.layout_q.setPixmap, QPixmap('animations/sum/37.png'))
                    for i in range(37, 0, -1):  # анимация показа блока с вопросом и ответами
                        self.scheduler1.schedule(30, self.layout_q.setPixmap, QPixmap(f'animations/sum/{i}.png'))
                    self.scheduler1.schedule(0, self.layout_q.setPixmap, QPixmap('images/question field/layout.png'))
                    logging.info('%d got', self.current_question_num)

                if self.current_question_num not in range(1, 5):
                    # для всех вопросов с 6-го свой бэкграунд-трек
                    self.scheduler1.schedule(
                        0, self.player1.setMedia, decorate_audio(f'sounds/{self.current_question_num + 1}/bed.mp3')
                    )
                    if self.mode == 'classic':
                        self.scheduler1.schedule(2500, self.player1.play)
                elif len(self.non_active_answers) in (1, 3) or self.is_x2_now:
                    # возвращаем предыдущий трек, если было «право на ошибку» в 1-5 вопросах
                    self.scheduler1.schedule(0, self.player1.setMedia, decorate_audio('sounds/1-4/bed.mp3'))
                    self.scheduler1.schedule(8, self.player1.play)

                if self.mode == 'clock':
                    if self.current_question_num not in range(1, 5):
                        self.player3.setMedia(
                            decorate_audio(f'sounds/{self.current_question_num + 1}/before_clock.mp3')
                        )
                    else:
                        self.player3.setMedia(decorate_audio('sounds/question_show_clock.mp3'))

                    if self.current_question_num in (5, 10):
                        self.scheduler1.schedule(1850, self.player3.play)
                    elif self.current_question_num in range(1, 5):
                        self.scheduler1.schedule(1000, self.player3.play)
                    elif self.current_question_num in range(6, 10):
                        self.scheduler1.schedule(2500, self.player3.play)
                    else:
                        self.scheduler1.schedule(3500, self.player3.play)
                    self.scheduler1.schedule(0, self.player2.stop)

                self.scheduler1.schedule(
                    800 * (self.current_question_num not in (5, 10)),
                    self.current_state_t.setPixmap,
                    QPixmap(f'images/money tree/{self.current_question_num + 1}.png'),
                )

                if self.mode == 'clock':
                    dial = 1 if n == '1-4' else (2 if n in range(5, 10) else (3 if n in range(10, 14) else 6))
                    for i in range(self.seconds_left // dial, -1, -1):  # анимируем опустошение таймера
                        self.scheduler1.schedule(0, self.timer_text.setText, str(i * dial))
                        self.scheduler1.schedule(40, self.timer_view.setPixmap, QPixmap(f'images/timer/{i}.png'))
                    if self.current_question_num not in list(range(1, 6)) + [10]:
                        self.scheduler1.schedule(2650 - 500 * int(self.current_question_num == 14), lambda a: a, True)
                    self.scheduler1.schedule(0, self.current_state_q.setPixmap, QPixmap())
                    self.scheduler1.schedule(0, self.current_state_q_2.setPixmap, QPixmap())
                    self.scheduler1.schedule(0, self.current_state_q_3.setPixmap, QPixmap())
                    self.scheduler1.schedule(300, self.updateQuestionField)
                    # обновляем текстовые блоки вопроса и ответов
                    self.scheduler1.schedule(0, self.question.startFadeIn)  # показываем вопрос
                    timer_animation_start = self.seconds_left // dial + 1
                    if self.current_question_num in (5, 10):
                        for i in range(1, 19):  # показываем таймер
                            self.scheduler1.schedule(
                                30, self.timer_view.setPixmap, QPixmap(f'animations/timer/{i}.png')
                            )
                        timer_animation_start = 0
                    if self.current_question_num == 14:
                        timer_animation_start = 0
                    for i in range(timer_animation_start, 16):  # анимируем пополнение таймера
                        self.scheduler1.schedule(0, self.timer_text.setText, str(i * dial))
                        self.scheduler1.schedule(50, self.timer_view.setPixmap, QPixmap(f'images/timer/{i}.png'))
                    self.scheduler1.schedule(0, self.double_dip.setPixmap, QPixmap('images/show-button.png'))
                    self.scheduler1.schedule(0, self.double_dip.show)
                    self.scheduler1.schedule(0, self.double_dip.startFadeInImage)
                else:
                    if self.current_question_num > 10:
                        self.scheduler1.schedule(1000, lambda a: a, True)
                    self.scheduler1.schedule(0, self.current_state_q.setPixmap, QPixmap())
                    self.scheduler1.schedule(0, self.current_state_q_2.setPixmap, QPixmap())
                    self.scheduler1.schedule(0, self.current_state_q_3.setPixmap, QPixmap())
                    self.scheduler1.schedule(0, self.updateQuestionField)  # обновляем текстовые поля для нового вопроса
                    self.scheduler1.schedule(0, self.question.startFadeIn)  # показываем вопрос
                    for answer_text_field in (self.answer_A, self.answer_B, self.answer_C, self.answer_D):
                        # показываем 4 ответа на новый вопрос
                        self.scheduler1.schedule(100, answer_text_field.startFadeIn)
                        self.scheduler1.schedule(0, answer_text_field.show)
                    self.scheduler1.schedule(0, self.player2.stop)
                self.current_question_num += 1

            else:  # если прошли 15 вопрос
                self.scheduler1.schedule(1000, self.layout_q.setPixmap, QPixmap('animations/sum/1.png'))
                self.clear_all_labels()
                if self.mode == 'clock':
                    dial = 1 if n in ('1-4', 5) else (2 if n in range(6, 11) else (3 if n in range(11, 15) else 6))
                    for i in range(self.seconds_left // dial, -1, -1):  # анимируем опустошение таймера
                        self.scheduler1.schedule(0, self.timer_text.setText, str(i * dial))
                        self.scheduler1.schedule(20, self.timer_view.setPixmap, QPixmap(f'images/timer/{i}.png'))
                    self.scheduler1.schedule(0, self.timer_text.setText, '')
                    for i in range(18, 0, -1):  # скрываем его
                        self.scheduler1.schedule(30, self.timer_view.setPixmap, QPixmap(f'animations/timer/{i}.png'))
                    self.scheduler1.schedule(30, self.timer_view.setPixmap, QPixmap())
                for i in range(1, 38):  # анимация показа суммы выигрыша
                    self.scheduler1.schedule(30, self.layout_q.setPixmap, QPixmap(f'animations/sum/{i}.png'))
                self.scheduler1.schedule(0, self.amount_q.setText, PRICES[self.current_question_num])
                sql_request(
                    f'INSERT INTO results (name, result, date) VALUES ("{self.name}", "3 000 000", "{self.date}")'
                )  # записываем в бд выигрыш
                self.scheduler1.schedule(1000, self.showWin)  # показываем окно победы

        if user_answer != self.correct_answer and not self.is_x2_now:
            # если ответ неправильный и не было активно «право на ошибку»
            result_game = GUARANTEED_PRICES[self.current_question_num - 1]
            self.scheduler1.schedule(0, self.showGameOver, [letter, result_game, self.is_sound])  # показываем проигрыш
            self.scheduler1.schedule(1000, self.layout_q.setPixmap, QPixmap('animations/sum/1.png'))
            self.clear_all_labels()
            if self.mode == 'clock':
                dial = 1 if n in ('1-4', 5) else (2 if n in range(6, 11) else (3 if n in range(11, 15) else 6))
                for i in range(self.seconds_left // dial, -1, -1):  # анимируем опустошение таймера
                    self.scheduler1.schedule(0, self.timer_text.setText, str(i * dial))
                    self.scheduler1.schedule(30, self.timer_view.setPixmap, QPixmap(f'images/timer/{i}.png'))
                self.scheduler1.schedule(0, self.timer_text.setText, '')
                for i in range(18, 0, -1):  # скрываем его
                    self.scheduler1.schedule(30, self.timer_view.setPixmap, QPixmap(f'animations/timer/{i}.png'))
                self.scheduler1.schedule(30, self.timer_view.setPixmap, QPixmap())
            for i in range(1, 38):  # анимация показа суммы выигрыша
                self.scheduler1.schedule(30, self.layout_q.setPixmap, QPixmap(f'animations/sum/{i}.png'))
            self.scheduler1.schedule(0, self.amount_q.setText, result_game)  # показываем сумму выигрыша
            sql_request(
                f'INSERT INTO results (name, result, date) VALUES ("{self.name}", "{result_game}", "{self.date}")'
            )  # записываем в бд выигрыш

        if self.is_x2_now:  # если было активно «право на ошибку», то со следующим вопросом снимаем его
            self.is_x2_now = False

        self.scheduler1.start()

    def useLifeline(self, type_ll: str):
        """Метод, использующий подсказку type_ll

        Параметры
        ---------
        type_ll: str
            тип подсказки ("50:50", "x2" или "change")
        """

        if self.lifelines[type_ll]:
            if type_ll == 'change':  # замена вопроса
                # запускаем трек
                self.player3.setMedia(
                    decorate_audio('sounds/change.mp3' if self.mode == 'classic' else 'sounds/change_clock.mp3')
                )
                self.scheduler1.schedule(750, self.player3.play)
                if self.mode == 'clock':
                    if self.current_question_num not in range(1, 5):
                        self.scheduler1.schedule(0, self.player1.stop)
                    self.scheduler1.schedule(0, self.player2.stop)
                    n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
                    dial = 1 if n in ('1-4', 5) else (2 if n in range(6, 11) else (3 if n in range(11, 15) else 6))
                    for i in range(0, 16):  # анимируем его пополнение
                        self.scheduler1.schedule(0, self.timer_text.setText, str(i * dial))
                        self.scheduler1.schedule(50, self.timer_view.setPixmap, QPixmap(f'images/timer/{i}.png'))
                    self.qttimer.stop()
                self.scheduler1.schedule(820, self.updateQuestionField, True)
                if self.is_x2_now:  # на смене вопроса отменяем «право на ошибку»
                    self.scheduler1.schedule(0, self.double_dip.startFadeOutImage)
                if self.is_x2_now or len(self.non_active_answers) in (1, 3):
                    n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
                    self.scheduler1.schedule(0, self.player1.setMedia, decorate_audio(f'sounds/{n}/bed.mp3'))
                    self.scheduler1.schedule(8, self.player1.play)
                self.scheduler1.schedule(0, self.question.startFadeIn)
                if self.mode == 'classic':
                    for answer_text_field in (self.answer_A, self.answer_B, self.answer_C, self.answer_D):
                        self.scheduler1.schedule(100, answer_text_field.startFadeIn)
                        self.scheduler1.schedule(0, answer_text_field.show)
                else:
                    self.scheduler1.schedule(0, self.double_dip.setPixmap, QPixmap('images/show-button.png'))
                    self.scheduler1.schedule(
                        0, self.double_dip.show
                    )  # подменяем кнопку по центру на кнопку показа ответа
                    self.scheduler1.schedule(0, self.double_dip.startFadeInImage)
                    self.has_shown = False
                self.scheduler1.schedule(0, self.current_state_q.setPixmap, QPixmap())
                self.scheduler1.schedule(0, self.current_state_q_2.setPixmap, QPixmap())
                self.scheduler1.schedule(0, self.current_state_q_3.setPixmap, QPixmap())
                self.is_x2_now = False

            elif type_ll == 'x2':  # право на ошибку
                self.is_x2_now = True  # активируем подсказку
                self.player1.setMedia(
                    decorate_audio(f'sounds/double/start{"_clock" if self.mode == "clock" else ""}.mp3')
                )  # запускаем трек
                if self.mode == 'clock':
                    self.player2.stop()
                    self.qttimer.stop()
                self.player1.play()

            elif type_ll == '50:50':  # 50:50
                self.player3.setMedia(decorate_audio('sounds/50_50.mp3'))  # запускаем трек
                self.scheduler1.schedule(0, self.player3.play)
                answs = [self.answer_A, self.answer_B, self.answer_C, self.answer_D]
                answ_letters = ['A', 'B', 'C', 'D']
                if self.non_active_answers:  # неактивные ответы от «права на ошибку»
                    indxs = set([0, 1, 2, 3]) - set([answ_letters.index(self.non_active_answers[0])])
                else:
                    indxs = set([0, 1, 2, 3])
                indxs = list(indxs - set([self.answers.index(self.correct_answer)]))
                # из индексов вырезаем индекс правильного ответа
                shuffle(indxs)  # перемешиваем индекс, чтобы убрать два неверных ответа СЛУЧАЙНО
                self.scheduler1.schedule(250, answs[indxs[0]].setText, '')
                self.scheduler1.schedule(0, answs[indxs[1]].setText, '')
                self.non_active_answers += [answ_letters[indxs[0]], answ_letters[indxs[1]]]
                # добавляем ещё 2 неактивных ответа

            self.lifelines[type_ll] = False  # деактивируем дальнейший доступ к подсказке
            self.scheduler1.start()
            logging.info(f'- {type_ll}-ll')

    def restartGame(self):
        """Метод, перезапускающий игру и возвращающий все значения в начальное состояние"""

        self.user_control = True
        self.timer, self.is_x2_now = 900, False  # 900 для синхронизации анимации и звука
        self.lifelines = {'change': True, '50:50': True, 'x2': True}
        for ll_button in (self.lost_change, self.lost_x2, self.lost_5050):
            ll_button.hide()
        self.clear_all_labels()
        for player in (self.player1, self.player2, self.player3, self.player4):
            player.stop()  # останавливаем все музыкальные плееры
        self.layout_q.setPixmap(QPixmap('images/question field/layout.png'))
        self.amount_q.setText('')
        self.startGame(True)  # начинаем игру с repeat = True

    def showWin(self):
        """Метод, показывающий окно для победы"""

        self.win = WinWindow(self, self.is_sound)
        self.user_control = False  # отключаем управление в игре, чтобы игрок не продолжил игру после победы
        self.win.move(169 + self.x(), 210 + self.y())
        self.win.show()
        logging.info('Game over - player won')

    def showGameOver(self, state: tuple[str, str, bool]):
        """Метод, показывающий окно для поражения

        Параметры
        ---------
        state: tuple[str, str, bool]
            содержит в себе правильный ответ, несгораемую сумму и is_sound (переключатель звука)
        """

        self.user_control = False  # отключаем управление в игре, чтобы игрок не продолжил игру после победы
        self.game_over = GameOverWindow(self, state)
        self.game_over.move(169 + self.x(), 210 + self.y())
        self.game_over.show()
        logging.info('Game over - player lost')

    def openConfirmLeave(self):
        """Метод, показывающий форму для подтверждения кнопки «забрать деньги»"""

        self.user_control = False
        num_to_let = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
        letter = num_to_let[self.answers.index(self.correct_answer)]  # получаем букву правильного ответа
        self.confirm_wndw = ConfirmLeaveWindow(self, letter, self.is_sound)
        # и передаём его, чтобы показать правильный ответ после взятия денег
        self.confirm_wndw.move(168 + self.x(), 216 + self.y())
        self.confirm_wndw.show()

    def openConfirmAgain(self):
        """Метод, показывающий форму для подтверждения перезапуска игры"""

        self.confirm_wndw = ConfirmAgainWindow(self)
        self.confirm_wndw.move(168 + self.x(), 216 + self.y())
        self.confirm_wndw.show()

    def openConfirmClose(self):
        """Метод, показывающий форму для подтверждения закрытия игры"""

        self.confirm_wndw = ConfirmCloseWindow()
        self.confirm_wndw.move(168 + self.x(), 216 + self.y())
        self.confirm_wndw.show()

    def openTable(self):
        """Метод, показывающий таблицу результатов"""

        self.results_table = ResultsTableWindow()
        self.results_table.move(170 + self.x(), 93 + self.y())
        self.results_table.show()
        logging.info('Results table open')

    def openDeleteResultForm(self):
        """Метод, показывающий форму для удаления одного результата из таблицы результатов"""

        self.delete_form = DeleteResultWindow()
        self.delete_form.move(147 + self.x(), 93 + self.y())
        self.delete_form.show()

    def openConfirmClearAll(self):
        """Метод, показывающий форму для очистки таблицы результатов"""

        self.confirm_wndw = ConfirmClearAll()
        self.confirm_wndw.move(168 + self.x(), 216 + self.y())
        self.confirm_wndw.show()

    def openAbout(self):
        """Метод, показывающий информацию об игре и разработчике"""

        self.about_wndw = AboutWindow(self, self.is_sound)
        for player in (self.player1, self.player2, self.player4):
            player.setVolume(20 * self.is_sound)  # приглушаем треки из игры
        self.player3.setMedia(decorate_audio('sounds/about.mp3'))
        self.player3.play()  # включаем трек для этого окна
        self.about_wndw.move(178 + self.x(), 175 + self.y())
        self.about_wndw.show()
        logging.info('About open')

    def checkSound(self):
        """Метод, переключающий звук (т.е. включает или отключает)"""

        if self.sender().isChecked():  # type: ignore | если галочка активна
            self.is_sound = True  # включаем музыку
        else:  # иначе
            self.is_sound = False  # отключаем

        for player in (self.player1, self.player2, self.player3, self.player4):
            player.setVolume(100 * self.is_sound)  # устанавливаем звук на основе self.is_sound

        if self.current_question_num in range(1, 6) and self.mode == 'clock':
            self.player1.setVolume(30 * self.is_sound)
