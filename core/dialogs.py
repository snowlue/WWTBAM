import logging
import sys
from typing import TYPE_CHECKING

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QDialog, QMessageBox

if TYPE_CHECKING:
    from core.game import GameWindow

from core.tools import convert_amount_to_str, decorate_audio, empty_timer, hide_timer, show_prize, sql_request
from core.widgets import GameRules, ResultsTableWindow
from ui import (Ui_ConfirmAgain, Ui_ConfirmClearAll, Ui_ConfirmExit, Ui_ConfirmLeave, Ui_GameOver, Ui_StartDialog,
                Ui_Win, Ui_WinLeave)


class StartWindow(QDialog, Ui_StartDialog):
    """Стартовое окно для ввода имени игрока и показа правил игр"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.ok_button.clicked.connect(self.get_name)
        self.rulebook_button.clicked.connect(self.show_rules)
        self.exit_button.clicked.connect(sys.exit)
        self.msg = QMessageBox()
        self.msg.setWindowTitle('Некорректное имя')
        self.msg.setWindowIcon(QIcon('images/app_icon.ico'))
        self.msg.setIcon(QMessageBox.Warning)

    def get_name(self) -> None:
        """Получает имя игрока"""
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
            self.start_game(name.capitalize())

    def show_rules(self):
        """Показывает правила игры"""
        self.rules_wndw = GameRules()
        self.rules_wndw.show()

    def start_game(self, name: str) -> None:
        """Начинает игру с заданным именем игрока name и режимом игры"""
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
    """Окно для отображения победы в игре"""

    def __init__(self, parent: 'GameWindow', is_sound: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

        self.parent_ = parent
        self.is_sound = is_sound

        self.buttonBox.accepted.connect(self.restart)
        self.buttonBox.rejected.connect(self.exit)

    def restart(self):
        """Перезапускает игру и показывает таблицу результатов"""
        self.parent_.restart_game()
        self.close()
        self.results = ResultsTableWindow()
        self.results.move(170 + self.parent_.x(), 93 + self.parent_.y())
        self.results.show()
        logging.info('Game restart')

    def exit(self):
        """Завершает игру и показывает таблицу результатов"""
        self.parent_.close()
        self.close()
        self.player = QMediaPlayer()
        self.player.setMedia(decorate_audio(f'sounds/quit_game{"_clock" if self.parent_.mode == "clock" else ""}.mp3'))
        if self.is_sound:
            self.player.play()
        self.results = ResultsTableWindow()
        self.results.show()
        logging.info('Game close\n')


class GameOverWindow(QDialog, Ui_GameOver):
    """Окно для отображения поражения в игре"""

    def __init__(self, parent: 'GameWindow', state: tuple[str, str, bool]):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

        self.parent_ = parent
        self.is_sound = state[2]
        self.buttonBox.accepted.connect(self.restart)
        self.buttonBox.rejected.connect(self.exit)
        if state[0]:
            self.label.setText(self.label.text().replace('{0}', state[0]).replace('{1}', state[1]))
        else:
            text = self.label.text().split(' Правильный')[0] + self.label.text().split('{0}.')[1]
            self.label.setText(text.replace('{1}', state[1]))

    def restart(self):
        """Перезапускает игру и показывает таблицу результатов"""
        self.parent_.restart_game()
        self.close()
        self.results = ResultsTableWindow()
        self.results.move(170 + self.parent_.x(), 93 + self.parent_.y())
        self.results.show()
        logging.info('Game restart')

    def exit(self):
        """Завершает игру и показывает таблицу результатов"""
        self.parent_.close()
        self.close()
        self.player = QMediaPlayer()
        self.player.setMedia(decorate_audio(f'sounds/quit_game{"_clock" if self.parent_.mode == "clock" else ""}.mp3'))
        if self.is_sound:
            self.player.play()
        self.results = ResultsTableWindow()
        self.results.show()
        logging.info('Game close')


class WinLeaveWindow(Ui_WinLeave, GameOverWindow):
    """Окно для подтверждения выхода из игры при забранных деньгах"""

    pass


class ConfirmLeaveWindow(QDialog, Ui_ConfirmLeave):
    """Окно для подтверждения действия «Забрать деньги»"""

    def __init__(self, parent: 'GameWindow', letter: str, is_sound: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))

        self.parent_ = parent
        self.correct_answer = letter if self.parent_.has_shown else ''
        self.is_sound = is_sound

        self.prize = convert_amount_to_str(
            self.parent_.got_amount + self.parent_.saved_seconds_prize + self.parent_.seconds_prize
        )
        self.label.setText(self.label.text().replace('{}', self.prize))
        self.buttonBox.accepted.connect(self.leave)
        self.buttonBox.rejected.connect(self.close_wndw)

    def leave(self):
        """Покидает игру, забирает деньги и предлагает сыграть ещё раз"""

        sql_request(
            f'INSERT INTO results (name, result, date) VALUES ("{self.parent_.name}", "{self.prize}", "{self.parent_.date}")'
        )

        self.windialog = WinLeaveWindow(self.parent_, (self.correct_answer, self.prize, self.is_sound))
        self.windialog.move(169 + self.parent_.x(), 210 + self.parent_.y())

        for player in (self.parent_.player1, self.parent_.player2, self.parent_.player3, self.parent_.player4):
            player.stop()
        self.parent_.player1.setMedia(
            decorate_audio(
                f'sounds/{"great_" if self.parent_.current_question_num >= 11 else ""}walk_away{"_clock" if self.parent_.mode == "clock" else ""}.mp3'
            )
        )
        self.parent_.player1.play()

        if self.parent_.has_shown:
            if self.parent_.mode == 'clock':
                self.parent_.qttimer.stop()
            self.parent_.current_state_q_2.setPixmap(
                QPixmap(f'images/question field/correct_{self.correct_answer}.png')
            )
            self.parent_.current_state_q_2.startFadeInImage()
            self.parent_.current_state_q_2.show()

        self.parent_.scheduler1.schedule(3000, lambda: True)
        self.parent_.scheduler1.schedule(0, self.parent_.double_dip.startFadeOutImage)
        self.parent_.clear_all_labels()
        if self.parent_.mode == 'clock':
            empty_timer(self.parent_)
            hide_timer(self.parent_)
        show_prize(self.parent_, self.prize)
        self.parent_.scheduler1.schedule(1000, self.windialog.show)
        self.parent_.scheduler1.start()

        logging.info('Game over — leave game')

        self.close()

    def close_wndw(self):
        """Закрывает окно подтверждения при отмене действия"""

        self.parent_.user_control = True
        self.close()


class ConfirmAgainWindow(QDialog, Ui_ConfirmAgain):
    """Окно для подтверждения действия к кнопке «Начать новую игру»"""

    def __init__(self, parent: 'GameWindow'):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.parent_ = parent
        self.buttonBox.accepted.connect(self.restart)
        self.buttonBox.rejected.connect(self.close)

    def restart(self):
        """Перезапускает игру"""

        self.parent_.restart_game()
        logging.info('Game restart')
        self.close()


class ConfirmCloseWindow(QDialog, Ui_ConfirmExit):
    """Окно для подтверждения закрытия игры после нажатия кнопки «Закрыть игру» в экшнбаре"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
        self.buttonBox.accepted.connect(self.exit)
        self.buttonBox.rejected.connect(self.close)

    def exit(self):
        """Завершает игру и закрывает приложение"""

        logging.info('Game close')
        sys.exit(0)


class ConfirmClearAll(QDialog, Ui_ConfirmClearAll):
    """Окно для очистки всей таблицы результатов"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images/app_icon.ico'))
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
