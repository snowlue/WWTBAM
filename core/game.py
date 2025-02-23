import logging
import sys
from bisect import bisect_right
from datetime import datetime
from random import shuffle

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QKeyEvent, QMouseEvent, QMovie, QPixmap
from PyQt5.QtWidgets import QMainWindow

from core.constants import APP_ICON, MONEY_TREE_AMOUNTS, SAFETY_NETS, SECONDS_FOR_QUESTION, SECONDS_PRICE
from core.dialogs import (
    ConfirmAgainWindow,
    ConfirmClearAll,
    ConfirmCloseWindow,
    ConfirmLeaveWindow,
    GameOverWindow,
    WinWindow,
)
from core.tools import (
    AnimationScheduler,
    LoopingMediaPlayer,
    ask_audience,
    convert_amount_to_str,
    decorate_audio,
    empty_timer,
    get_questions,
    hide_timer,
    refill_timer,
    show_prize,
    show_timer,
    sql_request,
)
from core.widgets import AboutWindow, DeleteResultWindow, ResultsTableWindow
from ui import AnimationLabel, Ui_MainWindow


class GameWindow(QMainWindow, Ui_MainWindow):
    """Окно, отображающее основной игровой контент"""

    def __init__(self, name: str, mode: str):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(APP_ICON)
        self.user_control = False  # реагирует ли игра на действия игрока
        self.name = name
        self.mode = mode

        self.hovered_answer = ''
        self.hovered_lifeline = ''

        self.is_sound = True

        self.player1 = LoopingMediaPlayer(self)  # для bed (6-15 в режиме на время) и неправильных ответов
        self.player2 = LoopingMediaPlayer(self)  # для интро, правильных ответов и часов для 1-5 в режиме на время
        # для lights-down, подсказок 50:50, «Помощь зала» и «Смена вопроса», «О программе»
        # в режиме на время: разморозка таймера и музыка после показа вопроса без ответов
        self.player3 = LoopingMediaPlayer(self)
        self.player4 = LoopingMediaPlayer(self)  # для подсказки x2 и разморозки таймера в «Помощи зала»

        self.scheduler1 = AnimationScheduler(self)
        self.scheduler2 = AnimationScheduler(self)  # для анимации ответов, запасной

        self.new_game.triggered.connect(self.open_confirm_again)
        self.close_game.triggered.connect(self.open_confirm_close)
        self.about.triggered.connect(self.open_about)
        self.open_table.triggered.connect(self.open_results_table)
        self.clear_one.triggered.connect(self.open_delete_result_from)
        self.clear_all.triggered.connect(self.open_confirm_clear_all)
        self.sound_btn.triggered.connect(self.toggle_sound)

        self.restart_game()

    def switch_user_control(self, is_available_to_control: bool):
        """Переключает реагирование игры на действия игрока"""
        self.user_control = is_available_to_control

    def start_game(self, is_repeat: bool = False, is_restarted: bool = False):
        """Запускает анимацию начала игры и показывает первый вопрос"""

        self.questions = get_questions()
        self.current_question_num = 1  # HACK God mode

        logo_and_bg_selector = {i: '1-5' for i in range(1, 6)}
        logo_and_bg_selector.update({i: '6-10' for i in range(6, 11)})
        logo_and_bg_selector.update({i: '11-14' for i in range(11, 15)})
        logo_and_bg_selector[15] = '15'
        current_logo_and_bg = logo_and_bg_selector[self.current_question_num]

        current_background = f'images/backgrounds/{self.bg_num}/{current_logo_and_bg}.jpg'

        if not is_repeat:
            self.scheduler1.schedule(0, self.background_1.setPixmap, QPixmap(current_background))

        date_raw = datetime.today()
        self.date = date_raw.strftime('%d.%m.%Y %H:%M')
        if date_raw.month == 12 and date_raw.day >= 10 or date_raw.month == 1 and date_raw.day <= 20:
            self.layout_t.setPixmap(QPixmap('images/money tree/layout_christmas.png'))

        self.scheduler1.schedule(800, lambda: True)

        if is_repeat:
            self.scheduler1.schedule(0, self.big_logo_1.setPixmap, QPixmap('images/logo/intro.png'))
            self.scheduler1.schedule(0, self.big_logo_2.startFadeOutImage, 200)
            self.scheduler1.schedule(0, self.background_1.setPixmap, QPixmap(current_background))
            self.scheduler1.schedule(0, self.background_2.startFadeOutImage, 200)
        self.scheduler1.schedule(200, self.big_logo_2.setPixmap, QPixmap(f'images/logo/{current_logo_and_bg}.png'))
        self.scheduler1.schedule(200, self.background_2.setPixmap, QPixmap(current_background))

        if self.mode == 'classic':
            self.player2.set_media(decorate_audio('sounds/' + ('new_start.mp3' if is_repeat else 'intro.mp3')))
        else:
            self.player2.set_media(
                decorate_audio('sounds/' + ('new_start_clock.mp3' if is_repeat else 'intro_clock.mp3'))
            )
            if is_repeat:
                self.timer_view.setPixmap(QPixmap())
                self.timer_text.setText('')
                self.central_q.setPixmap(QPixmap('images/question field/double-dip.png'))
        if is_repeat:
            self.central_q.hide()

        if not is_repeat:
            self.scheduler1.schedule(0, self.big_logo_1.show)
            self.scheduler1.schedule(0, self.big_logo_1.startFadeInImage, 1000)
        self.scheduler1.schedule(0, self.player2.play)

        # анимация показа блока с вопросом и ответами
        if is_repeat and not is_restarted:
            self.scheduler1.schedule(0, self.amount_q.setText, '')
            for i in range(37, 0, -1):
                self.scheduler1.schedule(30, self.layout_q.setPixmap, QPixmap(f'animations/sum/{i}.png'))
        elif not is_restarted:
            for i in range(1, 24):
                self.scheduler1.schedule(30, self.layout_q.setPixmap, QPixmap(f'animations/question field/{i}.png'))
        else:
            self.scheduler1.schedule(1000, lambda: True)
        self.scheduler1.schedule(0, self.layout_q.setPixmap, QPixmap('images/question field/layout_noletters.png'))
        self.scheduler1.schedule(600 - 150 * (self.mode == 'clock'), lambda: True)

        for i in range(1, 16):  # анимация денежного дерева
            self.scheduler1.schedule(
                220 + 32 * (self.mode == 'clock') - 27 * is_repeat,
                self.state_t.setPixmap,
                QPixmap(f'images/money tree/{i}.png'),
            )
        if self.mode == 'clock':
            self.scheduler1.schedule(500 * (not is_repeat), lambda: True)
        self.scheduler1.schedule(0, self.state_q_1.startFadeInImage)
        for i in ('A', 'B', 'C', 'D'):  # анимация 4 ответов
            self.scheduler1.schedule(
                450 - 80 * (is_repeat and self.mode == 'clock'),
                self.state_q_1.setPixmap,
                QPixmap(f'animations/chosen answers/chosen_{i}.png'),
            )
            self.scheduler1.schedule(0, self.state_q_1.startFadeInImage)

        self.scheduler1.schedule(450 - 80 * (is_repeat and self.mode == 'clock'), self.state_q_1.setPixmap, QPixmap())
        self.scheduler1.schedule(
            1000 + 600 * (self.mode == 'clock') - 600 * (self.mode == 'clock' and is_repeat),
            self.state_t.setPixmap,
            QPixmap(f'images/money tree/{self.current_question_num}.png'),
        )

        if self.mode == 'classic':
            self.scheduler1.schedule(500, self.update_question_field)
            self.scheduler1.schedule(0, self.question.startFadeIn)
            self.scheduler1.schedule(100, self.show_answers)
            self.scheduler1.schedule(0, self.big_logo_2.show)
            self.scheduler1.schedule(0, self.big_logo_2.startFadeInImage, 1000)

        n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
        self.player1.set_media(decorate_audio(f'sounds/{n}/bed.mp3'))
        self.scheduler1.schedule(500 if self.mode != 'clock' else 0, self.player1.play)
        if not self.is_sound:
            self.scheduler1.schedule(0, self.player1.setVolume, 30 if self.mode == 'clock' else 100)

        if self.mode == 'clock':
            self.player3.set_media(decorate_audio('sounds/question_show_clock.mp3'))
            self.scheduler1.schedule(500, self.player3.play)
            self.scheduler1.schedule(300, self.update_question_field)
            self.scheduler1.schedule(0, self.question.startFadeIn)
            self.scheduler1.schedule(0, self.big_logo_2.show)
            self.scheduler1.schedule(0, self.big_logo_2.startFadeInImage, 1000)
            self.scheduler1.schedule(300, lambda: True)
            show_timer(self)
            refill_timer(self, self.current_question_num)
            self.scheduler1.schedule(0, self.central_q.setPixmap, QPixmap('images/question field/show-button.png'))
            self.scheduler1.schedule(0, self.central_q.show)
            self.scheduler1.schedule(0, self.central_q.startFadeInImage)

        self.scheduler1.start()

        logging.info('Game is OK. Mode: %s. Username: %s', self.mode, self.name)

    def show_answers(self):
        """Анимирует показ возможных ответов на вопрос и запускает таймер в режиме на время"""

        for i, answer_text_field in enumerate((self.answer_A, self.answer_B, self.answer_C, self.answer_D), 1):
            self.scheduler2.schedule(100, answer_text_field.show)
            self.scheduler2.schedule(0, answer_text_field.startFadeIn)
            state_q = self.__getattribute__(f'state_q_{i}')
            self.scheduler2.schedule(0, state_q.setPixmap, QPixmap(f'images/question field/answer{i}.png'))
            self.scheduler2.schedule(-0, state_q.startFadeInImage)
        self.scheduler2.schedule(200, self.layout_q.setPixmap, QPixmap('images/question field/layout.png'))
        for i in range(1, 5):
            state_q = self.__getattribute__(f'state_q_{i}')
            self.scheduler2.schedule(0, state_q.setPixmap, QPixmap())

        if self.mode == 'clock':
            self.has_shown = True
            n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
            self.scheduler2.schedule(0, self.central_q.startFadeOutImage)
            self.scheduler2.schedule(200, self.central_q.setPixmap, QPixmap('images/question field/double-dip.png'))
            self.scheduler2.schedule(0, self.central_q.hide)

            self.qt_timer = QTimer(self)
            # noinspection PyUnresolvedReferences
            self.qt_timer.timeout.connect(self.merge_timer)
            self.qt_timer.start(1000)

            self.seconds_left = SECONDS_FOR_QUESTION[n]

            if n in ('1-4', 5):
                self.player2.set_media(decorate_audio(f'sounds/{n}/clock.mp3'))
                self.scheduler2.schedule(500, self.player2.play)
            else:
                self.player1.set_media(decorate_audio(f'sounds/{n}/bed_clock.mp3'))
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
            self.qt_timer.stop()

            num_to_let = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
            correct_answer_letter = num_to_let[self.answers.index(self.correct_answer)]

            self.scheduler1.schedule(2000 + 1000 * (n == 15), lambda: True)

            self.player3.set_media(decorate_audio(f'sounds/{n}/lose.mp3'))
            self.scheduler1.schedule(0, self.player3.play)
            self.scheduler1.schedule(0, self.player1.stop)
            self.scheduler1.schedule(0, self.player2.stop)

            if self.is_immunity_now:
                self.scheduler1.schedule(0, self.open_confirm_leave, True)
                self.scheduler1.start()
                logging.info("Time's up - leave game, immunity used")
                return

            logging.info("Time's up")
            self.update_and_animate_logo_and_background(None, 'wrong', None, 'wrong')

            # мигалка правильного ответа
            self.show_correct_answer(correct_answer_letter)

            result_amount = convert_amount_to_str(SAFETY_NETS[self.current_question_num - 1] + self.saved_seconds_prize)
            self.scheduler1.schedule(3000, lambda: True)
            self.scheduler1.schedule(0, self.timer_text.setText, '')
            self.clear_all_labels()
            hide_timer(self)
            show_prize(self, result_amount)
            self.scheduler1.schedule(750, self.show_game_over, [correct_answer_letter, result_amount, self.is_sound])

            sql_request(
                f'INSERT INTO results (name, result, date) VALUES ("{self.name}", "{result_amount}", "{self.date}")'
            )
            self.scheduler1.start()
        self.seconds_left -= 1

    def keyPressEvent(self, event: QKeyEvent):
        """Обрабатывает события от клавиатуры"""

        if event.key() < 1500:  # логирование только для клавиш клавиатуры
            logging.info('KP %d', event.key())
        if event.key() in (Qt.Key.Key_Q, 91, 1049, 1061):  # Q, Й, [, Х
            self.response_to_event(200, 601)  # эмулируем выбор ответа A
        if event.key() in (Qt.Key.Key_W, 93, 1062, 1066):  # W, Ц, ], Ъ
            self.response_to_event(568, 601)  # эмулируем выбор ответа В
        if event.key() in (Qt.Key.Key_A, 59, 1060, 1046):  # A, Ф, ;, Ж
            self.response_to_event(200, 653)  # эмулируем выбор ответа С
        if event.key() in (Qt.Key.Key_S, 39, 1067, 1069):  # S, Ы, ', Э
            self.response_to_event(568, 653)  # эмулируем выбор ответа D
        if event.key() == Qt.Key.Key_1:
            self.response_to_event(831, 43)  # эмулируем выбор 50:50
        if event.key() == Qt.Key.Key_2:
            self.response_to_event(892, 43)  # эмулируем выбор «права на ошибку»
        if event.key() == Qt.Key.Key_3:
            self.response_to_event(955, 43)  # эмулируем выбор «помощи зала»
        if event.key() == Qt.Key.Key_4:
            self.response_to_event(1017, 43)  # эмулируем выбор «замены вопроса»
        if event.key() == Qt.Key.Key_5:
            self.response_to_event(831, 77)  # эмулируем выбор «возрождения»
        if event.key() == Qt.Key.Key_6:
            self.response_to_event(892, 77)  # эмулируем выбор «иммунитета»
        if self.mode == 'clock' and event.key() == Qt.Key.Key_7:
            self.response_to_event(955, 77)  # эмулируем выбор «заморозки таймера»
        if event.key() == Qt.Key.Key_8:
            self.response_to_event(1017, 77)  # эмулируем выбор «забрать деньги»
        if event.key() in (Qt.Key.Key_M, 1068):  # M, Ь
            self.is_sound = not self.is_sound  # переключаем звук
            self.sound_btn.setChecked(self.is_sound)
            for p in (self.player1, self.player2, self.player3, self.player4):
                p.setVolume(100 * self.is_sound)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Обрабатывает события от движения мыши"""

        # print(event.x(), event.y(), self.user_control, self.has_shown)  # HACK God mode
        self.response_to_move(event.x(), event.y())  # делегируем обработку события на response_to_move
        return super().mouseMoveEvent(event)

    def response_to_move(self, x: int, y: int):
        if not self.user_control:
            return

        if all((1017 <= x <= 1064, 77 <= y <= 107, self.used_lifelines_count < 4)):
            self.show_selecting_lifeline('home')
            return
        elif not self.has_shown:
            self.show_selecting_lifeline('')

        if not self.has_shown:
            return

        if 200 <= x <= 538 and 601 <= y <= 642 and not self.is_revival_now:
            self.show_selecting_answer('A')
        elif 568 <= x <= 915 and 601 <= y <= 642 and not self.is_revival_now:
            self.show_selecting_answer('B')
        elif 200 <= x <= 538 and 653 <= y <= 693 and not self.is_revival_now:
            self.show_selecting_answer('C')
        elif 568 <= x <= 915 and 653 <= y <= 693 and not self.is_revival_now:
            self.show_selecting_answer('D')
        else:
            self.show_selecting_answer('')

        if self.used_lifelines_count >= 4 and not self.is_revival_now:
            return

        if 831 <= x <= 878 and 43 <= y <= 73 and '50:50' in self.available_to_choose:
            self.show_selecting_lifeline('5050')
        elif 892 <= x <= 939 and 43 <= y <= 73 and 'ata' in self.available_to_choose:
            self.show_selecting_lifeline('ata')
        elif 955 <= x <= 1002 and 43 <= y <= 63 and 'x2' in self.available_to_choose:
            self.show_selecting_lifeline('x2')
        elif 1017 <= x <= 1064 and 43 <= y <= 63 and 'change' in self.available_to_choose:
            self.show_selecting_lifeline('change')
        elif 831 <= x <= 878 and 77 <= y <= 107 and 'revival' in self.available_to_choose:
            self.show_selecting_lifeline('revival')
        elif 892 <= x <= 939 and 77 <= y <= 107 and 'immunity' in self.available_to_choose:
            self.show_selecting_lifeline('immunity')
        elif self.mode == 'clock' and 955 <= x <= 1002 and 77 <= y <= 107 and 'ftc' in self.available_to_choose:
            self.show_selecting_lifeline('ftc')
        else:
            self.show_selecting_lifeline('')

    def show_selecting_lifeline(self, ll_type: str):
        if not ll_type and self.hovered_lifeline:
            self.state_ll.setPixmap(QPixmap())
            self.hovered_lifeline = ''
            return

        if ll_type != self.hovered_lifeline:
            self.state_ll.setPixmap(QPixmap(f'images/money tree/{ll_type}/hover.png'))
            self.state_ll.startFadeInImage()
            self.hovered_lifeline = ll_type

    def show_selecting_answer(self, letter: str):
        if not letter and self.hovered_answer:
            self.state_q_1.setPixmap(QPixmap())
            self.hovered_answer = ''
            return

        if letter != self.hovered_answer and letter not in self.non_active_answers:
            self.state_q_1.setPixmap(QPixmap(f'images/question field/chosen_{letter}.png'))
            self.state_q_1.startFadeInImage()
            self.hovered_answer = letter

    def mousePressEvent(self, event: QMouseEvent):
        """Обрабатывает события от нажатий кнопок мыши"""

        self.response_to_event(event.x(), event.y())  # делегируем обработку события на response_to_event
        return super().mousePressEvent(event)

    def response_to_event(self, x: int, y: int):
        """Обрабатывает события от мыши и клавиатуры"""

        logging.info('MP (%d, %d)', x, y)

        if all((self.user_control, self.mode == 'clock', 521 <= x <= 584, 627 <= y <= 665)):
            self.show_answers()

        if all((self.user_control, 1017 <= x <= 1064, 77 <= y <= 107, self.used_lifelines_count < 4)):
            self.open_confirm_leave()

        if not self.user_control or not self.has_shown and self.mode == 'clock':
            return

        if len(self.non_active_answers) == 1:
            # 1 неактивный ответ — после использования «права на ошибку», играем second_final
            # 3 неактивных ответа — после использования 50:50 и «права на ошибку», не играем
            self.player4.set_media(decorate_audio('sounds/double/second_final.mp3'))
        elif not self.is_x2_now and self.current_question_num not in range(1, 6):
            # после пятого вопроса каждый ответ озвучивается отдельным треком
            self.player4.set_media(decorate_audio(f'sounds/{self.current_question_num}/final_answer.mp3'))
        elif self.is_x2_now:
            self.player4.set_media(decorate_audio('sounds/double/first_final.mp3'))

        if 200 <= x <= 538 and 601 <= y <= 642 and not self.is_revival_now:
            self.choose_answer('A')
        elif 568 <= x <= 915 and 601 <= y <= 642 and not self.is_revival_now:
            self.choose_answer('B')
        elif 200 <= x <= 538 and 653 <= y <= 693 and not self.is_revival_now:
            self.choose_answer('C')
        elif 568 <= x <= 915 and 653 <= y <= 693 and not self.is_revival_now:
            self.choose_answer('D')
        self.scheduler1.start()

        if self.used_lifelines_count >= 4 and not self.is_revival_now:
            return

        if 831 <= x <= 878 and 43 <= y <= 73 and '50:50' in self.available_to_choose:
            self.use_lifeline('50:50')
        elif 892 <= x <= 939 and 43 <= y <= 73 and 'ata' in self.available_to_choose:
            self.use_lifeline('ata')
        elif 955 <= x <= 1002 and 43 <= y <= 73 and 'x2' in self.available_to_choose:
            self.use_lifeline('x2')
        elif 1017 <= x <= 1064 and 43 <= y <= 73 and 'change' in self.available_to_choose:
            self.use_lifeline('change')
        elif 831 <= x <= 878 and 77 <= y <= 107 and 'revival' in self.available_to_choose:
            self.use_lifeline('revival')
        elif 892 <= x <= 939 and 77 <= y <= 107 and 'immunity' in self.available_to_choose:
            self.use_lifeline('immunity')
        elif self.mode == 'clock' and 955 <= x <= 1002 and 77 <= y <= 107 and 'ftc' in self.available_to_choose:
            self.use_lifeline('ftc')

    def update_question_field(self, changer: int = 0):
        """Обновляет текстовые поля вопроса и ответов"""

        self.non_active_answers = []
        text = self.questions[self.current_question_num - 1][changer][0]
        self.answers = list(map(str, self.questions[self.current_question_num - 1][changer][2]))
        self.correct_answer = str(self.questions[self.current_question_num - 1][changer][1])
        # print(self.correct_answer)  # HACK God mode
        self.got_amount = MONEY_TREE_AMOUNTS[self.current_question_num - 1]

        self.question.setText(text)
        for i, answer_text_field in enumerate((self.answer_A, self.answer_B, self.answer_C, self.answer_D)):
            answer_text_field.hide()
            answer_text_field.setText(self.answers[i])
        logging.info('Q%d set', self.current_question_num)

    def clear_question_field(self, is_for_question: bool = True):
        """Задаёт пустые pixmap'ы и делает фейд-аут текстовых блоков"""
        for state_label in (self.state_q_1, self.state_q_2, self.state_q_3):
            self.scheduler1.schedule(0, state_label.setPixmap, QPixmap())

        self.scheduler1.schedule(0, self.question.startFadeOut)
        for label in (self.answer_A, self.answer_B, self.answer_C, self.answer_D):
            self.scheduler1.schedule(0, label.startFadeOut)
        if is_for_question:
            self.scheduler1.schedule(0, self.state_q_1.setPixmap, QPixmap('images/question field/layout_noletters.png'))
        self.scheduler1.schedule(0, self.state_q_1.startFadeInImage, 100)
        self.scheduler1.schedule(100, self.state_q_1.setPixmap, QPixmap())
        if is_for_question:
            self.scheduler1.schedule(0, self.layout_q.setPixmap, QPixmap('images/question field/layout_noletters.png'))

    def clear_ata_field(self):
        for ata_label in (self.ata_a_percents, self.ata_b_percents, self.ata_c_percents, self.ata_d_percents):
            self.scheduler1.schedule(0, ata_label.startFadeOut)
        for ata_label in (self.ata_a_score, self.ata_b_score, self.ata_c_score, self.ata_d_score):
            self.scheduler1.schedule(0, ata_label.hide)
        self.scheduler1.schedule(0, self.ata_layout.startFadeOutImage)

    def clear_all_labels(self, is_for_question: bool = True):
        """Подчищает все слои состояния и текстовые блоки"""

        for state_label in (self.state_q_1, self.state_q_2, self.state_q_3):
            self.scheduler1.schedule(0, state_label.startFadeOutImage)

        if self.is_ata_now:
            self.clear_ata_field()
            self.is_ata_now = False

        self.scheduler1.schedule(100, lambda: True)
        self.clear_question_field(is_for_question)
        self.scheduler1.schedule(100, lambda: True)

        for label in (self.question, self.answer_A, self.answer_B, self.answer_C, self.answer_D):
            self.scheduler1.schedule(0, label.setText, '')

    @staticmethod
    def show_lost_lifeline(ll_button):
        """Показывает анимацию потери подсказки"""
        ll_button.show()
        ll_button.startFadeInImage()

    def update_and_animate_logo_and_background(
        self, prev_logo: str | None, logo: str, prev_bg: str | None, bg: str, slow_mode: bool = False
    ):
        """Обновляет фон и логотип с анимацией"""
        # обновляем логотип
        if prev_logo:
            self.scheduler1.schedule(0, self.big_logo_1.setPixmap, QPixmap(f'images/logo/{prev_logo}.png'))
        else:
            self.scheduler1.schedule(0, self.big_logo_1.setPixmap, self.big_logo_2.pixmap().copy())
        self.scheduler1.schedule(0, self.big_logo_2.setPixmap, QPixmap(f'images/logo/{logo}.png'))
        self.scheduler1.schedule(0, self.big_logo_2.show)
        self.scheduler1.schedule(0, self.big_logo_2.startFadeInImage, 1000 + 4000 * slow_mode)
        # обновляем фон

        if prev_bg:
            self.scheduler1.schedule(
                0, self.background_1.setPixmap, QPixmap(f'images/backgrounds/{self.bg_num}/{prev_bg}.jpg')
            )
        else:
            self.scheduler1.schedule(0, self.background_1.setPixmap, self.background_2.pixmap().copy())
        self.scheduler1.schedule(0, self.background_2.setPixmap, QPixmap(f'images/backgrounds/{self.bg_num}/{bg}.jpg'))
        self.scheduler1.schedule(0, self.background_2.show)
        self.scheduler1.schedule(0, self.background_2.startFadeInImage, 1000 + 4000 * slow_mode)

    def hide_timer_and_show_prize(self):
        """Опустошает и скрывает таймер, а затем показывает текущий выигрыш"""
        self.clear_all_labels()
        if self.mode == 'clock':
            self.saved_seconds_prize += self.seconds_prize
            empty_timer(self)
            hide_timer(self)
        prize = convert_amount_to_str(MONEY_TREE_AMOUNTS[self.current_question_num] + self.saved_seconds_prize)
        show_prize(self, prize)

    def choose_answer(self, letter: str):
        """Обрабатывает выбор ответа игроком и запрашивает проверку ответа"""
        if letter in self.non_active_answers:
            return

        self.state_q_1.setPixmap(QPixmap(f'images/question field/chosen_{letter}.png'))
        self.state_q_1.startFadeInImage()
        if self.mode == 'clock':
            self.player2.pause()
            self.qt_timer.stop()
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
        if len(self.non_active_answers) == 3 or len(self.non_active_answers) == 2 and self.is_x2_now:
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

        self.available_to_choose = list(self.lifelines.keys())
        if not self.revival_activated or self.is_x2_now:
            self.available_to_choose.remove('revival')

        n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
        if self.is_x2_now and user_answer != self.correct_answer:  # неправильный ответ с «правом на ошибку»
            self.scheduler1.schedule(
                1500,
                self.state_q_3.setPixmap,
                QPixmap(f'images/question field/wrong_{user_selected_letter}.png'),
            )
            self.scheduler1.schedule(0, self.central_q.startFadeOutImage)
            self.scheduler1.schedule(0, self.state_q_3.startFadeInImage)

            if self.is_immunity_now:
                self.scheduler1.schedule(0, self.central_q.setPixmap, QPixmap('images/question field/immunity.png'))
                self.scheduler1.schedule(0, self.central_q.startFadeInImage)

            self.scheduler1.schedule(0, self.player1.set_media, decorate_audio('sounds/double/first_wrong.mp3'))
            self.scheduler1.schedule(0, self.player1.play)
            self.scheduler1.schedule(0, self.player4.stop)

            self.non_active_answers.append(user_selected_letter)
            self.is_x2_now = False

            if self.mode == 'clock':
                self.scheduler1.schedule(3000, self.player3.set_media, decorate_audio('sounds/timer_unfreeze.mp3'))
                self.scheduler1.schedule(0, self.player3.play)
                if self.current_question_num in range(1, 6):
                    self.scheduler1.schedule(0, self.player1.set_media, decorate_audio('sounds/1-4/bed.mp3'))
                    self.scheduler1.schedule(8, self.player1.play)
                    self.scheduler1.schedule(0, self.player2.play)
                else:
                    self.scheduler1.schedule(0, self.player1.set_media, decorate_audio(f'sounds/{n}/bed_clock.mp3'))
                    self.scheduler1.schedule(0, self.player1.setPosition, self.player_seconds_position)
                    self.scheduler1.schedule(0, self.player1.play)
                self.scheduler1.schedule(0, self.qt_timer.start)
                if self.used_lifelines_count < 4:
                    self.scheduler1.schedule(0, self.gray_ftc.startFadeOutImage)
                    self.available_to_choose.append('ftc')

            logging.info('Answ incorrect (dd used)')
            self.scheduler1.start()
            return

        elif user_answer != self.correct_answer:  # неправильный ответ без «права на ошибку»
            self.scheduler1.schedule(0, self.player1.set_media, decorate_audio(f'sounds/{n}/lose.mp3'))
            self.scheduler1.schedule(0, self.player1.play)
            self.scheduler1.schedule(0, self.player2.stop)
            self.scheduler1.schedule(0, self.player4.stop)

            if self.is_immunity_now:
                self.scheduler1.schedule(0, self.open_confirm_leave, True)
                self.scheduler1.start()
                logging.info('Answ incorrect - leave game, immunity used')
                return

            self.update_and_animate_logo_and_background(None, 'wrong', None, 'wrong')
            self.show_correct_answer(correct_answer_letter)

            result_amount = convert_amount_to_str(SAFETY_NETS[self.current_question_num - 1] + self.saved_seconds_prize)

            self.scheduler1.schedule(1000, lambda: True)
            self.clear_all_labels()
            if self.mode == 'clock':
                empty_timer(self)
                hide_timer(self)
            show_prize(self, result_amount)
            self.scheduler1.schedule(750, self.show_game_over, (correct_answer_letter, result_amount, self.is_sound))

            sql_request(
                f'INSERT INTO results (name, result, date) VALUES ("{self.name}", "{result_amount}", "{self.date}")'
            )

            logging.info('Answ incorrect')
            self.scheduler1.start()
            return

        # правильный ответ без или с «правом на ошибку»
        if (len(self.non_active_answers) in (1, 3) or self.is_x2_now) and self.used_lifelines_count < 4:
            if self.mode == 'clock':
                self.scheduler1.schedule(0, self.gray_ftc.startFadeOutImage)
                self.available_to_choose.append('ftc')
            self.scheduler1.schedule(0, self.gray_revival.startFadeOutImage)
            self.available_to_choose.append('revival')

        if self.is_x2_now or self.is_immunity_now:
            self.scheduler1.schedule(0, self.central_q.startFadeOutImage)
        self.scheduler1.schedule(0, self.player2.set_media, decorate_audio(f'sounds/{n}/correct.mp3'))
        self.scheduler1.schedule(0, self.player2.play)
        self.scheduler1.schedule(0, self.player4.stop)
        logging.info('Answ correct')

        self.is_x2_now = False
        self.is_ata_now = False
        self.is_immunity_now = False

        self.seconds_prize += SECONDS_PRICE[n] * self.seconds_left

        self.show_correct_answer(correct_answer_letter)

        if self.current_question_num == 15:  # если ответ на последний вопрос был правильным
            self.update_and_animate_logo_and_background('15', 'millionaire', '15', '1-5')

            self.scheduler1.schedule(1000, lambda: True)
            self.hide_timer_and_show_prize()
            self.scheduler1.schedule(1000, self.show_win)

            prize = convert_amount_to_str(MONEY_TREE_AMOUNTS[self.current_question_num] + self.saved_seconds_prize)
            sql_request(f'INSERT INTO results (name, result, date) VALUES ("{self.name}", "{prize}", "{self.date}")')

            self.scheduler1.start()
            return

        if self.current_question_num in (5, 10):
            if self.mode == 'classic':
                prev = {5: '1-5', 10: '6-10'}.get(self.current_question_num)
                self.update_and_animate_logo_and_background(prev, 'intro', prev, '1-5')

            self.scheduler1.schedule(0, self.player1.stop)
            self.hide_timer_and_show_prize()
            self.scheduler1.schedule(0, self.layout_q.setPixmap, QPixmap('images/sum/amount.png'))
            self.scheduler1.schedule(3700, lambda: True)
            self.scheduler1.schedule(750 + 1000 * (self.current_question_num == 10), self.amount_q.startFadeOut)
            self.player3.set_media(decorate_audio('sounds/lights_down.mp3'))
            self.scheduler1.schedule(0, self.player3.play)

            for i in range(37, 0, -1):  # анимация показа блока с вопросом и ответами
                self.scheduler1.schedule(30, self.layout_q.setPixmap, QPixmap(f'animations/sum/{i}.png'))
            self.scheduler1.schedule(0, self.layout_q.setPixmap, QPixmap('images/question field/layout.png'))

            logging.info('%d got', self.current_question_num)

        new_num = {5: '6-10', 10: '11-14', 14: '15'}.get(self.current_question_num)
        if new_num and self.mode == 'classic':
            self.scheduler1.schedule(2000 * (new_num == '15'), lambda: True)
            self.update_and_animate_logo_and_background(
                '11-14' if new_num == '15' else 'intro',
                new_num,
                '11-14' if new_num == '15' else '1-5',
                new_num,
                new_num == '15',
            )
            self.scheduler1.schedule(2000 * (new_num != '15'), lambda: True)
        elif self.mode == 'classic':
            self.scheduler1.schedule(2000, lambda: True)

        if self.current_question_num in range(1, 5) and (len(self.non_active_answers) in (1, 3) or self.is_x2_now):
            # возвращаем предыдущий трек, если было «право на ошибку» в 1-5 вопросах
            self.scheduler1.schedule(0, self.player1.set_media, decorate_audio('sounds/1-4/bed.mp3'))
            self.scheduler1.schedule(8, self.player1.play)

        if self.mode == 'clock':
            if self.current_question_num not in range(1, 5):
                self.player3.set_media(decorate_audio(f'sounds/{self.current_question_num + 1}/before_clock.mp3'))
            else:
                self.player3.set_media(decorate_audio('sounds/question_show_clock.mp3'))

            new_num = {5: '6-10', 10: '11-14', 14: '15'}.get(self.current_question_num)
            if new_num:
                self.update_and_animate_logo_and_background(
                    '11-14' if new_num == '15' else 'intro',
                    new_num,
                    '11-14' if new_num == '15' else '1-5',
                    new_num,
                    new_num == '15',
                )

            delays = (1000, 1350, 2500, 1350, 3500)
            index = bisect_right((1, 5, 6, 10, 11), self.current_question_num) - 1
            self.scheduler1.schedule(delays[index], self.player3.play)
            self.scheduler1.schedule(0, self.player2.stop)

        self.scheduler1.schedule(
            400 * (self.current_question_num not in (5, 10)),
            self.state_t.setPixmap,
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
            0, self.state_q_2.setPixmap, QPixmap(f'images/question field/correct_{correct_answer_letter}.png')
        )
        self.scheduler1.schedule(0, self.state_q_2.startFadeInImage)
        self.scheduler1.schedule(0, self.state_q_2.show)
        for _ in range(2):
            self.scheduler1.schedule(400, self.state_q_2.startFadeOutImage)
            self.scheduler1.schedule(400, self.state_q_2.startFadeInImage)
        if self.mode == 'clock':
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
            self.scheduler1.schedule(0, self.central_q.setPixmap, QPixmap('images/question field/show-button.png'))
            self.scheduler1.schedule(0, self.central_q.show)
            self.scheduler1.schedule(0, self.central_q.startFadeInImage)
            return

        if self.current_question_num not in range(1, 5):
            # для всех вопросов с 6-го свой бэкграунд-трек
            self.scheduler1.schedule(
                0, self.player1.set_media, decorate_audio(f'sounds/{self.current_question_num + 1}/bed.mp3')
            )
            self.scheduler1.schedule(0, self.player1.play)

        if self.current_question_num > 10:
            self.scheduler1.schedule(1000, lambda: True)
        self.scheduler1.schedule(0, self.update_question_field)
        self.scheduler1.schedule(0, self.question.startFadeIn)
        self.scheduler1.schedule(0, self.show_answers)
        self.scheduler1.schedule(1000, self.player2.stop)

        if 1 <= self.used_lifelines_count < 4 and not self.revival_activated:
            self.gray_revival.startFadeOutImage()
            self.available_to_choose.append('revival')
            self.revival_activated = True

    def use_lifeline(self, type_ll: str):
        """Активирует подсказку и запускает соответствующие анимации и звуки"""

        if not self.lifelines[type_ll] and not self.is_revival_now:
            return

        if not self.is_revival_now:
            self.used_lifelines_count += 1

        state_lifelines = False

        if type_ll == 'change':  # замена вопроса
            self.show_lost_lifeline(self.lost_change)
            self.player3.set_media(
                decorate_audio('sounds/' + ('change.mp3' if self.mode == 'classic' else 'change_clock.mp3'))
            )
            self.scheduler1.schedule(750, self.player3.play)
            if self.mode == 'clock':
                if self.current_question_num not in range(1, 6):
                    self.scheduler1.schedule(0, self.player1.stop)
                self.scheduler1.schedule(0, self.player2.stop)
                refill_timer(self, self.current_question_num)
                self.qt_timer.stop()
            self.scheduler1.schedule(820 + 1200 * (self.mode == 'clock'), lambda: True)
            self.clear_question_field()
            if self.is_x2_now:  # на смене вопроса отменяем «право на ошибку»
                self.scheduler1.schedule(0, self.central_q.startFadeOutImage)
            if self.is_ata_now:
                self.clear_ata_field()
            self.scheduler1.schedule(200, self.update_question_field, 1 + int(self.is_revival_now))
            if self.is_x2_now or len(self.non_active_answers) in (1, 3):
                n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
                self.scheduler1.schedule(0, self.player1.set_media, decorate_audio(f'sounds/{n}/bed.mp3'))
                self.scheduler1.schedule(8, self.player1.play)
            self.scheduler1.schedule(100, self.question.startFadeIn)
            if self.mode == 'classic':
                self.scheduler1.schedule(0, self.show_answers)
            else:
                self.scheduler1.schedule(0, self.central_q.setPixmap, QPixmap('images/question field/show-button.png'))
                self.scheduler1.schedule(0, self.central_q.show)  # подменяем кнопку по центру на кнопку показа ответа
                self.scheduler1.schedule(0, self.central_q.startFadeInImage)
                if self.mode == 'clock':
                    self.has_shown = False
            self.is_x2_now = False
            self.is_ata_now = False
            self.is_immunity_now = False

        elif type_ll == 'x2':  # право на ошибку
            self.show_lost_lifeline(self.lost_x2)
            self.central_q.setPixmap(QPixmap('images/question field/double-dip.png'))
            self.central_q.show()
            self.central_q.startFadeInImage()
            self.is_x2_now = True
            if self.mode == 'clock' and self.current_question_num not in range(1, 6):
                self.player_seconds_position = self.player1.position()
            self.player1.set_media(decorate_audio(f'sounds/double/start{"_clock" * (self.mode == "clock")}.mp3'))
            if self.mode == 'clock':
                self.player2.pause()
                self.qt_timer.stop()
            self.player1.play()

            if 'revival' in self.available_to_choose:
                self.available_to_choose.remove('revival')
                self.gray_revival.show()
                self.gray_revival.startFadeInImage()
            if self.mode == 'clock':
                self.available_to_choose.remove('ftc')
                self.gray_ftc.show()
                self.gray_ftc.startFadeInImage()
            state_lifelines = True

        elif type_ll == '50:50':  # 50:50
            self.show_lost_lifeline(self.lost_5050)
            self.player3.set_media(decorate_audio('sounds/50_50.mp3'))
            self.scheduler1.schedule(0, self.player3.play)
            answers = [self.answer_A, self.answer_B, self.answer_C, self.answer_D]
            answers_letters = ['A', 'B', 'C', 'D']
            if self.non_active_answers:  # неактивные ответы от «права на ошибку»
                indexes = {0, 1, 2, 3} - {answers_letters.index(self.non_active_answers[0])}
            else:
                indexes = {0, 1, 2, 3}
            indexes = list(indexes - {self.answers.index(self.correct_answer)})  # вырезаем правильный ответ
            shuffle(indexes)  # убрать два неверных ответа СЛУЧАЙНО
            self.scheduler1.schedule(250, answers[indexes[0]].setText, '')
            self.scheduler1.schedule(0, answers[indexes[1]].setText, '')
            self.non_active_answers += [answers_letters[indexes[0]], answers_letters[indexes[1]]]
            state_lifelines = True

        elif type_ll == 'ata':  # помощь зала
            self.show_lost_lifeline(self.lost_ata)
            for score_label, percents_label in zip(
                (self.ata_a_score, self.ata_b_score, self.ata_c_score, self.ata_d_score),
                (self.ata_a_percents, self.ata_b_percents, self.ata_c_percents, self.ata_d_percents),
            ):
                score_label.hide()
                percents_label.setText('')
            if self.mode == 'clock':
                if self.current_question_num in range(1, 6):
                    self.scheduler1.schedule(0, self.player2.pause)
                self.scheduler1.schedule(0, self.qt_timer.stop)
            self.scheduler1.schedule(0, self.player1.pause)
            self.player3.set_media(decorate_audio(f'sounds/ata{"_clock" * (self.mode == "clock")}.mp3'))
            correct_percent, other_percents = ask_audience(self.current_question_num, 4 - len(self.non_active_answers))
            self.scheduler1.schedule(0, self.player3.play)
            self.scheduler1.schedule(0, self.ata_layout.show)
            self.scheduler1.schedule(0, self.ata_layout.startFadeInImage)
            gif = QMovie('images/ata.gif')
            self.scheduler1.schedule(4200, self.ata_layout.setMovie, gif)
            self.scheduler1.schedule(0, gif.start)
            self.scheduler1.schedule(7500, self.ata_layout.setPixmap, QPixmap('images/ata.png'))

            correct_answer_letter = ['A', 'B', 'C', 'D'][self.answers.index(self.correct_answer)]
            other_score_labels = []
            other_percents_labels = []
            for score_label, percents_label in zip(
                (self.ata_a_score, self.ata_b_score, self.ata_c_score, self.ata_d_score),
                (self.ata_a_percents, self.ata_b_percents, self.ata_c_percents, self.ata_d_percents),
            ):
                self.scheduler1.schedule(0, score_label.setFixedHeight, 0)
                self.scheduler1.schedule(0, score_label.show)

                self.scheduler1.schedule(0, percents_label.setText, '0%')

                letter = score_label.objectName().split('_')[1].upper()
                if letter == correct_answer_letter:
                    correct_score_label = score_label
                    self.scheduler1.schedule(0, percents_label.setText, f'{correct_percent}%')
                elif letter not in self.non_active_answers:
                    other_score_labels.append(score_label)
                    other_percents_labels.append(percents_label)

            for j, percent in enumerate(other_percents):
                self.scheduler1.schedule(0, other_percents_labels[j].setText, f'{percent}%')
            for percents_label in (self.ata_a_percents, self.ata_b_percents, self.ata_c_percents, self.ata_d_percents):
                self.scheduler1.schedule(0, percents_label.startFadeIn)

            for i in range(0, 100):
                current_step = int(180 / 100 * i // 1)
                if i <= correct_percent:
                    # noinspection PyUnboundLocalVariable
                    self.scheduler1.schedule(10, correct_score_label.setFixedHeight, current_step)
                for j, percent in enumerate(other_percents):
                    if i <= percent:
                        self.scheduler1.schedule(0, other_score_labels[j].setFixedHeight, current_step)

            self.scheduler1.schedule(0, self.player1.play)
            if self.mode == 'clock':
                self.scheduler1.schedule(0, self.player4.setMedia, decorate_audio('sounds/timer_unfreeze.mp3'))
                self.scheduler1.schedule(0, self.player4.play)
                if self.current_question_num in range(1, 6):
                    self.scheduler1.schedule(0, self.player2.play)
                self.scheduler1.schedule(0, self.qt_timer.start)
            self.is_ata_now = True

        elif type_ll == 'revival':  # возрождение
            self.show_lost_lifeline(self.lost_revival)
            self.player3.setMedia(decorate_audio('sounds/revival.mp3'))
            self.player3.play()

            self.central_q.setPixmap(QPixmap('images/question field/revival.png'))
            self.central_q.show()
            self.central_q.startFadeInImage()

            self.state_q_1.setPixmap(QPixmap('images/question field/all_wrong.png'))
            self.state_q_1.startFadeInImage()

            for lost_label in (self.lost_5050, self.lost_ata, self.lost_change, self.lost_ftc):
                lost_label.startFadeOutImage()
            self.is_revival_now = True
            self.available_to_choose = list(self.lifelines.keys())

            if len(self.non_active_answers) >= 2:
                self.available_to_choose.remove('50:50')
                self.gray_5050.show()
                self.gray_5050.startFadeInImage()
            for ll in self.lifelines:
                if self.lifelines[ll]:
                    self.available_to_choose.remove(ll)
            if self.is_x2_now:
                self.available_to_choose.remove('x2')
            else:
                self.lost_x2.startFadeOutImage()
            if self.is_immunity_now:
                self.available_to_choose.remove('immunity')
            else:
                self.lost_immunity.startFadeOutImage()

            self.lifelines['revival'] = False
            self.scheduler1.start()
            logging.info(f'- {type_ll}-ll')
            return

        elif type_ll == 'immunity':  # иммунитет
            if self.mode == 'clock':
                player = self.player2 if self.current_question_num in range(1, 6) else self.player1
                self.scheduler1.schedule(0, player.pause)
                self.scheduler1.schedule(0, self.qt_timer.stop)

            self.show_lost_lifeline(self.lost_immunity)
            self.player3.setMedia(decorate_audio('sounds/immunity.mp3'))
            self.player3.play()
            self.scheduler1.schedule(1700, self.central_q.setPixmap, QPixmap('images/question field/immunity.png'))
            self.scheduler1.schedule(0, self.central_q.show)
            self.scheduler1.schedule(0, self.central_q.startFadeInImage)
            if self.is_x2_now:
                self.scheduler1.schedule(
                    2000, self.central_q.setPixmap, QPixmap('images/question field/double-dip.png')
                )
                self.scheduler1.schedule(0, self.central_q.startFadeInImage)

            if self.mode == 'clock':
                # noinspection PyUnboundLocalVariable
                self.scheduler1.schedule(0, player.play)
                self.scheduler1.schedule(0, self.qt_timer.start)

            self.is_immunity_now = True
            state_lifelines = True

        elif type_ll == 'ftc':  # заморозка времени
            self.show_lost_lifeline(self.lost_ftc)
            self.player3.setMedia(decorate_audio('sounds/timer_freeze.mp3'))
            self.player3.play()
            self.qt_timer.stop()
            self.player2.stop()
            n = '1-4' if self.current_question_num in range(1, 5) else self.current_question_num
            self.player1.setMedia(decorate_audio(f'sounds/{n}/bed.mp3'))
            self.player1.play()
            state_lifelines = True

        if self.is_revival_now:
            for ll in self.lifelines:
                lifeline = ll.replace(':', '')
                if not self.lifelines[ll] and ll != 'revival':
                    self.__getattribute__(f'lost_{lifeline}').startFadeInImage()

            self.available_to_choose = list(self.lifelines.keys())

            if not self.is_x2_now and not self.is_immunity_now:
                self.central_q.startFadeOutImage()
            self.state_q_1.startFadeOutImage()
            self.is_revival_now = False

        if self.used_lifelines_count >= 4:
            for label in (
                self.gray_5050,
                self.gray_ata,
                self.gray_x2,
                self.gray_change,
                self.gray_revival,
                self.gray_immunity,
                self.gray_ftc,
                self.gray_home,
            ):
                label.show()
                label.startFadeInImage()

        self.lifelines[type_ll] = False

        if self.used_lifelines_count >= 1 and not state_lifelines and not self.revival_activated:
            self.gray_revival.startFadeOutImage()
            self.available_to_choose.append('revival')
            self.revival_activated = True

        self.scheduler1.start()
        logging.info(f'- {type_ll}-ll')

    def restart_game(self, is_repeat: bool = False, is_restarted: bool = False):
        """Перезапускает игру и возвращает все значения в начальное состояние"""

        self.has_shown = True if self.mode == 'classic' else False
        self.seconds_left = 0
        self.seconds_prize = 0  # приз за сэкономленные секунды в режиме игры на время
        self.saved_seconds_prize = 0  # приз за секунды сохраняется из seconds_prize после 5 и 10 вопросов

        self.is_x2_now = False
        self.is_ata_now = False
        self.is_revival_now = False
        self.revival_activated = False
        self.is_immunity_now = False
        self.non_active_answers = []
        self.lifelines = {
            'change': True,
            '50:50': True,
            'x2': True,
            'ata': True,
            'revival': True,
            'ftc': self.mode == 'clock',
            'immunity': True,
        }
        self.available_to_choose = ['change', '50:50', 'x2', 'ata', 'ftc', 'immunity']
        self.used_lifelines_count = 0

        for player in (self.player1, self.player2, self.player3, self.player4):
            player.stop()

        for label in (
            self.lost_5050,
            self.lost_ata,
            self.lost_x2,
            self.lost_change,
            self.lost_revival,
            self.lost_immunity,
            self.lost_ftc,
            self.gray_5050,
            self.gray_ata,
            self.gray_x2,
            self.gray_change,
            self.gray_immunity,
            self.gray_ftc,
            self.gray_home,
        ):
            label.hide()

        if self.mode == 'classic':
            self.gray_ftc.show()
        self.gray_revival.show()
        self.central_q.hide()
        self.clear_all_labels(is_repeat and is_restarted)
        self.scheduler1.start()
        self.start_game(is_repeat, is_restarted)

    def show_win(self):
        """Показывает окно победы"""

        self.user_control = False
        self.win = WinWindow(self, self.is_sound)
        self.win.move(201 + self.x(), 210 + self.y())
        self.win.show()
        logging.info('Game over - player won')

    def show_game_over(self, state: tuple[str, str, bool]):
        """Показывает окно поражения"""

        self.user_control = False
        self.game_over = GameOverWindow(self, state)
        self.game_over.move(201 + self.x(), 210 + self.y())
        self.game_over.show()
        logging.info('Game over - player lost')

    def open_confirm_leave(self, trigger_leaving: bool = False):
        """Показывает форму для подтверждения кнопки «Забрать деньги»"""

        self.user_control = False
        num_to_let = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
        letter = num_to_let[self.answers.index(self.correct_answer)]
        self.confirm_window = ConfirmLeaveWindow(self, letter, self.is_sound)
        # и передаём правильный ответ, чтобы показать его после взятия денег
        self.confirm_window.move(200 + self.x(), 216 + self.y())
        if trigger_leaving:
            self.confirm_window.leave(True)
            return
        self.confirm_window.show()

    def open_confirm_again(self):
        """Показывает форму для подтверждения перезапуска игры"""

        self.confirm_window = ConfirmAgainWindow(self)
        self.confirm_window.move(200 + self.x(), 216 + self.y())
        self.confirm_window.show()

    def open_confirm_close(self):
        """Показывает форму для подтверждения закрытия игры"""

        self.confirm_window = ConfirmCloseWindow()
        self.confirm_window.move(200 + self.x(), 216 + self.y())
        self.confirm_window.show()

    def open_results_table(self):
        """Показывает таблицу результатов"""

        self.results_table = ResultsTableWindow()
        self.results_table.move(202 + self.x(), 93 + self.y())
        self.results_table.show()
        logging.info('Results table open')

    def open_delete_result_from(self):
        """Показывает форму для удаления одного результата из таблицы результатов"""

        self.delete_form = DeleteResultWindow()
        self.delete_form.move(179 + self.x(), 93 + self.y())
        self.delete_form.show()

    def open_confirm_clear_all(self):
        """Показывает форму для очистки таблицы результатов"""

        self.confirm_window = ConfirmClearAll()
        self.confirm_window.move(200 + self.x(), 216 + self.y())
        self.confirm_window.show()

    def open_about(self):
        """Показывает информацию об игре и разработчике"""

        self.about_window = AboutWindow(self, self.is_sound)
        for player in (self.player1, self.player2, self.player4):
            player.setVolume(20 * self.is_sound)
        self.player3.set_media(decorate_audio('sounds/about.mp3'))
        self.player3.play()
        self.about_window.move(210 + self.x(), 175 + self.y())
        self.about_window.show()
        logging.info('About open')

    def toggle_sound(self):
        """Переключает звук (т.е. включает или отключает)"""

        # noinspection PyUnresolvedReferences
        if self.sender().isChecked():
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
