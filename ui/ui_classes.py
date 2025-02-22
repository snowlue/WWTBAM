from datetime import datetime  # год в копирайте в «О приложении»

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, QVariant, QVariantAnimation, Qt, pyqtSlot
from PyQt5.QtGui import QColor, QFontDatabase, QPalette
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QLabel

import ui.font_resources as font_resources  # noqa: F401 | ресурсы шрифтов
from core.constants import MONEY_TREE_AMOUNTS, SAFETY_NETS
from core.tools import convert_amount_to_str


class AnimationLabel(QLabel):
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)
        self.animation = QVariantAnimation()
        # noinspection PyUnresolvedReferences
        self.animation.valueChanged.connect(self.changeColor)

    @pyqtSlot(QVariant)
    def changeColor(self, color):
        palette = self.palette()
        palette.setColor(QPalette.WindowText, color)
        self.setPalette(palette)

    def startFadeIn(self):
        self.animation.stop()
        self.animation.setStartValue(QColor(255, 255, 255, 0))
        self.animation.setEndValue(QColor(255, 255, 255, 255))
        self.animation.setDuration(750)
        self.animation.setEasingCurve(QEasingCurve.InBack)
        self.animation.start()

    def startFadeOut(self):
        self.animation.stop()
        self.animation.setStartValue(QColor(255, 255, 255, 255))
        self.animation.setEndValue(QColor(255, 255, 255, 0))
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutBack)
        self.animation.start()

    def startFadeInImage(self, duration: int = 200):
        self.effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.effect)

        self.animation = QPropertyAnimation(self.effect, b'opacity')
        self.animation.setDuration(duration)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()

    def startFadeOutImage(self, duration: int = 200):
        self.effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.effect)

        self.animation = QPropertyAnimation(self.effect, b'opacity')
        self.animation.setDuration(duration)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.start()


font = QtGui.QFont()
font9 = QtGui.QFont()
bold_font = QtGui.QFont()
for f in (font, font9, bold_font):
    f.setFamily('PT Sans')
for f in (font9, bold_font):
    f.setPointSize(9)
bold_font.setBold(True)
bold_font.setWeight(75)


