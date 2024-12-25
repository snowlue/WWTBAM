import logging
import os
import sqlite3
import sys
import traceback  # для получения текстового представления исключения
from random import shuffle
from types import TracebackType
from typing import Type

from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaContent
from PyQt5.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from application import msg


def sql_request(request: str) -> str:
    '''Метод для запроса данных из базы данных database.sqlite3 и возвращает "OK" или "ERROR" с описанием ошибки

    Параметры
    ---------
    request: str
        текст запроса
    '''

    with sqlite3.connect('database.sqlite3') as con:  # подключаемся к бд
        cur = con.cursor()  # и задаём курсор по бд
        try:
            # выясняем цель запроса
            if 'select' in request.lower():  # для получения данных из бд?
                return cur.execute(request).fetchall()  # возвращаем выборку
            else:  # для записи данных в бд?
                cur.execute(request)  # распаковываем запрос
                con.commit()
                return 'OK'
        except Exception as ex:
            return 'ERROR: ' + str(ex)  # если в запросе ошибка, возвращаем её


def get_questions():
    '''Метод для получения и подготовки вопросов из базы данных database.sqlite3 для игры
    '''

    questions_data, questions = [sql_request(
        'SELECT * FROM "{}_questions"'.format(i)
    ) for i in range(1, 16)], []  # извлекаем все вопросы из бд

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
    '''Метод для генерации таблицы в table с первой сторокой header и матрицей data

    Параметры
    ---------
    table: QTableWidget
        виджет таблицы из Qt
    header: list[str]
        первая строка таблицы — её заголовок
    data: list[list[str]]
        оставшиеся данные таблицы
    '''

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
    '''Метод, декорирующий путь к аудиофайлу в медиа-контент, понятный для Qt

    Параметры
    ---------
    file: str
        относительный путь к аудиофайлу
    '''

    url = QUrl.fromLocalFile(os.path.abspath(file))  # определяем из относительного пути file QUrl-объект, понятный для QMediaContent
    return QMediaContent(url)  # создаём из QUrl медиа-контент, понятный для Qt, и возвращаем его


def excepthook(exc_type: Type[BaseException], exc_value: BaseException, exc_tb: TracebackType):
    '''Обработчик исключений

    При вызове исключения логгирует ошибку в логи и показывает окно, предлагающее отправить ошибку разработчику.

    Параметры
    ---------
    exc_type: Type[BaseException]
        тип вызванного исключения
    exc_value: BaseException
        описание исключения
    exc_tb: TracebackType
        подробный трейсбек
    '''

    logging.error(
        str(exc_value) + '\n' +
        ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    )  # логируем ошибку
    msg.show()
    msg.buttonClicked.connect(sys.exit)  # привязываем кнопку «ОК» к завершению приложения
