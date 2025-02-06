import logging
import sys
from bisect import bisect_right
from datetime import datetime
from random import shuffle

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QKeyEvent, QMouseEvent, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QMainWindow

from core.constants import MONEYTREE_AMOUNTS, SAFETY_NETS, SECONDS_FOR_QUESTION, SECONDS_PRICE
from core.dialogs import (ConfirmAgainWindow, ConfirmClearAll, ConfirmCloseWindow, ConfirmLeaveWindow, GameOverWindow,
                          WinWindow)
from core.tools import (AnimationScheduler, convert_amount_to_str, decorate_audio, empty_timer, get_questions,
                        hide_timer, refill_timer, show_prize, show_timer, sql_request)
from core.widgets import AboutWindow, DeleteResultWindow, ResultsTableWindow
from ui import AnimationLabel, Ui_MainWindow


class GameWindow(QMainWindow, Ui_MainWindow):
    """Окно, отображащее основной игровой контент"""

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
        self.seconds_prize = 0  # приз за сэкономленные секунды в режиме игры на время
        self.saved_seconds_prize = 0  # приз за секунды сохраняется из seconds_prize после 5 и 10 вопросов

        self.player1 = QMediaPlayer()  # для музыки во время вопроса и неправильных ответов
        self.player2 = QMediaPlayer()  # для интро и правильных ответов
        self.player3 = QMediaPlayer()  # для музыки перед вопросом, подсказки 50:50 и смены вопроса
        self.player4 = QMediaPlayer()  # для подсказки x2
        self.is_sound = True
        self.scheduler1 = AnimationScheduler(self)
        self.scheduler2 = AnimationScheduler(self)  # для анимации ответов, запасной

        self.new_game.triggered.connect(self.open_confirm_again)
        self.close_game.triggered.connect(self.open_confirm_close)
        self.about.triggered.connect(self.open_about)
        self.open_table.triggered.connect(self.open_results_table)
        self.clear_one.triggered.connect(self.open_delete_result_from)
        self.clear_all.triggered.connect(self.open_confirm_clear_all)
        self.sound_btn.triggered.connect(self.toggle_sound)
        self.start_game()

    def switch_user_control(self, is_available_to_control: bool):
        """Переключает реагирование игры на действия игрока"""
        self.user_control = is_available_to_control

    def start_game(self, repeat: bool = False):
        """Запускает анимацию начала игры и показывает первый вопрос"""

        self.date = datetime.today().strftime('%d.%m.%Y %H:%M')

        self.scheduler1.schedule(1000, lambda: True)
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

        self.scheduler1.schedule(0, self.player2.play)

        self.questions = get_questions()
        self.current_question_num = 1  # HACK God mode

        # анимация показа блока с вопросом и ответами
        if repeat:
            self.scheduler1.schedule(0, self.amount_q.setText, '')
            for i in range(37, 0, -1):
                self.scheduler1.schedule(30, self.layout_q.setPixmap, QPixmap(f'animations/sum/{i}.png'))
        else:
            for i in range(1, 24):
                self.scheduler1.schedule(30, self.layout_q.setPixmap, QPixmap(f'animations/question field/{i}.png'))
        self.scheduler1.schedule(0, self.layout_q.setPixmap, QPixmap('images/question field/layout.png'))
        self.scheduler1.schedule(600 - 150 * (self.mode == 'clock'), lambda: True)

        for i in range(1, 16):  # анимация денежного дерева
            self.scheduler1.schedule(
                220 + 32 * (self.mode == 'clock') - 27 * repeat,
                self.current_state_t.setPixmap,
                QPixmap(f'images/money tree/{i}.png'),
            )
        if self.mode == 'clock':
            self.scheduler1.schedule(500 * (not repeat), lambda: True)
        self.scheduler1.schedule(0, self.current_state_q.startFadeInImage)
        for i in ('A', 'B', 'C', 'D'):  # анимация 4 ответов
            self.scheduler1.schedule(
                450 - 80 * (repeat and self.mode == 'clock'),
                self.current_state_q.setPixmap,
                QPixmap(f'images/question field/chosen_{i}.png'),
            )

        self.scheduler1.schedule(
            450 - 80 * (repeat and self.mode == 'clock'), self.current_state_q.setPixmap, QPixmap()
        )
        self.scheduler1.schedule(
            1000 + 600 * (self.mode == 'clock') - 600 * (self.mode == 'clock' and repeat),
            self.current_state_t.setPixmap,
            QPixmap(f'images/money tree/{self.current_question_num}.png'),
        )

        if self.mode == 'classic':
            self.scheduler1.schedule(500, self.update_question_field)
            self.scheduler1.schedule(0, self.question.startFadeIn)
            self.scheduler1.schedule(0, self.show_answers)

        n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
        self.player1.setMedia(decorate_audio(f'sounds/{n}/bed.mp3'))
        self.scheduler1.schedule(2500 if self.mode != 'clock' else 0, self.player1.play)
        if not self.is_sound:
            self.scheduler1.schedule(0, self.player1.setVolume, 30 if self.mode == 'clock' else 100)

        if self.mode == 'clock':
            self.player3.setMedia(decorate_audio('sounds/question_show_clock.mp3'))
            self.scheduler1.schedule(500, self.player3.play)
            self.scheduler1.schedule(300, self.update_question_field)
            self.scheduler1.schedule(0, self.question.startFadeIn)
            self.scheduler1.schedule(300, lambda: True)
            show_timer(self)
            refill_timer(self, self.current_question_num)
            self.scheduler1.schedule(0, self.double_dip.setPixmap, QPixmap('images/show-button.png'))
            self.scheduler1.schedule(0, self.double_dip.show)
            self.scheduler1.schedule(0, self.double_dip.startFadeInImage)

        self.scheduler1.start()

        logging.info('Game is OK. Mode: %s. Username: %s', self.mode, self.name)

    def show_answers(self):
        """Анимирует показ возможных ответов на вопрос и запускает таймер в режиме на время"""

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
            self.qttimer.timeout.connect(self.merge_timer)
            self.qttimer.start(1000)

            self.seconds_left = SECONDS_FOR_QUESTION[n]

            if n in ('1-4', 5):
                self.player2.setMedia(decorate_audio(f'sounds/{n}/clock.mp3'))
                self.scheduler2.schedule(500, self.player2.play)
            else:
                self.player1.setMedia(decorate_audio(f'sounds/{n}/bed_clock.mp3'))
                self.scheduler2.schedule(500, self.player1.play)
                self.scheduler2.schedule(0, self.player3.stop)
        self.scheduler2.start()

    def merge_timer(self):
        """Отсчитывает секунду от таймера в режиме на время"""

        n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
        dial = 1 if n in ('1-4', 5) else (2 if n in range(6, 11) else (3 if n in range(11, 15) else 6))
        dial = self.seconds_left // dial + 1 * (self.seconds_left % dial in range(1, dial))

        self.scheduler1.schedule(0, self.timer_view.setPixmap, QPixmap(f'images/timer/{dial}.png'))
        self.scheduler1.schedule(0, self.timer_text.setText, str(self.seconds_left))
        self.scheduler1.start()

        if self.seconds_left == 0:
            self.qttimer.stop()

            num_to_let = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
            correct_answer_letter = num_to_let[self.answers.index(self.correct_answer)]

            self.scheduler1.schedule(2000 + 1000 * (n == 15), lambda: True)

            self.player3.setMedia(decorate_audio(f'sounds/{n}/lose.mp3'))
            self.scheduler1.schedule(0, self.player1.stop)
            self.scheduler1.schedule(0, self.player2.stop)
            self.scheduler1.schedule(0, self.player3.play)
            logging.info("Time's up")

            # мигалка правильного ответа
            self.show_correct_answer(correct_answer_letter)

            result_game = convert_amount_to_str(SAFETY_NETS[self.current_question_num - 1] + self.saved_seconds_prize)
            self.scheduler1.schedule(3000, lambda: True)
            self.scheduler1.schedule(0, self.timer_text.setText, '')
            self.clear_all_labels()
            hide_timer(self)
            show_prize(self, result_game)
            self.scheduler1.schedule(750, self.show_game_over, [correct_answer_letter, result_game, self.is_sound])

            sql_request(
                f'INSERT INTO results (name, result, date) VALUES ("{self.name}", "{result_game}", "{self.date}")'
            )
            self.scheduler1.start()
        self.seconds_left -= 1

    def keyPressEvent(self, event: QKeyEvent):
        """Обрабатывает события от клавиатуры"""

        if event.key() < 1500:  # логирование только для клавиш клавиатуры
            logging.info('KP %d', event.key())
        if event.key() in (Qt.Key.Key_Q, 91, 1049, 1061):  # Q, Й, [, Х
            self.response_event(200, 601)  # эмулируем выбор ответа A
        if event.key() in (Qt.Key.Key_W, 93, 1062, 1066):  # W, Ц, ], Ъ
            self.response_event(568, 601)  # эмулируем выбор ответа В
        if event.key() in (Qt.Key.Key_A, 59, 1060, 1046):  # A, Ф, ;, Ж
            self.response_event(200, 653)  # эмулируем выбор ответа С
        if event.key() in (Qt.Key.Key_S, 39, 1067, 1069):  # S, Ы, ', Э
            self.response_event(568, 653)  # эмулируем выбор ответа D
        if event.key() == Qt.Key.Key_1:
            self.response_event(766, 100)  # эмулируем выбор «замены вопроса»
        if event.key() == Qt.Key.Key_2:
            self.response_event(835, 100)  # эмулируем выбор 50:50
        if event.key() == Qt.Key.Key_3:
            self.response_event(902, 100)  # эмулируем выбор «права на ошибку»
        if event.key() == Qt.Key.Key_4:
            self.response_event(970, 100)  # эмулируем выбор «забрать деньги»
        if event.key() in (Qt.Key.Key_M, 1068):  # M, Ь
            self.is_sound = not self.is_sound  # переключаем звук
            self.sound_btn.setChecked(self.is_sound)
            for p in (self.player1, self.player2, self.player3, self.player4):
                p.setVolume(100 * self.is_sound)

    def mousePressEvent(self, event: QMouseEvent):
        """Обрабатывает события от мыши"""

        self.response_event(event.x(), event.y())  # делегируем обработку события на checkPosition

    def response_event(self, x: int, y: int):
        """Обрабатывает события от мыши и клавиатуры"""

        logging.info('MP (%d, %d)', x, y)

        if all((self.user_control, self.mode == 'clock', 521 <= x <= 584, 627 <= y <= 665)):
            self.show_answers()

        if all((self.user_control, 970 <= x <= 1020, 99 <= y <= 129)):  # забрать деньги
            self.open_confirm_leave()

        if not self.user_control or not self.has_shown and not self.mode == 'classic':
            return

        if len(self.non_active_answers) == 1:
            # 1 неактивный ответ — после использования «права на ошибку», играем second_final
            # 3 неактивных ответа — после использования 50:50 и «права на ошибку», не играем
            self.player4.setMedia(decorate_audio('sounds/double/second_final.mp3'))
        elif not self.is_x2_now and self.current_question_num not in range(1, 6):
            # после пятого вопроса каждый ответ озвучивается отдельным треком
            self.player4.setMedia(decorate_audio(f'sounds/{self.current_question_num}/final_answer.mp3'))
        elif self.is_x2_now:
            self.player4.setMedia(decorate_audio('sounds/double/first_final.mp3'))

        if 200 <= x <= 538 and 601 <= y <= 642:
            self.choose_answer('A')
        elif 568 <= x <= 915 and 601 <= y <= 642:
            self.choose_answer('B')
        elif 200 <= x <= 538 and 653 <= y <= 693:
            self.choose_answer('C')
        elif 568 <= x <= 915 and 653 <= y <= 693:
            self.choose_answer('D')
        self.scheduler1.start()

        if 766 <= x <= 816 and 99 <= y <= 129:
            self.show_lost_lifeline(self.lost_change)
            self.use_lifeline('change')
        elif 835 <= x <= 885 and 99 <= y <= 129:
            self.show_lost_lifeline(self.lost_5050)
            self.use_lifeline('50:50')
        elif 902 <= x <= 952 and 99 <= y <= 129:
            self.show_lost_lifeline(self.lost_x2)
            if self.lifelines['x2']:
                self.double_dip.show()
                self.double_dip.startFadeInImage()
            self.use_lifeline('x2')

    def update_question_field(self, changer: bool = False):
        """Обновляет текстовые поля вопроса и ответов"""

        self.non_active_answers = []
        text = self.questions[self.current_question_num - 1][int(changer)][0]
        self.answers = list(map(str, self.questions[self.current_question_num - 1][int(changer)][2]))
        self.correct_answer = str(self.questions[self.current_question_num - 1][int(changer)][1])
        # print(self.correct_answer)  # HACK God mode
        self.got_amount = MONEYTREE_AMOUNTS[self.current_question_num - 1]

        self.question.setText(text)
        for i, answer_text_field in enumerate((self.answer_A, self.answer_B, self.answer_C, self.answer_D)):
            answer_text_field.hide()
            answer_text_field.setText(self.answers[i])
        logging.info('Q%d set', self.current_question_num)

    def clear_all_labels(self):
        """Подчищает все слои состояния и текстовые блоки"""

        for state_label in (self.current_state_q, self.current_state_q_2, self.current_state_q_3):
            self.scheduler1.schedule(0, state_label.startFadeOutImage)

        self.scheduler1.schedule(100, lambda: True)
        for state_label in (self.current_state_q, self.current_state_q_2, self.current_state_q_3):
            self.scheduler1.schedule(0, state_label.setPixmap, QPixmap())

        self.scheduler1.schedule(0, self.question.startFadeOut)
        for label in (self.answer_A, self.answer_B, self.answer_C, self.answer_D):
            self.scheduler1.schedule(0, label.startFadeOut)
        self.scheduler1.schedule(100, lambda: True)

        for label in (self.question, self.answer_A, self.answer_B, self.answer_C, self.answer_D):
            self.scheduler1.schedule(0, label.setText, '')

    def show_lost_lifeline(self, ll_button):
        """Показывает анимацию потери подсказки"""
        ll_button.show()
        ll_button.startFadeInImage()

    def choose_answer(self, letter: str):
        """Обрабатывает выбор ответа игроком и запрашивает проверку ответа"""
        if letter in self.non_active_answers:
            return

        self.current_state_q.setPixmap(QPixmap(f'images/question field/chosen_{letter}.png'))
        self.current_state_q.startFadeInImage()
        if self.mode == 'clock':
            self.player2.stop()
            self.qttimer.stop()
        if self.current_question_num not in range(1, 6) or self.is_x2_now:
            self.scheduler1.schedule(0, self.player1.stop)
            if len(self.non_active_answers) != 3:
                self.scheduler1.schedule(0, self.player4.play)
        logging.info(f'Answ[{letter}]')
        letter_to_button = {'A': self.answer_A, 'B': self.answer_B, 'C': self.answer_C, 'D': self.answer_D}

        # для каждого из номеров вопроса выставляем паузу (задаёт интригу)
        delays = (2000 * self.is_x2_now + 400, 2000, 2500, 3000, 3500, 4500, 5500)
        # находим индекс, куда попадает self.current_question_num
        index = bisect_right((1, 5, 6, 10, 11, 13, 15), self.current_question_num) - 1
        delay = delays[index]
        if len(self.non_active_answers) == 3:
            delay = 400
        elif len(self.non_active_answers) == 2 and self.is_x2_now:
            delay = 400
        self.scheduler1.schedule(delay, lambda: True)
        if self.current_question_num == 5:
            self.scheduler1.schedule(0, self.player1.setVolume, 100)

        self.scheduler1.schedule(0, self.check_answer, letter_to_button[letter], letter)
        self.scheduler1.start()

    def check_answer(self, label: AnimationLabel, user_selected_letter: str):
        """Проверяет правильность ответа и запускает соответствующие анимации и звуки"""

        user_answer = label.text()

        num_to_let = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
        correct_answer_letter = num_to_let[self.answers.index(self.correct_answer)]

        n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
        if self.is_x2_now and user_answer != self.correct_answer:  # неправильный ответ с «правом на ошибку»
            self.scheduler1.schedule(
                1500,
                self.current_state_q_3.setPixmap,
                QPixmap(f'images/question field/wrong_{user_selected_letter}.png'),
            )
            self.scheduler1.schedule(0, self.current_state_q_3.startFadeInImage)
            self.scheduler1.schedule(0, self.double_dip.startFadeOutImage)

            self.scheduler1.schedule(0, self.player1.setMedia, decorate_audio('sounds/double/first_wrong.mp3'))
            self.scheduler1.schedule(0, self.player1.play)
            self.scheduler1.schedule(0, self.player4.stop)

            self.non_active_answers.append(user_selected_letter)
            self.is_x2_now = False
            logging.info('Answ incorrect (dd used)')

            self.scheduler1.start()
            return

        elif user_answer != self.correct_answer:  # неправильный ответ без «права на ошибку»
            self.scheduler1.schedule(0, self.player1.setMedia, decorate_audio(f'sounds/{n}/lose.mp3'))
            self.scheduler1.schedule(0, self.player1.play)
            self.scheduler1.schedule(0, self.player2.stop)
            self.scheduler1.schedule(0, self.player4.stop)

            self.show_correct_answer(correct_answer_letter)

            result_game = convert_amount_to_str(SAFETY_NETS[self.current_question_num - 1] + self.saved_seconds_prize)
            self.scheduler1.schedule(1000, lambda: True)
            self.clear_all_labels()
            if self.mode == 'clock':
                empty_timer(self)
                hide_timer(self)
            show_prize(self, result_game)
            self.scheduler1.schedule(750, self.show_game_over, (correct_answer_letter, result_game, self.is_sound))

            sql_request(
                f'INSERT INTO results (name, result, date) VALUES ("{self.name}", "{result_game}", "{self.date}")'
            )

            logging.info('Answ incorrect')
            self.scheduler1.start()
            return

        # правильный ответ без или с «правом на ошибку»
        if self.is_x2_now:
            self.scheduler1.schedule(0, self.double_dip.startFadeOutImage)
        self.scheduler1.schedule(0, self.player2.setMedia, decorate_audio(f'sounds/{n}/correct.mp3'))
        self.scheduler1.schedule(0, self.player2.play)
        self.scheduler1.schedule(0, self.player4.stop)
        logging.info('Answ correct')

        self.seconds_prize += SECONDS_PRICE[n] * self.seconds_left

        self.show_correct_answer(correct_answer_letter)

        if self.current_question_num == 15:  # если ответ на последний вопрос был правильным
            self.scheduler1.schedule(1000, lambda: True)
            self.clear_all_labels()
            if self.mode == 'clock':
                self.saved_seconds_prize += self.seconds_prize
                empty_timer(self)
                hide_timer(self)
            prize = convert_amount_to_str(MONEYTREE_AMOUNTS[self.current_question_num] + self.saved_seconds_prize)
            show_prize(self, prize)
            self.scheduler1.schedule(1000, self.show_win)
            sql_request(f'INSERT INTO results (name, result, date) VALUES ("{self.name}", "{prize}", "{self.date}")')

            self.scheduler1.start()
            return

        if self.current_question_num in (5, 10):
            self.scheduler1.schedule(0, self.player1.stop)
            self.clear_all_labels()
            if self.mode == 'clock':
                self.saved_seconds_prize += self.seconds_prize
                empty_timer(self)
                hide_timer(self)
            prize = convert_amount_to_str(MONEYTREE_AMOUNTS[self.current_question_num] + self.saved_seconds_prize)
            show_prize(self, prize)
            self.scheduler1.schedule(0, self.layout_q.setPixmap, QPixmap('images/sum/amount.png'))
            self.scheduler1.schedule(3700, lambda: True)
            self.scheduler1.schedule(750 + 1000 * (self.current_question_num == 10), self.amount_q.startFadeOut)
            self.player3.setMedia(decorate_audio('sounds/lights_down.mp3'))
            self.scheduler1.schedule(0, self.player3.play)

            for i in range(37, 0, -1):  # анимация показа блока с вопросом и ответами
                self.scheduler1.schedule(30, self.layout_q.setPixmap, QPixmap(f'animations/sum/{i}.png'))
            self.scheduler1.schedule(0, self.layout_q.setPixmap, QPixmap('images/question field/layout.png'))
            logging.info('%d got', self.current_question_num)

        if self.mode == 'classic':
            self.scheduler1.schedule(2000, lambda: True)

        if self.current_question_num in range(1, 5) and (len(self.non_active_answers) in (1, 3) or self.is_x2_now):
            # возвращаем предыдущий трек, если было «право на ошибку» в 1-5 вопросах
            self.scheduler1.schedule(0, self.player1.setMedia, decorate_audio('sounds/1-4/bed.mp3'))
            self.scheduler1.schedule(8, self.player1.play)

        if self.mode == 'clock':
            if self.current_question_num not in range(1, 5):
                self.player3.setMedia(decorate_audio(f'sounds/{self.current_question_num + 1}/before_clock.mp3'))
            else:
                self.player3.setMedia(decorate_audio('sounds/question_show_clock.mp3'))

            delays = (1000, 1350, 2500, 1350, 3500)
            index = bisect_right((1, 5, 6, 10, 11), self.current_question_num) - 1
            self.scheduler1.schedule(delays[index], self.player3.play)
            self.scheduler1.schedule(0, self.player2.stop)

        self.scheduler1.schedule(
            400 * (self.current_question_num not in (5, 10)),
            self.current_state_t.setPixmap,
            QPixmap(f'images/money tree/{self.current_question_num + 1}.png'),
        )
        self.scheduler1.schedule(0, self.clear_all_labels)
        self.scheduler1.schedule(0, self.show_next_question)

        def increase_current_question_number():
            self.current_question_num += 1

        self.scheduler1.schedule(0, increase_current_question_number)

        self.scheduler1.start()

    def show_correct_answer(self, correct_answer_letter: str):
        self.scheduler1.schedule(
            0, self.current_state_q_2.setPixmap, QPixmap(f'images/question field/correct_{correct_answer_letter}.png')
        )
        self.scheduler1.schedule(0, self.current_state_q_2.startFadeInImage)
        self.scheduler1.schedule(0, self.current_state_q_2.show)
        for _ in range(2):
            self.scheduler1.schedule(400, self.current_state_q_2.startFadeOutImage)
            self.scheduler1.schedule(400, self.current_state_q_2.startFadeInImage)
        self.has_shown = False

    def show_next_question(self):
        """Показывает следующий вопрос"""
        if self.mode == 'clock':
            if self.current_question_num == 14:
                empty_timer(self)
            if self.current_question_num not in list(range(1, 6)) + [10]:
                self.scheduler1.schedule(2650 - 500 * (self.current_question_num == 14), lambda: True)
            self.scheduler1.schedule(300, self.update_question_field)

            self.scheduler1.schedule(0, self.question.startFadeIn)
            if self.current_question_num in (5, 10):
                show_timer(self)
            refill_timer(
                self,
                self.current_question_num + 1,
                0 if self.current_question_num in (5, 10, 14) else self.seconds_left,
            )
            self.scheduler1.schedule(0, self.double_dip.setPixmap, QPixmap('images/show-button.png'))
            self.scheduler1.schedule(0, self.double_dip.show)
            self.scheduler1.schedule(0, self.double_dip.startFadeInImage)

        else:
            if self.current_question_num not in range(1, 5):
                # для всех вопросов с 6-го свой бэкграунд-трек
                self.scheduler1.schedule(
                    0, self.player1.setMedia, decorate_audio(f'sounds/{self.current_question_num + 1}/bed.mp3')
                )
                self.scheduler1.schedule(0, self.player1.play)

            if self.current_question_num > 10:
                self.scheduler1.schedule(1000, lambda: True)
            self.scheduler1.schedule(0, self.update_question_field)
            self.scheduler1.schedule(0, self.question.startFadeIn)
            for answer_text_field in (self.answer_A, self.answer_B, self.answer_C, self.answer_D):
                self.scheduler1.schedule(100, answer_text_field.startFadeIn)
                self.scheduler1.schedule(0, answer_text_field.show)
            self.scheduler1.schedule(1000, self.player2.stop)

    def use_lifeline(self, type_ll: str):
        """Активирует подсказку и запускает соответствующие анимации и звуки"""

        if self.lifelines[type_ll]:
            if type_ll == 'change':  # замена вопроса
                self.player3.setMedia(
                    decorate_audio('sounds/change.mp3' if self.mode == 'classic' else 'sounds/change_clock.mp3')
                )
                self.scheduler1.schedule(750, self.player3.play)
                if self.mode == 'clock':
                    if self.current_question_num not in range(1, 5):
                        self.scheduler1.schedule(0, self.player1.stop)
                    self.scheduler1.schedule(0, self.player2.stop)
                    refill_timer(self, self.current_question_num)
                    self.qttimer.stop()
                self.scheduler1.schedule(820 + 1200 * (self.mode == 'clock'), lambda: True)
                for state_label in (self.current_state_q, self.current_state_q_2, self.current_state_q_3):
                    self.scheduler1.schedule(0, state_label.setPixmap, QPixmap())
                self.scheduler1.schedule(0, self.question.startFadeOut)
                for label in (self.answer_A, self.answer_B, self.answer_C, self.answer_D):
                    self.scheduler1.schedule(0, label.startFadeOut)
                if self.is_x2_now:  # на смене вопроса отменяем «право на ошибку»
                    self.scheduler1.schedule(0, self.double_dip.startFadeOutImage)
                self.scheduler1.schedule(200, self.update_question_field, True)
                if self.is_x2_now or len(self.non_active_answers) in (1, 3):
                    n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
                    self.scheduler1.schedule(0, self.player1.setMedia, decorate_audio(f'sounds/{n}/bed.mp3'))
                    self.scheduler1.schedule(8, self.player1.play)
                self.scheduler1.schedule(100, self.question.startFadeIn)
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
                self.is_x2_now = False

            elif type_ll == 'x2':  # право на ошибку
                self.is_x2_now = True
                self.player1.setMedia(
                    decorate_audio(f'sounds/double/start{"_clock" if self.mode == "clock" else ""}.mp3')
                )
                if self.mode == 'clock':
                    self.player2.stop()
                    self.qttimer.stop()
                self.player1.play()

            elif type_ll == '50:50':  # 50:50
                self.player3.setMedia(decorate_audio('sounds/50_50.mp3'))
                self.scheduler1.schedule(0, self.player3.play)
                answs = [self.answer_A, self.answer_B, self.answer_C, self.answer_D]
                answ_letters = ['A', 'B', 'C', 'D']
                if self.non_active_answers:  # неактивные ответы от «права на ошибку»
                    indxs = set([0, 1, 2, 3]) - set([answ_letters.index(self.non_active_answers[0])])
                else:
                    indxs = set([0, 1, 2, 3])
                indxs = list(indxs - set([self.answers.index(self.correct_answer)]))  # вырезаем правильный ответ
                shuffle(indxs)  # убрать два неверных ответа СЛУЧАЙНО
                self.scheduler1.schedule(250, answs[indxs[0]].setText, '')
                self.scheduler1.schedule(0, answs[indxs[1]].setText, '')
                self.non_active_answers += [answ_letters[indxs[0]], answ_letters[indxs[1]]]

            self.lifelines[type_ll] = False
            self.scheduler1.start()
            logging.info(f'- {type_ll}-ll')

    def restart_game(self):
        """Перезапускает игру и возвращает все значения в начальное состояние"""

        self.user_control = True
        self.is_x2_now = False
        self.lifelines = {'change': True, '50:50': True, 'x2': True}
        for ll_button in (self.lost_change, self.lost_x2, self.lost_5050):
            ll_button.hide()
        self.clear_all_labels()
        self.scheduler1.start()
        for player in (self.player1, self.player2, self.player3, self.player4):
            player.stop()
        self.start_game(True)

    def show_win(self):
        """Показывает победы"""

        self.user_control = False
        self.win = WinWindow(self, self.is_sound)
        self.win.move(169 + self.x(), 210 + self.y())
        self.win.show()
        logging.info('Game over - player won')

    def show_game_over(self, state: tuple[str, str, bool]):
        """Показывает окно поражения"""

        self.user_control = False
        self.game_over = GameOverWindow(self, state)
        self.game_over.move(169 + self.x(), 210 + self.y())
        self.game_over.show()
        logging.info('Game over - player lost')

    def open_confirm_leave(self):
        """Показывает форму для подтверждения кнопки «Забрать деньги»"""

        self.user_control = False
        num_to_let = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
        letter = num_to_let[self.answers.index(self.correct_answer)]
        self.confirm_wndw = ConfirmLeaveWindow(self, letter, self.is_sound)
        # и передаём правильный ответ, чтобы показать его после взятия денег
        self.confirm_wndw.move(168 + self.x(), 216 + self.y())
        self.confirm_wndw.show()

    def open_confirm_again(self):
        """Показывает форму для подтверждения перезапуска игры"""

        self.confirm_wndw = ConfirmAgainWindow(self)
        self.confirm_wndw.move(168 + self.x(), 216 + self.y())
        self.confirm_wndw.show()

    def open_confirm_close(self):
        """Показывает форму для подтверждения закрытия игры"""

        self.confirm_wndw = ConfirmCloseWindow()
        self.confirm_wndw.move(168 + self.x(), 216 + self.y())
        self.confirm_wndw.show()

    def open_results_table(self):
        """Показывает таблицу результатов"""

        self.results_table = ResultsTableWindow()
        self.results_table.move(170 + self.x(), 93 + self.y())
        self.results_table.show()
        logging.info('Results table open')

    def open_delete_result_from(self):
        """Показывает форму для удаления одного результата из таблицы результатов"""

        self.delete_form = DeleteResultWindow()
        self.delete_form.move(147 + self.x(), 93 + self.y())
        self.delete_form.show()

    def open_confirm_clear_all(self):
        """Показывает форму для очистки таблицы результатов"""

        self.confirm_wndw = ConfirmClearAll()
        self.confirm_wndw.move(168 + self.x(), 216 + self.y())
        self.confirm_wndw.show()

    def open_about(self):
        """Показывает информацию об игре и разработчике"""

        self.about_wndw = AboutWindow(self, self.is_sound)
        for player in (self.player1, self.player2, self.player4):
            player.setVolume(20 * self.is_sound)
        self.player3.setMedia(decorate_audio('sounds/about.mp3'))
        self.player3.play()
        self.about_wndw.move(178 + self.x(), 175 + self.y())
        self.about_wndw.show()
        logging.info('About open')

    def toggle_sound(self):
        """Переключает звук (т.е. включает или отключает)"""

        if self.sender().isChecked():  # type: ignore | если галочка активна
            self.is_sound = True
        else:
            self.is_sound = False

        for player in (self.player1, self.player2, self.player3, self.player4):
            player.setVolume(100 * self.is_sound)

        if self.current_question_num in range(1, 6) and self.mode == 'clock':
            self.player1.setVolume(30 * self.is_sound)

    def closeEvent(self, event):
        """Завершает работу приложения при закрытии игрового окна"""
        sys.exit(0)
