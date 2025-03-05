import logging
import os
import random
import sqlite3
import sys
import traceback
from random import shuffle
from types import TracebackType
from typing import TYPE_CHECKING, Type

from PyQt5.QtCore import QObject, QTime, QTimer, QUrl
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from core.application import msg
from core.constants import LOOP_POINTS, SECONDS_FOR_QUESTION

if TYPE_CHECKING:
    from core.game import GameWindow


class AnimationScheduler(QObject):
    """Планировщик анимаций, необходим для своевременного проигрывания анимаций."""

    def __init__(self, parent: 'GameWindow', restore_user_control: bool = True):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(10)
        # noinspection PyUnresolvedReferences
        self._timer.timeout.connect(self._update)  # в случае истечения интервала в 10 мс вызывает _update
        self._start_time = None  # будет хранить QTime запуска анимации
        self._events = []  # список запланированных событий в виде (относительное время, функция, args, kwargs)
        self._current_delay = 0  # текущее относительное время; сбрасывается, когда кончается список событий
        self._restore_user_control = restore_user_control
        self._parent = parent

    def schedule(self, delay: int, func, *args, **kwargs):
        """Планирует выполнение функции func(*args, **kwargs) через delay мс после старта анимации"""
        self._current_delay += delay
        self._events.append((self._current_delay, func, args, kwargs))

    def start(self):
        """Запускает анимацию, высвобождая запланированные события"""
        if not self._events:
            return
        self._events.sort(key=lambda event: event[0])
        self._start_time = QTime.currentTime()
        self._timer.start()
        self._parent.user_control = False

    def _update(self):
        """Проверяет, какие события пора выполнить (периодически вызывается таймером)"""
        if self._start_time is None:
            return

        elapsed = self._start_time.msecsTo(QTime.currentTime())
        # Найдём все события, время которых наступило
        due_events = [event for event in self._events if event[0] <= elapsed]
        for event in due_events:
            _, func, args, kwargs = event
            func(*args, **kwargs)
            self._events.remove(event)

        # Если все события выполнены, останавливаем таймер
        if not self._events:
            self._timer.stop()
            self._parent.user_control = self._restore_user_control
            self._current_delay = 0


