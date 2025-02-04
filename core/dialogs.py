import logging
import sys
from typing import TYPE_CHECKING

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QDialog, QMessageBox

if TYPE_CHECKING:
    from core.game import GameWindow

from core.tools import decorate_audio, sql_request
from core.widgets import GameRules, ResultsTableWindow
from ui import (Ui_ConfirmAgain, Ui_ConfirmClearAll, Ui_ConfirmExit, Ui_ConfirmLeave, Ui_GameOver, Ui_StartDialog,
                Ui_Win, Ui_WinLeave)


class StartWindow(QDialog, Ui_StartDialog):
    """Класс типа QDialog, использующийся для ввода имени игрока и показа правил игр

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
    """

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.ok_button.clicked.connect(self.getName)
        self.rulebook_button.clicked.connect(self.showRules)
        self.exit_button.clicked.connect(sys.exit)
        self.msg = QMessageBox()
        self.msg.setWindowTitle('Некорректное имя')
        self.msg.setWindowIcon(QIcon('images/app_icon.ico'))
        self.msg.setIcon(QMessageBox.Warning)

    def getName(self) -> None:
        """Метод, получающий имя игрока"""

        name = self.lineEdit.text()
        if not name:
            self.msg.setText('Введите имя, чтобы учитываться в таблице рекордов.\nНе оставляйте поле пустым.')
            self.msg.show()
        elif any([(le in name) for le in '`~!@#$%^&*()_+{}|:"<>?[]\\;\',./№0123456789']):
            self.msg.setText(
                'Введите корректное имя, состоящее только из букв и пробелов. Не используйте цифры или спецсимволы.'
            )
            self.msg.show()
            self.lineEdit.setText('')
        else:
            self.startGame(name.capitalize())

    def showRules(self):
        """Метод, показывающий правила игры"""

        self.rules_wndw = GameRules()
        self.rules_wndw.show()

    def startGame(self, name: str) -> None:
        """Метод, начинающий игру с заданным именем игрока name и режимом игры

        Параметры
        ---------
        name: str
            имя игрока
        """
        from core.game import GameWindow

        mode = self.buttonGroup.checkedButton().text()
        mode = 'classic' if mode == 'Обычный режим' else 'clock'
        self.game = GameWindow(name, mode)
        self.game.show()

        self.game.lost_change.hide()
        self.game.lost_5050.hide()
        self.game.lost_x2.hide()
        self.game.double_dip.hide()

        self.close()


