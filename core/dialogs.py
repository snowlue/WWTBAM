import logging
import sys
from typing import TYPE_CHECKING

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QDesktopWidget, QDialog, QMessageBox

if TYPE_CHECKING:
    from core.game import GameWindow

from core.constants import APP_ICON, MONEY_TREE_AMOUNTS
from core.tools import (
    AnimationScheduler,
    LoopingMediaPlayer,
    convert_amount_to_str,
    decorate_audio,
    empty_timer,
    hide_timer,
    show_prize,
    sql_request,
)
from core.widgets import GameRules, ResultsTableWindow
from ui import (
    Ui_ConfirmAgain,
    Ui_ConfirmClearAll,
    Ui_ConfirmExit,
    Ui_ConfirmLeave,
    Ui_GameOver,
    Ui_StartDialog,
    Ui_Win,
    Ui_WinLeave,
)


class StartWindow(QDialog, Ui_StartDialog):
    """Стартовое окно для ввода имени игрока и показа правил игр"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.setWindowIcon(APP_ICON)
        self.radioButton_4.toggled.connect(self.check_db_is_ok)
        self.ok_button.clicked.connect(self.get_name)
        self.exit_button.clicked.connect(sys.exit)
        self.rulebook_button.clicked.connect(self.show_rules)
        self.msg = QMessageBox()
        self.msg.setWindowIcon(APP_ICON)
        self.msg.setIcon(QMessageBox.Warning)

    def check_db_is_ok(self):
        """Проверяет, готова ли локальная база вопросов к игре"""
        for i in range(1, 16):
            _, question_data = sql_request(f'SELECT * FROM "{i}_questions"')
            if question_data:
                continue
            self.msg.setWindowTitle('Локальная база не наполнена вопросами')
            self.msg.setText(
                f'В локальной базе вопросов нет вопросов для {i}-го шага денежного дерева. Пожалуйста, добавьте '
                'вопросы для игры или воспользуйтесь удалённой базой вопросов.'
            )
            self.msg.show()
            self.radioButton_3.setChecked(True)
            break

    def get_name(self) -> None:
        """Получает имя игрока"""
        name = self.lineEdit.text()
        if not name:
            self.msg.setText('Введите имя, чтобы учитываться в таблице рекордов.\nНе оставляйте поле пустым.')
            self.msg.show()
        elif any([(le in name) for le in '`~!@#$%^&*()_+{}|:"<>?[]\\;\',./№0123456789']):
            self.msg.setWindowTitle('Некорректное имя')
            self.msg.setText(
                'Введите корректное имя, состоящее только из букв и пробелов. Не используйте цифры или спецсимволы.'
            )
            self.msg.show()
            self.lineEdit.setText('')
        else:
            self.start_game(name.capitalize())

    def show_rules(self):
        """Показывает правила игры"""
        self.player1 = LoopingMediaPlayer(self)  # для фоновой музыки
        self.player2 = QMediaPlayer(self)  # для звука остановки
        self.rules_window = GameRules((self.player1, self.player2))
        self.player1.set_media(decorate_audio('sounds/rules/bed.mp3'))
        self.player1.play()
        self.rules_window.show()

    def start_game(self, name: str) -> None:
        """Начинает игру с заданным именем игрока name и режимом игры"""
        from core.game import GameWindow

        mode = self.buttonGroup.checkedButton().text()
        mode = 'classic' if mode == 'Обычный режим' else 'clock'
        question_sources = self.buttonGroup_2.checkedButton().text()
        question_sources = 'cloud' if question_sources == 'Удалённая база вопросов' else 'local'
        self.game = GameWindow(name, mode, question_sources)
        self.game.show()
        self.close()


class EndGameWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.parent_ = None
        self.is_sound = None

    def restart(self):
        """Перезапускает игру и показывает таблицу результатов"""
        self.parent_.restart_game(True)
        self.close()
        self.results = ResultsTableWindow()
        self.results.move(203 + self.parent_.x(), 93 + self.parent_.y())
        self.results.show()
        logging.info('Game restart')

    def exit(self):
        """Завершает игру и показывает таблицу результатов"""
        self.close()
        self.player = QMediaPlayer()
        self.player.setMedia(decorate_audio(f'sounds/quit_game{"_clock" if self.parent_.mode == "clock" else ""}.mp3'))
        if self.is_sound:
            self.player.play()
        self.results = ResultsTableWindow(True)
        self.results.move(203 + self.parent_.x(), 93 + self.parent_.y())
        self.results.show()
        logging.info('Game close\n')


class WinWindow(EndGameWindow, Ui_Win):
    """Окно для отображения победы в игре"""

    def __init__(self, parent: 'GameWindow', is_sound: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(APP_ICON)

        self.parent_ = parent
        self.is_sound = is_sound

        if self.parent_.mode == 'clock':
            prize = convert_amount_to_str(MONEY_TREE_AMOUNTS[-1] + self.parent_.saved_seconds_prize)
            self.label.setText(
                self.label.text().replace(f'заветные ₽{convert_amount_to_str(MONEY_TREE_AMOUNTS[-1])}', f'₽{prize}')
            )

        self.buttonBox.accepted.connect(self.restart)
        self.buttonBox.rejected.connect(self.exit)


class GameOverWindow(EndGameWindow, Ui_GameOver):
    """Окно для отображения поражения в игре"""

    def __init__(self, parent: 'GameWindow', state: tuple[str, str, bool]):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(APP_ICON)

        self.parent_ = parent
        self.is_sound = state[2]
        self.buttonBox.accepted.connect(self.restart)
        self.buttonBox.rejected.connect(self.exit)
        if state[0]:
            self.label.setText(self.label.text().replace('{0}', state[0]).replace('{1}', state[1]))
        else:
            text = self.label.text().split(' Правильный')[0] + self.label.text().split('{0}.')[1]
            self.label.setText(text.replace('{1}', state[1]))


class WinLeaveWindow(Ui_WinLeave, GameOverWindow):
    """Окно для подтверждения выхода из игры при забранных деньгах"""

    pass


class ConfirmLeaveWindow(QDialog, Ui_ConfirmLeave):
    """Окно для подтверждения действия «Забрать деньги»"""

    def __init__(self, parent: 'GameWindow', letter: str, is_sound: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(APP_ICON)

        self.parent_ = parent
        self.parent_.scheduler1 = AnimationScheduler(self.parent_, False)
        self.correct_answer = letter if self.parent_.has_shown else ''
        self.is_sound = is_sound

        self.prize = convert_amount_to_str(
            self.parent_.got_amount + self.parent_.saved_seconds_prize + self.parent_.seconds_prize
        )
        self.label.setText(self.label.text().replace('{}', self.prize))
        self.buttonBox.accepted.connect(self.leave)
        self.buttonBox.rejected.connect(self.close_window)

    def leave(self, triggered: bool = False):
        """Покидает игру, забирает деньги и предлагает сыграть ещё раз"""

        parent_ = self.parent_
        sql_request(
            f'INSERT INTO results (name, result, date) VALUES ("{parent_.name}", "{self.prize}", "{parent_.date}")'
        )

        self.windialog = WinLeaveWindow(parent_, (self.correct_answer, self.prize, self.is_sound))
        self.windialog.move(201 + parent_.x(), 210 + parent_.y())

        player_list = [parent_.player3] + [parent_.player1, parent_.player2, parent_.player4] * (not triggered)
        for player in player_list:
            player.stop()
        prefix = "great_" if parent_.current_question_num >= 11 and parent_.mode == "clock" else ""
        suffix = "_clock" if parent_.mode == "clock" else ""
        lose_media = f'sounds/{prefix}walk_away{suffix}.mp3'
        parent_.player2.set_media(decorate_audio(lose_media))

        if parent_.has_shown:
            if parent_.mode == 'clock':
                parent_.qt_timer.stop()
            parent_.state_q_2.setPixmap(QPixmap(f'images/question field/correct_{self.correct_answer}.png'))
            parent_.state_q_2.startFadeInImage()
            parent_.state_q_2.show()

        QTimer.singleShot(2000 + 3000 * (parent_.current_question_num == 15), parent_.player2.play)

        parent_.scheduler1.schedule(3000, lambda: True)
        parent_.scheduler1.schedule(0, parent_.central_q.startFadeOutImage)
        parent_.clear_all_labels()
        parent_.update_and_animate_logo_and_background(None, 'intro', None, '1-5')
        if parent_.mode == 'clock':
            empty_timer(parent_)
            hide_timer(parent_)
        show_prize(parent_, self.prize)
        parent_.scheduler1.schedule(1000, self.windialog.show)
        parent_.scheduler1.start()

        def reinit_scheduler():
            parent_.scheduler1 = AnimationScheduler(parent_, True)

        QTimer.singleShot(1000, reinit_scheduler)

        logging.info('Game over — leave game')
        self.close()

    def close_window(self):
        """Закрывает окно подтверждения при отмене действия"""

        self.parent_.user_control = True
        self.close()


class ConfirmAgainWindow(QDialog, Ui_ConfirmAgain):
    """Окно для подтверждения действия к кнопке «Начать новую игру»"""

    def __init__(self, parent: 'GameWindow'):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(APP_ICON)
        self.parent_ = parent
        self.buttonBox.accepted.connect(self.restart)
        self.buttonBox.rejected.connect(self.close)

    def restart(self):
        """Перезапускает игру"""

        self.parent_.restart_game(True, True)
        logging.info('Game restart')
        self.close()


class ConfirmCloseWindow(QDialog, Ui_ConfirmExit):
    """Окно для подтверждения закрытия игры после нажатия кнопки «Закрыть игру» в экшнбаре"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(APP_ICON)
        self.buttonBox.accepted.connect(self.exit)
        self.buttonBox.rejected.connect(self.close)

    @staticmethod
    def exit():
        """Завершает игру и закрывает приложение"""

        logging.info('Game close')
        sys.exit(0)


class ConfirmClearAll(QDialog, Ui_ConfirmClearAll):
    """Окно для очистки всей таблицы результатов"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(APP_ICON)
        self.buttonBox.accepted.connect(self.delete_all_data)
        self.buttonBox.rejected.connect(self.close)

    def delete_all_data(self):
        """Очищает всю таблицу результатов"""

        sql_request('DELETE FROM results')
        self.results_table = ResultsTableWindow()
        self.results_table.move(self.x(), self.y() - 117)
        self.results_table.show()
        logging.info('AllR delete')
        self.close()