class Ui_StartDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName('Dialog')
        Dialog.setFixedSize(361, 150)
        Dialog.setFont(font9)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout_2.setContentsMargins(5, 5, 5, 5)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName('horizontalLayout_2')
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName('verticalLayout')
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setFormAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter  # type: ignore
        )
        self.formLayout.setHorizontalSpacing(10)
        self.formLayout.setVerticalSpacing(0)
        self.formLayout.setObjectName('formLayout')
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName('label')
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label)
        self.lineEdit = QtWidgets.QLineEdit(Dialog)
        self.lineEdit.setObjectName('lineEdit')
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.lineEdit)
        self.verticalLayout.addLayout(self.formLayout)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName('horizontalLayout')
        self.ok_button = QtWidgets.QPushButton(Dialog)
        self.ok_button.setObjectName('ok_button')
        self.horizontalLayout.addWidget(self.ok_button)
        self.exit_button = QtWidgets.QPushButton(Dialog)
        self.exit_button.setObjectName('exit_button')
        self.horizontalLayout.addWidget(self.exit_button)

        self.buttonGroup = QtWidgets.QButtonGroup(Dialog)
        self.buttonGroup.setObjectName('ButtonGroup')
        self.radioButton = QtWidgets.QRadioButton(self)  # type: ignore
        self.radioButton.setChecked(True)
        self.radioButton.setObjectName('radioButton')
        self.buttonGroup.addButton(self.radioButton)
        self.radioButton_2 = QtWidgets.QRadioButton(self)  # type: ignore
        self.radioButton_2.setObjectName('radioButton_2')
        self.buttonGroup.addButton(self.radioButton_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.addWidget(self.radioButton)
        self.horizontalLayout_3.addWidget(self.radioButton_2)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_3.setContentsMargins(0, 5, 0, 5)
        self.horizontalLayout_3.setSpacing(0)

        self.verticalLayout.addLayout(self.horizontalLayout)
        self.rulebook_button = QtWidgets.QPushButton(Dialog)
        self.rulebook_button.setObjectName('rulebook_button')
        self.verticalLayout.addWidget(self.rulebook_button)
        self.verticalLayout.setStretch(0, 2)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout.setStretch(2, 1)
        self.horizontalLayout_2.addLayout(self.verticalLayout)

        self.setTextInUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def setTextInUi(self, Dialog):
        Dialog.setWindowTitle('Начало игры')
        self.label.setText('Введите ваше имя:')
        self.radioButton.setText('Обычный режим')
        self.radioButton_2.setText('Режим на время')
        self.ok_button.setText('Начать игру')
        self.exit_button.setText('Выйти')
        self.rulebook_button.setText('Правила игры')


class Ui_Rules(object):
    def create_big_label(self, name: str, text: str, internal_font: QtGui.QFont):
        self.__setattr__(name, QtWidgets.QLabel(self.scrollAreaWidgetContents))
        label = self.__getattribute__(name)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(label.sizePolicy().hasHeightForWidth())
        label.setSizePolicy(sizePolicy)
        label.setFont(internal_font)
        label.setText(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName(name)
        self.verticalLayout.addWidget(label)

    def setupUi(self, Form):
        Form.setObjectName('Form')
        Form.setFixedSize(624, 886)
        Form.setFont(font9)
        Form.setWindowTitle('Правила игры')
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName('verticalLayout_3')
        self.scrollArea = QtWidgets.QScrollArea(Form)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.scrollArea.setObjectName('scrollArea')
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 624, 933))
        self.scrollAreaWidgetContents.setObjectName('scrollAreaWidgetContents')
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout.setSpacing(15)
        self.verticalLayout.setObjectName('verticalLayout')

        local_font = QtGui.QFont()
        local_font.setPointSize(11)
        local_font.setBold(True)
        local_font.setWeight(75)

        self.create_big_label('start_label', 'Добро пожаловать в «Кто хочет стать миллионером?»', local_font)

        self.aboutMoneyTree = QtWidgets.QHBoxLayout()
        self.aboutMoneyTree.setSpacing(10)
        self.aboutMoneyTree.setObjectName('aboutMoneyTree')
        self.verticalLayout.addLayout(self.aboutMoneyTree)

        self.text_mt = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.text_mt.sizePolicy().hasHeightForWidth())
        self.text_mt.setSizePolicy(sizePolicy)
        self.text_mt.setMaximumSize(QtCore.QSize(420, 266))
        length_tree = len(MONEY_TREE_AMOUNTS) - 1
        max_prize = convert_amount_to_str(MONEY_TREE_AMOUNTS[-1])
        safety_nets = list(set(SAFETY_NETS))[1:]
        milestones = [SAFETY_NETS.index(net) for net in safety_nets]
        safety_nets = [convert_amount_to_str(net) for net in safety_nets]
        self.text_mt.setText(
            f'<html><head/><body><p>Игра проста, как и все лучшие игры!</p><p>Перед вами {length_tree} вопросов и, '
            f'ответив на каждый из них, вы получите виртуальный денежный приз. Если вы хотите выиграть ₽{max_prize}, '
            f'придётся ответить на все {length_tree} вопросов!</p><p>Чтобы вы не уходили с пустыми руками, игра '
            f'предлагает вам две несгораемые суммы — ₽{safety_nets[0]} на {milestones[0]} вопросе и ₽{safety_nets[1]} '
            f'на {milestones[1]} вопросе. В случае если вы пройдёте эти рубежи, но проиграете,<br>то гарантированно '
            f'получите несгораемую сумму.</p><p>Сложность вопросов с прохождением рубежей в ₽{safety_nets[0]} и '
            f'₽{safety_nets[1]} будет увеличиваться, что потребует от вас больших знаний<br>и смекалки.</p><p><b>Будет '
            f'непросто, но это достойно ₽{max_prize}!</b></p></body></html>'
        )
        self.text_mt.setWordWrap(True)
        self.text_mt.setObjectName('text_mt')
        self.aboutMoneyTree.addWidget(self.text_mt)

        self.picture_mt = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.picture_mt.setSizePolicy(sizePolicy)
        self.picture_mt.setMaximumSize(QtCore.QSize(172, 266))
        self.picture_mt.setPixmap(QtGui.QPixmap('images/rules/money_tree.png'))
        self.picture_mt.setScaledContents(True)
        self.picture_mt.setObjectName('picture_mt')
        self.aboutMoneyTree.addWidget(self.picture_mt)

        self.aboutLifelines = QtWidgets.QVBoxLayout()
        self.aboutLifelines.setSpacing(10)
        self.aboutLifelines.setObjectName('aboutLifelines')
        self.verticalLayout.addLayout(self.aboutLifelines)

        self.text_ll = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.text_ll.setSizePolicy(sizePolicy)
        self.text_ll.setMaximumSize(QtCore.QSize(602, 262))
        self.text_ll.setText(
            '<html><head/><body><p>Чтобы упростить задачу, предлагаем четыре подсказки и возможность забрать деньги, '
            'пополнив таблицу результатов своим выигрышем с указанным именем и датой игры.</p><p>Во время игры у вас есть '
            'возможность выбрать любые три из предложенных опций.<br>Будьте осторожны, ведь как только вы выберете '
            'третью опцию, выбор двух оставшихся будет закрыт. <b>Расходуйте подсказки разумно!</b></p><p><b>«Замена '
            'вопроса»</b> заменяет текущий вопрос на другой — пригодится, если не разбираетесь<br>в теме вопроса.<br>'
            '<b>«50:50»</b> убирает два неверных ответа – полезна, если не уверены в своём выборе. <br><b>«Право на '
            'ошибку»</b> даёт вам возможность ошибиться при ответе один раз — отличная страховка на сложных вопросах.'
            '<br><b>«Помощь зала»</b> попросит помощи у виртуального зала, который может помочь вам с ответом<br>на вопрос.'
            '<br>Или вы можете покинуть игру с уже заработанным выигрышем, чтобы не потерять всё<br>до несгораемой '
            'суммы.</p></body></html>'
        )
        self.text_ll.setWordWrap(True)
        self.text_ll.setObjectName('text_ll')
        self.aboutLifelines.addWidget(self.text_ll)

        self.picture_ll = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.picture_ll.setSizePolicy(sizePolicy)
        self.picture_ll.setMaximumSize(QtCore.QSize(602, 56))
        self.picture_ll.setPixmap(QtGui.QPixmap('images/rules/lifelines.png'))
        self.picture_ll.setScaledContents(True)
        self.picture_ll.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.picture_ll.setObjectName('picture_ll')
        self.aboutLifelines.addWidget(self.picture_ll)

        self.aboutAnswers = QtWidgets.QVBoxLayout()
        self.aboutAnswers.setSpacing(10)
        self.aboutAnswers.setObjectName('aboutAnswers')
        self.verticalLayout.addLayout(self.aboutAnswers)

        self.text_ans = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.text_ans.setSizePolicy(sizePolicy)
        self.text_ans.setMinimumSize(QtCore.QSize(0, 0))
        self.text_ans.setMaximumSize(QtCore.QSize(602, 51))
        self.text_ans.setText(
            '<html><head/><body><p>Блок с вопросом и ответами на выбор отображается внизу. В большом верхнем поле '
            'отображается вопрос, а под ним четыре ответа: A, B, C и D. Выбранный ответ будет отмечаться оранжевым '
            'цветом, а правильный — зелёным. Выбирайте ответ с умом!</p></body></html>'
        )
        self.text_ans.setWordWrap(True)
        self.text_ans.setObjectName('text_ans')
        self.aboutAnswers.addWidget(self.text_ans)

        self.picture_ans = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.picture_ans.setSizePolicy(sizePolicy)
        self.picture_ans.setMaximumSize(QtCore.QSize(602, 103))
        self.picture_ans.setPixmap(QtGui.QPixmap('images/rules/question_field.png'))
        self.picture_ans.setScaledContents(True)
        self.picture_ans.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.picture_ans.setObjectName('picture_ans')
        self.aboutAnswers.addWidget(self.picture_ans)

        self.create_big_label('final_label', 'Удачной игры, успехов и побед!', local_font)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_3.addWidget(self.scrollArea)

        QtCore.QMetaObject.connectSlotsByName(Form)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        fontId = QFontDatabase.addApplicationFont(':itc_conduit.ttf')
        fontName = QFontDatabase.applicationFontFamilies(fontId)[0]

        MainWindow.setObjectName('MainWindow')
        MainWindow.setFixedSize(1100, 703)
        MainWindow.setFont(font9)

        self.central_widget = QtWidgets.QWidget(MainWindow)
        self.central_widget.setObjectName('central_widget')
        MainWindow.setCentralWidget(self.central_widget)
        self.central_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        MainWindow.setMouseTracking(True)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1100, 25))
        self.menubar.setObjectName('menubar')
        self.game_menu = QtWidgets.QMenu(self.menubar)
        self.game_menu.setFont(font9)
        self.game_menu.setObjectName('game_menu')
        self.table_menu = QtWidgets.QMenu(self.menubar)
        self.table_menu.setFont(font9)
        self.table_menu.setObjectName('table_menu')
        self.menu = QtWidgets.QMenu(self.table_menu)
        self.menu.setObjectName('menu')
        self.help_menu = QtWidgets.QMenu(self.menubar)
        self.help_menu.setFont(font9)
        self.help_menu.setObjectName('help_menu')
        MainWindow.setMenuBar(self.menubar)
        self.new_game = QtWidgets.QAction(MainWindow)
        self.new_game.setFont(font9)
        self.new_game.setObjectName('new_game')
        self.close_game = QtWidgets.QAction(MainWindow)
        self.close_game.setFont(font9)
        self.close_game.setObjectName('close_game')
        self.open_table = QtWidgets.QAction(MainWindow)
        self.open_table.setFont(font9)
        self.open_table.setObjectName('open_table')
        self.about = QtWidgets.QAction(MainWindow)
        self.about.setFont(font9)
        self.about.setObjectName('about')
        self.action = QtWidgets.QAction(MainWindow)
        self.action.setFont(font9)
        self.action.setObjectName('action')
        self.clear_one = QtWidgets.QAction(MainWindow)
        self.clear_one.setFont(font9)
        self.clear_one.setObjectName('clear_one')
        self.clear_all = QtWidgets.QAction(MainWindow)
        self.clear_all.setFont(font9)
        self.clear_all.setObjectName('clear_all')
        self.sound_btn = QtWidgets.QAction(MainWindow)
        self.sound_btn.setCheckable(True)
        self.sound_btn.setChecked(True)
        self.sound_btn.setObjectName('sound_btn')
        self.game_menu.addAction(self.new_game)
        self.game_menu.addAction(self.close_game)
        self.game_menu.addSeparator()
        self.game_menu.addAction(self.sound_btn)
        self.menu.addAction(self.clear_one)
        self.menu.addAction(self.clear_all)
        self.table_menu.addAction(self.open_table)
        self.table_menu.addAction(self.menu.menuAction())
        self.help_menu.addAction(self.about)
        self.menubar.addAction(self.game_menu.menuAction())
        self.menubar.addAction(self.table_menu.menuAction())
        self.menubar.addAction(self.help_menu.menuAction())

        self.questionField = QtWidgets.QWidget(self.central_widget)
        self.questionField.setGeometry(QtCore.QRect(0, 477, 1100, 201))
        self.questionField.setObjectName('questionField')

        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)

        local_font = QtGui.QFont(fontName)
        local_font.setPointSize(15)
        local_font.setBold(False)
        local_font.setWeight(50)

        self.answer_A = AnimationLabel(self.questionField)
        self.answer_B = AnimationLabel(self.questionField)
        self.answer_C = AnimationLabel(self.questionField)
        self.answer_D = AnimationLabel(self.questionField)
        for answer_letter in ('answer_A', 'answer_B', 'answer_C', 'answer_D'):
            percent_label = self.__getattribute__(answer_letter)
            percent_label.setPalette(palette)
            percent_label.setFont(local_font)
            percent_label.setCursor(QtGui.QCursor(Qt.CursorShape.PointingHandCursor))
            percent_label.setText('')
            percent_label.setAlignment(
                Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                # type: ignore
            )
            percent_label.setWordWrap(True)
            percent_label.setObjectName(answer_letter)

        for answer_letter, rect in zip(
            ('answer_A', 'answer_B', 'answer_C', 'answer_D'),
            ((237, 99, 288, 40), (607, 99, 288, 40), (237, 151, 288, 40), (607, 151, 288, 40)),
        ):
            percent_label = self.__getattribute__(answer_letter)
            percent_label.setGeometry(QtCore.QRect(*rect))

        self.question = AnimationLabel(self.questionField)
        self.question.setGeometry(QtCore.QRect(190, 7, 728, 80))
        self.question.setPalette(palette)
        self.question.setFont(local_font)
        self.question.setText('')
        self.question.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.question.setWordWrap(True)
        self.question.setObjectName('question')

        self.layout_q = QtWidgets.QLabel(self.questionField)
        self.layout_q.setGeometry(QtCore.QRect(-20, -28, 1142, 226))
        self.layout_q.setText('')
        self.layout_q.setPixmap(QtGui.QPixmap('animation/question field/1.png'))
        self.layout_q.setScaledContents(True)
        self.layout_q.setObjectName('layout_q')

        self.current_state_q = AnimationLabel(self.questionField)
        self.current_state_q.setGeometry(QtCore.QRect(-20, -28, 1142, 226))
        self.current_state_q.setText('')
        self.current_state_q.setScaledContents(True)
        self.current_state_q.setObjectName('current_state_q')

        self.current_state_q_2 = AnimationLabel(self.questionField)
        self.current_state_q_2.setGeometry(QtCore.QRect(-20, -28, 1142, 226))
        self.current_state_q_2.setText('')
        self.current_state_q_2.setScaledContents(True)
        self.current_state_q_2.setObjectName('current_state_q_2')

        self.current_state_q_3 = AnimationLabel(self.questionField)
        self.current_state_q_3.setGeometry(QtCore.QRect(-20, -28, 1142, 226))
        self.current_state_q_3.setText('')
        self.current_state_q_3.setScaledContents(True)
        self.current_state_q_3.setObjectName('current_state_q_3')

        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)

        self.amount_q = AnimationLabel(self.questionField)
        self.amount_q.setGeometry(QtCore.QRect(127, 60, 850, 81))
        self.amount_q.setPalette(palette)
        local_font.setPointSize(33)
        self.amount_q.setFont(local_font)
        self.amount_q.setText('')
        self.amount_q.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.amount_q.setObjectName('amount_q')

        self.double_dip = AnimationLabel(self.questionField)
        self.double_dip.setGeometry(QtCore.QRect(519, 126, 66, 40))
        self.double_dip.setText('')
        self.double_dip.setPixmap(QtGui.QPixmap('images/double-dip.png'))
        self.double_dip.setScaledContents(True)
        self.double_dip.setObjectName('double_dip')

        self.layoutWidget = QtWidgets.QWidget(self.central_widget)
        self.layoutWidget.setGeometry(QtCore.QRect(0, 0, 1101, 491))
        self.layoutWidget.setObjectName('layoutWidget')

        self.moneyTree = QtWidgets.QWidget(self.layoutWidget)
        self.moneyTree.setObjectName('moneyTree')

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.horizontalLayout.addWidget(self.moneyTree)
        self.horizontalLayout.setStretch(0, 101)
        self.horizontalLayout.setStretch(1, 50)
        self.horizontalLayout.setObjectName('horizontalLayout')

        self.layout_t = QtWidgets.QLabel(self.moneyTree)
        self.layout_t.setGeometry(QtCore.QRect(0, 0, 411, 480))
        self.layout_t.setText('')
        self.layout_t.setPixmap(QtGui.QPixmap('images/money tree/layout.png'))
        self.layout_t.setScaledContents(True)
        self.layout_t.setObjectName('layout_t')

        self.current_state_t = QtWidgets.QLabel(self.moneyTree)
        self.current_state_t.setGeometry(QtCore.QRect(0, 0, 411, 480))
        self.current_state_t.setText('')
        self.current_state_t.setScaledContents(True)
        self.current_state_t.setObjectName('current_state_t')

        self.lost_change = AnimationLabel(self.moneyTree)
        self.lost_change.setGeometry(QtCore.QRect(0, 0, 411, 480))
        self.lost_change.setText('')
        self.lost_change.setPixmap(QtGui.QPixmap('images/money tree/change/lost.png'))
        self.lost_change.setScaledContents(True)
        self.lost_change.setObjectName('lost_change')
        self.lost_5050 = AnimationLabel(self.moneyTree)
        self.lost_5050.setGeometry(QtCore.QRect(0, 0, 411, 480))
        self.lost_5050.setText('')
        self.lost_5050.setPixmap(QtGui.QPixmap('images/money tree/5050/lost.png'))
        self.lost_5050.setScaledContents(True)
        self.lost_5050.setObjectName('lost_5050')
        self.lost_x2 = AnimationLabel(self.moneyTree)
        self.lost_x2.setGeometry(QtCore.QRect(0, 0, 411, 480))
        self.lost_x2.setText('')
        self.lost_x2.setPixmap(QtGui.QPixmap('images/money tree/x2/lost.png'))
        self.lost_x2.setScaledContents(True)
        self.lost_x2.setObjectName('lost_x2')
        self.lost_ata = AnimationLabel(self.moneyTree)
        self.lost_ata.setGeometry(QtCore.QRect(0, 0, 411, 480))
        self.lost_ata.setText('')
        self.lost_ata.setPixmap(QtGui.QPixmap('images/money tree/ata/lost.png'))
        self.lost_ata.setScaledContents(True)
        self.lost_ata.setObjectName('lost_ata')
        self.deactivated_home = AnimationLabel(self.moneyTree)
        self.deactivated_home.setGeometry(QtCore.QRect(0, 0, 411, 480))
        self.deactivated_home.setText('')
        self.deactivated_home.setPixmap(QtGui.QPixmap('images/money tree/home/deactivated.png'))
        self.deactivated_home.setScaledContents(True)
        self.deactivated_home.setObjectName('deactivated_home')
        self.current_state_ll = AnimationLabel(self.moneyTree)
        self.current_state_ll.setGeometry(QtCore.QRect(0, 0, 411, 480))
        self.current_state_ll.setText('')
        self.current_state_ll.setScaledContents(True)
        self.current_state_ll.setObjectName('current_state_ll')

        self.background_1 = QtWidgets.QLabel(self.central_widget)
        self.background_1.setGeometry(QtCore.QRect(0, 0, 1100, 680))
        self.background_1.setText('')
        self.background_1.setScaledContents(True)
        self.background_1.setObjectName('background_1')

        self.background_2 = AnimationLabel(self.central_widget)
        self.background_2.setGeometry(QtCore.QRect(0, 0, 1100, 680))
        self.background_2.setText('')
        self.background_2.setScaledContents(True)
        self.background_2.setObjectName('background_2')

        self.timer_view = QtWidgets.QLabel(self.central_widget)
        self.timer_view.setGeometry(QtCore.QRect(215, 419, 678, 64))
        self.timer_view.setText('')
        self.timer_view.setScaledContents(True)
        self.timer_view.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.timer_view.setObjectName('timer')

        self.timer_text = AnimationLabel(self.central_widget)
        self.timer_text.setGeometry(QtCore.QRect(509, 443, 89, 40))
        self.timer_text.setPalette(palette)
        local_font.setPointSize(27)
        local_font.setBold(True)
        local_font.setWeight(75)
        self.timer_text.setFont(local_font)
        self.timer_text.setText('')
        self.timer_text.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.timer_text.setObjectName('timer_text')

        verdana_font = QtGui.QFont()
        verdana_font.setFamily('Verdana')
        verdana_font.setPointSize(11)
        verdana_font.setBold(True)
        verdana_font.setWeight(75)
        styles = 'color: rgb(255, 255, 255);'

        self.ata_layout = AnimationLabel(self.central_widget)
        self.ata_layout.setObjectName('ata_layout')
        self.ata_layout.setGeometry(QtCore.QRect(503, 15, 226, 331))
        self.ata_layout.setPixmap(QtGui.QPixmap('images/ata.png'))
        self.ata_layout.setScaledContents(True)
        self.ata_layout.hide()

        self.ata_a_percents = AnimationLabel(self.central_widget)
        self.ata_b_percents = AnimationLabel(self.central_widget)
        self.ata_c_percents = AnimationLabel(self.central_widget)
        self.ata_d_percents = AnimationLabel(self.central_widget)
        for answer_letter, rect in zip(
            ('a', 'b', 'c', 'd'),
            ((517, 28), (566, 28), (619, 28), (668, 28)),
        ):
            percent_label = self.__getattribute__(f'ata_{answer_letter}_percents')
            percent_label.setGeometry(QtCore.QRect(*rect, 49, 22))
            percent_label.setFont(verdana_font)
            percent_label.setStyleSheet(styles)
            percent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            percent_label.hide()

        score_column = QtGui.QPixmap('images/ata_score.png')
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        self.ata_a_score = QLabel()
        self.ata_b_score = QLabel()
        self.ata_c_score = QLabel()
        self.ata_d_score = QLabel()
        for i, (answer_letter, coord_x) in enumerate(zip(('a', 'b', 'c', 'd'), (526, 575, 628, 677))):
            self.__setattr__(f'verticalLayoutWidget_{i}', QtWidgets.QWidget(self.central_widget))
            layout_widget = self.__getattribute__(f'verticalLayoutWidget_{i}')
            layout_widget.setObjectName(f'verticalLayoutWidget_{i}')
            layout_widget.setGeometry(QtCore.QRect(coord_x, 49, 31, 182))

            self.__setattr__(f'ata_{answer_letter}', QtWidgets.QVBoxLayout(layout_widget))
            extending_label = self.__getattribute__(f'ata_{answer_letter}')
            extending_label.setSpacing(0)
            extending_label.setObjectName(f'ata_{answer_letter}')
            extending_label.setContentsMargins(0, 0, 0, 0)
            self.__setattr__(
                f'verticalSpacer_{i}',
                QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding),
            )
            spacer = self.__getattribute__(f'verticalSpacer_{i}')
            extending_label.addItem(spacer)
            self.__setattr__(f'ata_{answer_letter}_score', QLabel(layout_widget))
            column_label = self.__getattribute__(f'ata_{answer_letter}_score')
            column_label.setObjectName(f'ata_{answer_letter}_score')
            column_label.setEnabled(True)
            sizePolicy.setHeightForWidth(column_label.sizePolicy().hasHeightForWidth())
            column_label.setSizePolicy(sizePolicy)
            column_label.setMaximumSize(QtCore.QSize(29, 180))
            column_label.setPixmap(score_column)
            column_label.setScaledContents(True)
            column_label.hide()
            extending_label.addWidget(column_label)

        big_logo_position = QtCore.QRect(227, 98, 300, 300)
        self.big_logo_1 = AnimationLabel(self.central_widget)
        self.big_logo_1.setObjectName('big_logo_1')
        self.big_logo_1.setGeometry(big_logo_position)
        self.big_logo_1.setPixmap(QtGui.QPixmap('images/logo/intro.png'))
        self.big_logo_1.setScaledContents(True)
        self.big_logo_1.hide()

        self.big_logo_2 = AnimationLabel(self.central_widget)
        self.big_logo_2.setObjectName('big_logo_2')
        self.big_logo_2.setGeometry(big_logo_position)
        self.big_logo_2.setScaledContents(True)
        self.big_logo_2.hide()

        # noinspection PyUnresolvedReferences
        for label in (
            self.layout_q,
            self.amount_q,
            self.current_state_q,
            self.current_state_q_2,
            self.current_state_q_3,
            self.question,
            self.answer_A,
            self.answer_B,
            self.answer_C,
            self.answer_D,
            self.double_dip,
            self.lost_change,
            self.lost_5050,
            self.lost_x2,
            self.lost_ata,
            self.background_1,
            self.background_2,
            self.questionField,
            self.layoutWidget,
            self.timer_view,
            self.timer_text,
            self.big_logo_1,
            self.big_logo_2,
            self.ata_layout,
            self.ata_a_percents,
            self.ata_b_percents,
            self.ata_c_percents,
            self.ata_d_percents,
            self.verticalLayoutWidget_0,
            self.verticalLayoutWidget_1,
            self.verticalLayoutWidget_2,
            self.verticalLayoutWidget_3,
        ):
            label.raise_()

        self.setTextInUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def setTextInUi(self, MainWindow):
        MainWindow.setWindowTitle('Кто хочет стать Миллионером?')
        self.game_menu.setTitle('Игра')
        self.table_menu.setTitle('Таблица результатов')
        self.menu.setTitle('Очистить')
        self.help_menu.setTitle('Помощь')
        self.new_game.setText('Начать новую игру')
        self.close_game.setText('Завершить игру')
        self.open_table.setText('Открыть')
        self.about.setText('О программе')
        self.action.setText('Удалить один результат')
        self.clear_one.setText('Удалить один результат')
        self.clear_all.setText('Удалить всё')
        self.sound_btn.setText('Звук')


class EndGameDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName('Dialog')
        Dialog.setFixedSize(400, 150)
        Dialog.setFont(font9)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName('horizontalLayout')
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName('verticalLayout')
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setFont(bold_font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.label.setObjectName('label')
        self.verticalLayout.addWidget(self.label)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.No | QtWidgets.QDialogButtonBox.Yes)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName('buttonBox')
        self.verticalLayout.addWidget(self.buttonBox)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.setTextInUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def setTextInUi(self, Dialog):
        pass


class Ui_Win(EndGameDialog):
    def setTextInUi(self, Dialog):
        Dialog.setWindowTitle('Вы — миллионер!')
        self.label.setText(
            'Поздравляем! Вы выиграли и стали миллионером!\nВаш выигрыш составил заветные ₽3 000 000!\n'
            'Начать новую игру?'
        )


class Ui_GameOver(EndGameDialog):
    def setTextInUi(self, Dialog):
        Dialog.setWindowTitle('Вы проиграли!')
        self.label.setText('Вы проиграли! Правильный ответ: {0}.\nВаш выигрыш составил ₽{1}.\nНачать новую игру?')


class ConfirmDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName('Dialog')
        Dialog.setFixedSize(400, 140)
        Dialog.setFont(font9)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 90, 341, 32))
        self.buttonBox.setFont(font9)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.No | QtWidgets.QDialogButtonBox.Yes)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName('buttonBox')
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(24, 20, 351, 50))
        self.label.setFont(bold_font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setObjectName('label')

        self.setTextInUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def setTextInUi(self, Dialog):
        pass


class Ui_ConfirmExit(ConfirmDialog):
    def setTextInUi(self, Dialog):
        Dialog.setWindowTitle('Завершить игру?')
        self.label.setText('Действительно завершить текущую игру без сохранения?')


class Ui_ConfirmLeave(ConfirmDialog):
    def setTextInUi(self, Dialog):
        Dialog.setWindowTitle('Покинуть игру?')
        self.label.setText('Вы действительно хотите покинуть игру\nс суммой в ₽{}?')


class Ui_WinLeave(EndGameDialog):
    def setTextInUi(self, Dialog):
        Dialog.setWindowTitle('Вы выиграли, но не всё!')
        self.label.setText(
            'Вы покинули игру! Правильный ответ на этот вопрос: {0}.\nВаш выигрыш составил ₽{1}.\nНачать новую игру?'
        )


class Ui_ConfirmAgain(ConfirmDialog):
    def setTextInUi(self, Dialog):
        Dialog.setWindowTitle('Начать новую игру?')
        self.label.setText('Действительно начать новую игру без сохранения текущей?')


class Ui_ResultsTable(object):
    def setupUi(self, Form):
        Form.setObjectName('Form')
        Form.setFixedSize(395, 385)
        Form.setFont(font9)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout.setContentsMargins(10, 10, 10, 10)
        self.horizontalLayout.setObjectName('horizontalLayout')
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName('verticalLayout')
        self.tableWidget = QtWidgets.QTableWidget(Form)
        self.tableWidget.setObjectName('tableWidget')
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.verticalLayout.addWidget(self.tableWidget)
        self.okButton = QtWidgets.QPushButton(Form)
        self.okButton.setObjectName('okButton')
        self.verticalLayout.addWidget(self.okButton)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.setTextInUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def setTextInUi(self, Form):
        Form.setWindowTitle('Таблица результатов')
        self.okButton.setText('ОК')


class Ui_DeleteResult(object):
    def setupUi(self, Form):
        Form.setObjectName('Form')
        Form.setFixedSize(442, 385)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout.setObjectName('verticalLayout')
        self.tableWidget = QtWidgets.QTableWidget(Form)
        self.tableWidget.setFont(font)
        self.tableWidget.setObjectName('tableWidget')
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.verticalLayout.addWidget(self.tableWidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName('horizontalLayout')
        self.label = QtWidgets.QLabel(Form)
        self.label.setFont(font)
        self.label.setObjectName('label')
        self.horizontalLayout.addWidget(self.label)
        self.spinBox = QtWidgets.QSpinBox(Form)
        self.spinBox.setFont(font)
        self.spinBox.setObjectName('spinBox')
        self.horizontalLayout.addWidget(self.spinBox)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.deleteButton = QtWidgets.QPushButton(Form)
        self.deleteButton.setFont(font)
        self.deleteButton.setObjectName('deleteButton')
        self.verticalLayout.addWidget(self.deleteButton)

        self.setTextInUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def setTextInUi(self, Form):
        Form.setWindowTitle('Удаление результата из таблицы')
        self.label.setText('Выберите номер результата для удаления:')
        self.deleteButton.setText('Удалить (без подтверждений, сразу при нажатии)')


class Ui_ConfirmClearAll(ConfirmDialog):
    def setTextInUi(self, Dialog):
        Dialog.setWindowTitle('Очистить таблицу результатов?')
        self.label.setText('Действительно очистить всю таблицу результатов без возможности вернуть?')


class Ui_About(object):
    def setupUi(self, Form):
        Form.setObjectName('Form')
        Form.setFixedSize(380, 222)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout_2.setObjectName('horizontalLayout_2')
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName('verticalLayout')
        self.ruText = QtWidgets.QLabel(Form)
        self.ruText.setFont(font9)
        self.ruText.setScaledContents(False)
        self.ruText.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)  # type: ignore
        self.ruText.setWordWrap(True)
        self.ruText.setObjectName('ruText')
        self.ruText.setOpenExternalLinks(True)
        self.verticalLayout.addWidget(self.ruText)
        self.enText = QtWidgets.QLabel(Form)
        self.enText.setEnabled(True)
        self.enText.setFont(font9)
        self.enText.setScaledContents(False)
        self.enText.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)  # type: ignore
        self.enText.setWordWrap(True)
        self.enText.setObjectName('enText')
        self.enText.setOpenExternalLinks(True)
        self.verticalLayout.addWidget(self.enText)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setContentsMargins(40, -1, 40, -1)
        self.verticalLayout_2.setObjectName('verticalLayout_2')
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName('horizontalLayout')
        self.ruButton = QtWidgets.QPushButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ruButton.sizePolicy().hasHeightForWidth())
        self.ruButton.setSizePolicy(sizePolicy)
        self.ruButton.setMaximumSize(QtCore.QSize(50, 16777215))
        self.ruButton.setFont(font)
        self.ruButton.setObjectName('ruButton')
        self.horizontalLayout.addWidget(self.ruButton)
        self.enButton = QtWidgets.QPushButton(Form)
        self.enButton.setSizePolicy(sizePolicy)
        self.enButton.setMaximumSize(QtCore.QSize(50, 16777215))
        self.enButton.setFont(font)
        self.enButton.setObjectName('enButton')
        self.horizontalLayout.addWidget(self.enButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.okButton = QtWidgets.QPushButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.okButton.sizePolicy().hasHeightForWidth())
        self.okButton.setSizePolicy(sizePolicy)
        self.okButton.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.okButton.setFont(font)
        self.okButton.setObjectName('okButton')
        self.verticalLayout_2.addWidget(self.okButton)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        self.horizontalLayout_2.addLayout(self.verticalLayout)

        self.setTextInUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def setTextInUi(self, Form):
        Form.setWindowTitle('О программе')
        year = datetime.today().year
        self.ruText.setText(
            '<html><body><p><span style="font-weight:600;">Игра «Кто хочет стать Миллионером?»</span></p><p>Игра, '
            'написанная на Python и основанная на популярном интеллектуальном телешоу <br>«Who Wants to Be a '
            'Millionaire?»</p><p><a href="https://github.com/snowlue/"><span style="text-decoration: underline; '
            'color:#3453D0;">© Павел Овчинников, {}</span></a></p></body></html>'.format(year)
        )
        self.enText.setText(
            '<html><body><p><span style="font-weight:600;">The Game «Who Want to Be a Millionaire?»</span></p><p>'
            'The game was written on Python and based<br>on popular intellectual TV show <br>«Who Wants to Be a '
            'Millionaire?»</p><p><a href="https://github.com/snowlue/"><span style="text-decoration: underline; '
            'color:#3453D0;">© Pavel Ovchinnikov, {}</span></a></p></body></html>'.format(year)
        )
        self.ruButton.setText('RU')
        self.enButton.setText('EN')
        self.okButton.setText('ОК')