class WinWindow(QDialog, Ui_Win):
    """Класс типа QDialog, использующийся для отображения окна победы в игре

    Атрибуты
    --------
    parent: GameWindow
        класс основного окна игры
    is_sound: bool
        определяет, включён или отключён ли звук

    Методы
    ------
    restart()
        Перезапускает игру и показывает таблицу результатов
    exit()
        Завершает игру и показывает таблицу результатов
    """

    def __init__(self, parent: 'GameWindow', is_sound: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

        self.parent_ = parent  # родительское окно
        self.is_sound = is_sound

        self.buttonBox.accepted.connect(self.restart)
        self.buttonBox.rejected.connect(self.exit)

    def restart(self):
        """Метод, перезапускающий игру и показывающий таблицу результатов"""

        self.parent_.restartGame()  # перезапускаем игру в родительском окне
        self.close()
        self.results = ResultsTableWindow()
        self.results.move(170 + self.parent_.x(), 93 + self.parent_.y())
        self.results.show()  # показываем таблицу результатов
        logging.info('Game restart')

    def exit(self):
        """Метод, завершающий игру и показывающий таблицу результатов"""

        self.parent_.close()
        self.close()
        self.player = QMediaPlayer()
        self.player.setMedia(
            decorate_audio(f'sounds/quit_game{"_clock" if self.parent_.mode == "clock" else ""}.mp3')
        )  # запускаем трек конца игры
        if self.is_sound:
            self.player.play()
        self.results = ResultsTableWindow()
        self.results.show()
        logging.info('Game close\n')


class GameOverWindow(QDialog, Ui_GameOver):
    """Класс типа QDialog, использующийся для отображения окна поражения в игре

    Атрибуты
    --------
    parent: GameWindow
        класс основного окна игры
    state: tuple[str, str, bool]
        содержит правильный ответ, несгораемую сумму и is_sound (переключатель звука)

    Методы
    ------
    restart()
        Перезапускает игру и показывает таблицу результатов
    exit()
        Завершает игру и показывает таблицу результатов
    """

    def __init__(self, parent: 'GameWindow', state: tuple[str, str, bool]):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

        self.parent_ = parent  # родительское окно
        self.is_sound = state[2]
        self.buttonBox.accepted.connect(self.restart)
        self.buttonBox.rejected.connect(self.exit)
        self.label.setText(self.label.text().replace('{0}', state[0]).replace('{1}', state[1]))
        # заменяем плейсхолдеры на правильный ответ и выигрыш

    def restart(self):
        """Метод, перезапускающий игру и показывающий таблицу результатов"""

        self.parent_.restartGame()
        self.close()
        self.results = ResultsTableWindow()
        self.results.move(170 + self.parent_.x(), 93 + self.parent_.y())
        self.results.show()
        logging.info('Game restart')

    def exit(self):
        """Метод, завершающий игру и показывающий таблицу результатов"""

        self.parent_.close()
        self.close()
        self.player = QMediaPlayer()
        self.player.setMedia(
            decorate_audio(f'sounds/quit_game{"_clock" if self.parent_.mode == "clock" else ""}.mp3')
        )  # запускаем трек конца игры
        if self.is_sound:
            self.player.play()
        self.results = ResultsTableWindow()
        self.results.show()
        logging.info('Game close')


class WinLeaveWindow(Ui_WinLeave, GameOverWindow):
    """Класс, наследующийся от GameOverWindow — необходим для подтверждения выхода из игры при забранных деньгах

    Атрибуты
    --------
    parent: GameWindow
        класс основного окна игры
    state: tuple[str, str, bool]
        содержит (по очереди) правильный ответ, выигрыш и булево, определяющее, включён ли звук или нет

    Методы
    ------
    restart()
        Перезапускает игру и показывает таблицу результатов
    exit()
        Завершает игру и показывает таблицу результатов
    """

    pass


class ConfirmLeaveWindow(QDialog, Ui_ConfirmLeave):
    """Класс типа QDialog, необходимый для подтверждения «забрать деньги»

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
    """

    def __init__(self, parent: 'GameWindow', letter: str, is_sound: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

        self.parent_ = parent  # родительское окно
        self.correct = letter  # правильный ответ
        self.is_sound = is_sound
        self.label.setText(self.label.text().replace('{}', self.parent_.got_amount))
        # заменяем плейсхолдер на сумму, с которой игрок хочет уйти
        self.buttonBox.accepted.connect(self.leave)
        self.buttonBox.rejected.connect(self.close_wndw)

    def leave(self):
        """Метод, покидающий игру, забирающий деньги и предлагающий сыграть ещё раз"""

        sql_request(
            f'INSERT INTO results (name, result, date) VALUES ("{self.parent_.name}", "{self.parent_.got_amount}", "{self.parent_.date}")'
        )
        # вставляем результат игры в таблицы
        self.windialog = WinLeaveWindow(self.parent_, (self.correct, self.parent_.got_amount, self.is_sound))
        # инициализируем окно после «забрать деньги»
        self.windialog.move(169 + self.parent_.x(), 210 + self.parent_.y())
        self.windialog.show()

        for player in (self.parent_.player1, self.parent_.player2, self.parent_.player3, self.parent_.player4):
            player.stop()  # стопим все плееры
        self.parent_.player1.setMedia(
            decorate_audio(
                f'sounds/{"great_" if self.parent_.current_question_num >= 11 else ""}walk_away{"_clock" if self.parent_.mode == "clock" else ""}.mp3'
            )
        )  # запускаем музыку на «забрать деньги»
        self.parent_.player1.play()
        if self.parent_.mode == 'clock':
            self.parent_.qttimer.stop()
        self.parent_.current_state_q_2.setPixmap(
            QPixmap(f'images/question field/correct_{self.correct}.png')
        )  # показываем правильный ответ
        self.parent_.current_state_q_2.startFadeInImage()
        self.parent_.current_state_q_2.show()

        self.parent_.scheduler1.schedule(3000, self.parent_.layout_q.setPixmap, QPixmap('animations/sum/1.png'))
        self.parent_.clear_all_labels()
        n = '1-4' if self.parent_.current_question_num in range(1, 5) else self.parent_.current_question_num
        if self.parent_.mode == 'clock':
            dial = 1 if n in ('1-4', 5) else (2 if n in range(6, 11) else (3 if n in range(11, 15) else 6))
            for i in range(self.parent_.seconds_left // dial, -1, -1):  # анимируем опустошение таймера
                self.parent_.scheduler1.schedule(0, self.parent_.timer_text.setText, str(i * dial))
                self.parent_.scheduler1.schedule(
                    20, self.parent_.timer_view.setPixmap, QPixmap(f'images/timer/{i}.png')
                )
            self.parent_.scheduler1.schedule(0, self.parent_.timer_text.setText, '')
            for i in range(18, 0, -1):  # скрываем его
                self.parent_.scheduler1.schedule(
                    30, self.parent_.timer_view.setPixmap, QPixmap(f'animations/timer/{i}.png')
                )
            self.parent_.scheduler1.schedule(30, self.parent_.timer_view.setPixmap, QPixmap())
        for i in range(1, 38):  # анимация показа суммы выигрыша
            self.parent_.scheduler1.schedule(30, self.parent_.layout_q.setPixmap, QPixmap(f'animations/sum/{i}.png'))
        self.parent_.scheduler1.schedule(
            0, self.parent_.amount_q.setText, self.parent_.got_amount
        )  # показываем сумму выигрыша
        self.parent_.scheduler1.start()

        logging.info('Game over — leave game')

        self.close()

    def close_wndw(self):
        """Метод, закрывающий окно подтверждения при отмене действия"""

        self.parent_.user_control = True
        self.close()


class ConfirmAgainWindow(QDialog, Ui_ConfirmAgain):
    """Класс типа QDialog, необходим для подтверждения к кнопке «Начать новую игру»

    Атрибуты
    --------
    parent: GameWindow
        класс основного окна игры

    Методы
    ------
    restart()
        Перезапускает игру
    """

    def __init__(self, parent: 'GameWindow'):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.parent_ = parent  # родительское окно
        self.buttonBox.accepted.connect(self.restart)
        self.buttonBox.rejected.connect(self.close)

    def restart(self):
        """Метод, перезапускающий игру"""

        self.parent_.restartGame()
        logging.info('Game restart')
        self.close()


class ConfirmCloseWindow(QDialog, Ui_ConfirmExit):
    """Класс типа QDialog, подтверждающий закрытие игры после нажатия кнопки «Закрыть игру» в экшнбаре

    Методы
    ------
    exit()
        Завершает игру и закрывает приложение
    """

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.buttonBox.accepted.connect(self.exit)
        self.buttonBox.rejected.connect(self.close)

    def exit(self):
        """Метод, завершающий игру и закрывающий приложение"""

        logging.info('Game close')
        sys.exit()


class ConfirmClearAll(QDialog, Ui_ConfirmClearAll):
    """Класс типа QDialog, использующийся для очистки всей таблицы результатов

    Методы
    -----
    deleteAllData()
        Очищает всю таблицу результатов
    """

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.buttonBox.accepted.connect(self.deleteAllData)
        self.buttonBox.rejected.connect(self.close)

    def deleteAllData(self):
        """Метод, очищающий всю таблицу результатов"""

        sql_request('DELETE FROM results')
        self.results_table = ResultsTableWindow()
        self.results_table.move(self.x(), self.y() - 117)
        self.results_table.show()
        logging.info('AllR delete')
        self.close()
