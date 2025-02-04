import logging
import os
import sqlite3
import sys
import traceback
from random import shuffle
from types import TracebackType
from typing import TYPE_CHECKING, Type

from PyQt5.QtCore import QObject, QTime, QTimer, QUrl
from PyQt5.QtMultimedia import QMediaContent
from PyQt5.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from core.application import msg

if TYPE_CHECKING:
    from core.game import GameWindow


def sql_request(request: str) -> tuple[str, list]:
    """Метод для запроса данных из базы данных database.sqlite3 и возвращает "OK" или "ERROR" с описанием ошибки

    Параметры
    ---------
    request: str
        текст запроса
    """

    with sqlite3.connect('database.sqlite3') as con:  # подключаемся к бд
        cur = con.cursor()  # и задаём курсор по бд
        try:
            # выясняем цель запроса
            if 'select' in request.lower():  # для получения данных из бд?
                return 'OK', cur.execute(request).fetchall()  # возвращаем выборку
            else:  # для записи данных в бд?
                cur.execute(request)  # распаковываем запрос
                con.commit()
                return 'OK', []
        except Exception as ex:
            return 'ERROR: ' + str(ex), []  # если в запросе ошибка, возвращаем её


def get_questions():
    """Метод для получения и подготовки вопросов из базы данных database.sqlite3 для игры"""

    questions_data, questions = (
        [sql_request('SELECT * FROM "{}_questions"'.format(i))[1] for i in range(1, 16)],
        [],
    )  # извлекаем все вопросы из бд

    for q_unshuffled in questions_data:  # проходимся по списку с вопросами по каждому шагу денежного дерева
        questions_set = []

        q_shuffled = q_unshuffled.copy()
        shuffle(q_shuffled)  # перемешиваем список вопросов
        for q in q_shuffled[:2]:  # берём первые два вопроса
            text, corr_answ, answs = q[1], q[2], list(q[2:])  # отбираем текст вопроса, правильный и другие три ответа
            shuffle(answs)  # перемешиваем ответы
            questions_set.append([text, corr_answ, answs])  # собираем два вопроса — первый и для смены вопроса

        questions.append(questions_set)

    logging.info('Qs are gotten')
    return questions


def makeTable(table: QTableWidget, header: list[str], data: list[list[str]]) -> None:
    """Метод для генерации таблицы в table с первой строкой header и матрицей data

    Параметры
    ---------
    table: QTableWidget
        виджет таблицы из Qt
    header: list[str]
        первая строка таблицы — её заголовок
    data: list[list[str]]
        оставшиеся данные таблицы
    """

    table.setColumnCount(len(header))
    table.setHorizontalHeaderLabels(header)
    table.setRowCount(0)

    for i, rowlist in enumerate(data):  # заносим контент из data в table
        table.setRowCount(table.rowCount() + 1)
        for j, elem in enumerate(rowlist):
            table.setItem(i, j, QTableWidgetItem(elem))
    table.resizeColumnsToContents()

    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    table.setEditTriggers(QTableWidget.NoEditTriggers)


def decorate_audio(file: str) -> QMediaContent:
    """Метод, декорирующий путь к аудиофайлу в медиа-контент, понятный для Qt

    Параметры
    ---------
    file: str
        относительный путь к аудиофайлу
    """

    url = QUrl.fromLocalFile(os.path.abspath(file))  # из пути file определяем QUrl-объект, понятный для QMediaContent
    return QMediaContent(url)  # создаём из QUrl медиа-контент, понятный для Qt, и возвращаем его


def excepthook(exc_type: Type[BaseException], exc_value: BaseException, exc_tb: TracebackType):
    """Обработчик исключений

    При вызове исключения логирует ошибку в логи и показывает окно, предлагающее отправить ошибку разработчику.

    Параметры
    ---------
    exc_type: Type[BaseException]
        тип вызванного исключения
    exc_value: BaseException
        описание исключения
    exc_tb: TracebackType
        подробный трейсбек
    """

    logging.error(
        str(exc_value) + '\n' + ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    )  # логируем ошибку
    msg.show()
    msg.buttonClicked.connect(sys.exit)  # привязываем кнопку «ОК» к завершению приложения


class AnimationScheduler(QObject):
    def __init__(self, parent: 'GameWindow'):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(10)  # интервал проверки (10 мс)
        self._timer.timeout.connect(self._update)
        self._start_time = None  # будет хранить QTime запуска анимации
        self._events = []  # список запланированных событий в виде (относительное время, функция, args, kwargs)
        self._current_delay = 0
        self._parent = parent

    def schedule(self, delay: int, func, *args, **kwargs):
        """
        Запланировать выполнение функции func через delay миллисекунд после старта анимации.
        """
        self._current_delay += delay
        self._events.append((self._current_delay, func, args, kwargs))

    def start(self):
        """
        Запускаем анимацию – сохраняем текущее время и стартуем таймер.
        """
        # сортируем события по времени (на случай, если порядок добавления не по возрастанию)
        if not self._events:
            return
        self._events.sort(key=lambda event: event[0])
        self._start_time = QTime.currentTime()
        self._timer.start()
        self._parent.user_control = False

    def _update(self):
        """
        Метод, вызываемый периодически таймером: проверяет, какие события пора выполнить.
        """
        if self._start_time is None:
            return

        elapsed = self._start_time.msecsTo(QTime.currentTime())
        # Найдём все события, время которых наступило
        due_events = [event for event in self._events if event[0] <= elapsed]
        for event in due_events:
            delay, func, args, kwargs = event
            func(*args, **kwargs)
            self._events.remove(event)

        # Если все события выполнены, останавливаем таймер
        if not self._events:
            self._timer.stop()
            self._parent.user_control = True
            self._current_delay = 0