class LoopingMediaPlayer(QMediaPlayer):
    """Реализация `QMediaPlayer`, зацикливающая фоновую музыку, для которой прописан момент зацикливания в `LOOP_POINTS`"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = ''
        self.mediaStatusChanged.connect(self.handle_media_status_changed)

    def set_media(self, media: QMediaContent):
        """Устанавливает медиа, аналогично QMediaPlayer.setMedia"""
        self.current_file = 'sounds/' + os.path.relpath(media.canonicalUrl().toLocalFile(), 'sounds')
        self.setMedia(media)

    def handle_media_status_changed(self, status):
        if status != QMediaPlayer.MediaStatus.EndOfMedia:
            return

        start_position = LOOP_POINTS.get(self.current_file, None)
        if start_position is None:
            return

        self.setPosition(start_position)
        self.play()


def empty_timer(window: 'GameWindow'):
    """Опустошает таймер"""
    n = '1-4' if window.current_question_num in range(1, 5) else window.current_question_num
    dial = 1 if n in ('1-4', 5) else (2 if n in range(6, 11) else (3 if n in range(11, 15) else 6))

    if window.has_shown or window.current_question_num == 15:
        seconds_left = window.seconds_left
    else:
        seconds_left = SECONDS_FOR_QUESTION[n]
    for i in range(seconds_left // dial, -1, -1):
        window.scheduler1.schedule(0, window.timer_text.setText, str(i * dial))
        window.scheduler1.schedule(20, window.timer_view.setPixmap, QPixmap(f'images/timer/{i}.png'))
    window.scheduler1.schedule(0, window.timer_text.setText, '')


def refill_timer(window: 'GameWindow', question_num: int, seconds_left: int = 0):
    """Пополняет таймер"""
    n = '1-4' if question_num in range(1, 5) else question_num
    dial = 1 if n in ('1-4', 5) else (2 if n in range(6, 11) else (3 if n in range(11, 15) else 6))
    animation_start = seconds_left // dial + 1
    for i in range(animation_start, 16):
        window.scheduler1.schedule(0, window.timer_text.setText, str(i * dial))
        window.scheduler1.schedule(50, window.timer_view.setPixmap, QPixmap(f'images/timer/{i}.png'))


def hide_timer(window: 'GameWindow'):
    """Скрывает таймер"""
    for i in range(18, 0, -1):
        window.scheduler1.schedule(30, window.timer_view.setPixmap, QPixmap(f'animations/timer/{i}.png'))
    window.scheduler1.schedule(30, window.timer_view.setPixmap, QPixmap())


def show_timer(window: 'GameWindow'):
    for i in range(1, 19):
        window.scheduler1.schedule(30, window.timer_view.setPixmap, QPixmap(f'animations/timer/{i}.png'))


def show_prize(window: 'GameWindow', amount: str):
    for i in range(1, 38):
        window.scheduler1.schedule(30, window.layout_q.setPixmap, QPixmap(f'animations/sum/{i}.png'))
    window.scheduler1.schedule(0, window.amount_q.setText, amount)
    window.scheduler1.schedule(0, window.amount_q.startFadeIn)


def convert_amount_to_str(amount: int) -> str:
    """Преобразует сумму в строку с разделителями разрядов"""
    return '{:,}'.format(amount).replace(',', ' ')


def ask_audience(question_number: int, available_count: int) -> tuple[int, list[int]]:
    """Симулирует помощь зала"""

    if question_number in range(1, 6):
        correct_min, correct_max = 70, 100
    elif question_number in range(6, 11):
        correct_min, correct_max = 50, 80
    elif question_number in range(11, 16):
        correct_min, correct_max = 30, 60
    else:
        correct_min, correct_max = 10, 60

    correct_percentage = random.randint(correct_min, correct_max)
    remaining = 100 - correct_percentage

    other_votes = [random.random() for _ in range(available_count - 1)]
    total = sum(other_votes)
    other_percentages = [round(x / total * remaining) for x in other_votes]

    if not other_percentages:
        return 100, []
    diff = remaining - sum(other_percentages)
    other_percentages[0] += diff
    random.shuffle(other_percentages)

    return correct_percentage, other_percentages


def sql_request(request: str) -> tuple[str, list]:
    """Отправляет запрос к базе данных database.sqlite3 и возвращает "OK" или "ERROR" с описанием ошибки"""

    with sqlite3.connect('database.sqlite3') as con:
        cur = con.cursor()
        try:
            if 'select' in request.lower():
                return 'OK', cur.execute(request).fetchall()
            else:
                cur.execute(request)
                con.commit()
                return 'OK', []
        except Exception as ex:
            return 'ERROR: ' + str(ex), []


def get_local_questions():
    """Получает из базы данных database.sqlite3 вопросы и подготавливает их для игры"""

    questions_data, questions = (
        [sql_request('SELECT * FROM "{}_questions"'.format(i))[1] for i in range(1, 16)],
        [],
    )

    for q_unmixed in questions_data:
        questions_set = []

        q_shuffled = q_unmixed.copy()
        shuffle(q_shuffled)
        for q in q_shuffled[:3]:
            text, correct_answer, answers = q[1], q[2], list(q[2:])
            shuffle(answers)
            questions_set.append([text, correct_answer, answers])

        questions.append(questions_set)

    logging.info('Qs are gotten')
    return questions


def make_table(table: QTableWidget, header: list[str], data: list[list[str]]) -> None:
    """Генерирует таблицу в table с первой строкой header и матрицей data"""

    table.setColumnCount(len(header))
    table.setHorizontalHeaderLabels(header)
    table.setRowCount(0)

    for i, row_list in enumerate(data):
        table.setRowCount(table.rowCount() + 1)
        for j, elem in enumerate(row_list):
            table.setItem(i, j, QTableWidgetItem(elem))
    table.resizeColumnsToContents()

    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    table.setEditTriggers(QTableWidget.NoEditTriggers)


def decorate_audio(file: str) -> QMediaContent:
    """Декорирует путь к аудиофайлу в медиа-контент, понятный для Qt"""

    url = QUrl.fromLocalFile(os.path.abspath(file))  # необходим QUrl, т.к. он будет понятен QMediaContent
    return QMediaContent(url)


def except_hook(exc_type: Type[BaseException], exc_value: BaseException, exc_tb: TracebackType):
    """Обработчик исключений

    При вызове исключения логирует ошибку в логи и показывает окно, предлагающее отправить ошибку разработчику."""

    logging.error(str(exc_value) + '\n' + ''.join(traceback.format_exception(exc_type, exc_value, exc_tb)))
    msg.show()
    msg.buttonClicked.connect(sys.exit)
