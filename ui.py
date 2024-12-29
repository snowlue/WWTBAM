from datetime import datetime  # год в копирайте в «О приложении»
from random import choice  # выбирает фон

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QEasingCurve, QPropertyAnimation, QVariant, QVariantAnimation, pyqtSlot
from PyQt5.QtGui import QColor, QFontDatabase, QPalette
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QLabel

import font_resources  # noqa: F401 | ресурсы шрифтов


class AnimationLabel(QLabel):
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)
        self.animation = QVariantAnimation()
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

    def startFadeInImage(self):
        self.effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.effect)

        self.animation = QPropertyAnimation(self.effect, b'opacity')
        self.animation.setDuration(200)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()

    def startFadeOutImage(self):
        self.effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.effect)

        self.animation = QPropertyAnimation(self.effect, b'opacity')
        self.animation.setDuration(200)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.start()


class Ui_StartDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName('Dialog')
        Dialog.setFixedSize(361, 150)
        font = QtGui.QFont()
        font.setFamily('PT Sans')
        font.setPointSize(9)
        Dialog.setFont(font)
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
    def setupUi(self, Form):
        Form.setObjectName('Form')
        Form.resize(616, 350)
        Form.setMinimumSize(QtCore.QSize(616, 293))
        Form.setMaximumSize(QtCore.QSize(616, 867))
        font = QtGui.QFont()
        font.setFamily('PT Sans')
        font.setPointSize(9)
        Form.setFont(font)
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
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 595, 874))
        self.scrollAreaWidgetContents.setObjectName('scrollAreaWidgetContents')
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout.setSpacing(15)
        self.verticalLayout.setObjectName('verticalLayout')

        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)

        self.start_label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.start_label.sizePolicy().hasHeightForWidth())
        self.start_label.setSizePolicy(sizePolicy)
        self.start_label.setFont(font)
        self.start_label.setText('Добро пожаловать в «Кто хочет стать миллионером?»')
        self.start_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.start_label.setObjectName('start_label')
        self.verticalLayout.addWidget(self.start_label)

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
        self.text_mt.setMaximumSize(QtCore.QSize(391, 233))
        self.text_mt.setText(
            '<html><head/><body><p>Правила просты. Перед вами 15 вопросов с разной стоимостью. Чтобы выиграть 3 000'
            ' 000 виртуальных рублей, придётся ответить на все из них.</p><p>Вам представляются две несгораемые суммы '
            'в 5 000 рублей на пятом вопросе и в 100 000 рублей на 10 вопросе. Если вы проиграете, то гарантированно '
            'получите эти деньги, как только пройдёте эти рубежи.</p><p>Сложность вопросов по мере прохождения будет '
            'увеличиваться, что потребует от вас больших знаний и смекалки. Будет непросто, но это достойно 3 000 000 '
            'рублей!</p></body></html>'
        )
        self.text_mt.setWordWrap(True)
        self.text_mt.setObjectName('text_mt')
        self.aboutMoneyTree.addWidget(self.text_mt)

        self.picture_mt = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.picture_mt.setSizePolicy(sizePolicy)
        self.picture_mt.setMaximumSize(QtCore.QSize(172, 233))
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
        self.text_ll.setMaximumSize(QtCore.QSize(573, 221))
        self.text_ll.setText(
            '<html><head/><body><p>Чтобы упростить задачу, предлагаем три подсказки и возможность забрать деньги, '
            'пополнив таблицу результатов своим выигрышем с указанным именем и датой игры.</p><p>1-я подсказка «Замена'
            ' вопроса» заменяет текущий вопрос на другой — пригодится, если не разбираетесь в теме вопроса. (клик по '
            'подсказке или 1 на клавиатуре)<br/>2-я подсказка «50:50» убирает два неверных ответа – полезна, если не '
            'уверены в своём выборе. (клик по подсказке или 2 на клавиатуре)<br/>И 3-я подсказка «Право на ошибку» '
            'даёт вам возможность ошибиться при ответе один раз — отличная страховка на сложных вопросах. (клик по '
            'подсказке или 3 на клавиатуре)<br/>Или вы можете покинуть игру с уже заработанным выигрышем, чтобы не '
            'потерять всё до несгораемой суммы. (клик по иконке «домой» или 4 на клавиатуре)</p></body></html>'
        )
        self.text_ll.setWordWrap(True)
        self.text_ll.setObjectName('text_ll')
        self.aboutLifelines.addWidget(self.text_ll)

        self.picture_ll = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.picture_ll.setSizePolicy(sizePolicy)
        self.picture_ll.setMaximumSize(QtCore.QSize(566, 58))
        self.picture_ll.setPixmap(QtGui.QPixmap('images/rules/lifelines.png'))
        self.picture_ll.setScaledContents(False)
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
        self.text_ans.setMaximumSize(QtCore.QSize(573, 98))
        self.text_ans.setText(
            '<html><head/><body><p>Блок с вопросом и ответами на выбор отображается внизу. В большом верхнем поле '
            'отображается вопрос, а под ним четыре ответа: A, B, C и D (нажимайте на ответ или Q, W, A и S на '
            'клавиатуре). Выбранный ответ будет отмечаться оранжевым цветом, правильный — зелёным, а неправильный в '
            '«праве на ошибку» — серым. Выбирайте ответ с умом!</p></body></html>'
        )
        self.text_ans.setWordWrap(True)
        self.text_ans.setObjectName('text_ans')
        self.aboutAnswers.addWidget(self.text_ans)

        self.picture_ans = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.picture_ans.setSizePolicy(sizePolicy)
        self.picture_ans.setMaximumSize(QtCore.QSize(566, 112))
        self.picture_ans.setPixmap(QtGui.QPixmap('images/rules/question_field.png'))
        self.picture_ans.setScaledContents(True)
        self.picture_ans.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.picture_ans.setObjectName('picture_ans')
        self.aboutAnswers.addWidget(self.picture_ans)

        self.final_label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.final_label.sizePolicy().hasHeightForWidth())
        self.final_label.setSizePolicy(sizePolicy)
        self.final_label.setFont(font)
        self.final_label.setText('Удачной игры, успехов и побед!')
        self.final_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.final_label.setObjectName('final_label')
        self.verticalLayout.addWidget(self.final_label)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_3.addWidget(self.scrollArea)

        QtCore.QMetaObject.connectSlotsByName(Form)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        fontId = QFontDatabase.addApplicationFont(':itc_conduit.ttf')
        if fontId == 0:
            fontName = QFontDatabase.applicationFontFamilies(fontId)[0]

        MainWindow.setObjectName('MainWindow')
        MainWindow.setFixedSize(1100, 703)
        font = QtGui.QFont()
        font.setFamily('PT Sans')
        font.setPointSize(9)
        MainWindow.setFont(font)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName('centralwidget')
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1100, 25))
        self.menubar.setObjectName('menubar')
        self.game_menu = QtWidgets.QMenu(self.menubar)
        self.game_menu.setFont(font)
        self.game_menu.setObjectName('game_menu')
        self.table_menu = QtWidgets.QMenu(self.menubar)
        self.table_menu.setFont(font)
        self.table_menu.setObjectName('table_menu')
        self.menu = QtWidgets.QMenu(self.table_menu)
        self.menu.setObjectName('menu')
        self.help_menu = QtWidgets.QMenu(self.menubar)
        self.help_menu.setFont(font)
        self.help_menu.setObjectName('help_menu')
        MainWindow.setMenuBar(self.menubar)
        self.new_game = QtWidgets.QAction(MainWindow)
        self.new_game.setFont(font)
        self.new_game.setObjectName('new_game')
        self.close_game = QtWidgets.QAction(MainWindow)
        self.close_game.setFont(font)
        self.close_game.setObjectName('close_game')
        self.open_table = QtWidgets.QAction(MainWindow)
        self.open_table.setFont(font)
        self.open_table.setObjectName('open_table')
        self.about = QtWidgets.QAction(MainWindow)
        self.about.setFont(font)
        self.about.setObjectName('about')
        self.action = QtWidgets.QAction(MainWindow)
        self.action.setFont(font)
        self.action.setObjectName('action')
        self.clear_one = QtWidgets.QAction(MainWindow)
        self.clear_one.setFont(font)
        self.clear_one.setObjectName('clear_one')
        self.clear_all = QtWidgets.QAction(MainWindow)
        self.clear_all.setFont(font)
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

        self.questionField = QtWidgets.QWidget(self.centralwidget)
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

        font = QtGui.QFont(fontName)
        font.setPointSize(15)
        font.setBold(False)
        font.setWeight(50)

        self.answer_A = AnimationLabel(self.questionField)
        self.answer_A.setGeometry(QtCore.QRect(237, 99, 288, 40))
        self.answer_A.setPalette(palette)
        self.answer_A.setFont(font)
        self.answer_A.setCursor(QtGui.QCursor(Qt.CursorShape.PointingHandCursor))
        self.answer_A.setText('')
        self.answer_A.setAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter  # type: ignore
        )
        self.answer_A.setWordWrap(True)
        self.answer_A.setObjectName('answer_A')

        self.answer_B = AnimationLabel(self.questionField)
        self.answer_B.setGeometry(QtCore.QRect(607, 99, 288, 40))
        self.answer_B.setPalette(palette)
        self.answer_B.setFont(font)
        self.answer_B.setCursor(QtGui.QCursor(Qt.CursorShape.PointingHandCursor))
        self.answer_B.setText('')
        self.answer_B.setAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter  # type: ignore
        )
        self.answer_B.setWordWrap(True)
        self.answer_B.setObjectName('answer_B')

        self.answer_C = AnimationLabel(self.questionField)
        self.answer_C.setGeometry(QtCore.QRect(237, 151, 288, 40))
        self.answer_C.setPalette(palette)
        self.answer_C.setFont(font)
        self.answer_C.setCursor(QtGui.QCursor(Qt.CursorShape.PointingHandCursor))
        self.answer_C.setText('')
        self.answer_C.setAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter  # type: ignore
        )
        self.answer_C.setWordWrap(True)
        self.answer_C.setObjectName('answer_C')

        self.answer_D = AnimationLabel(self.questionField)
        self.answer_D.setGeometry(QtCore.QRect(607, 151, 288, 40))
        self.answer_D.setPalette(palette)
        self.answer_D.setFont(font)
        self.answer_D.setCursor(QtGui.QCursor(Qt.CursorShape.PointingHandCursor))
        self.answer_D.setText('')
        self.answer_D.setAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter  # type: ignore
        )
        self.answer_D.setWordWrap(True)
        self.answer_D.setObjectName('answer_D')

        self.question = AnimationLabel(self.questionField)
        self.question.setGeometry(QtCore.QRect(190, 7, 728, 80))
        self.question.setPalette(palette)
        self.question.setFont(font)
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

        self.current_state_q_3 = QtWidgets.QLabel(self.questionField)
        self.current_state_q_3.setGeometry(QtCore.QRect(-20, -28, 1142, 226))
        self.current_state_q_3.setText('')
        self.current_state_q_3.setScaledContents(True)
        self.current_state_q_3.setObjectName('current_state_q_3')

        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)

        self.amount_q = QtWidgets.QLabel(self.questionField)
        self.amount_q.setGeometry(QtCore.QRect(127, 60, 850, 81))
        self.amount_q.setPalette(palette)
        font.setPointSize(33)
        self.amount_q.setFont(font)
        self.amount_q.setText('')
        self.amount_q.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.amount_q.setObjectName('amount_q')

        self.double_dip = AnimationLabel(self.questionField)
        self.double_dip.setGeometry(QtCore.QRect(519, 126, 66, 40))
        self.double_dip.setText('')
        self.double_dip.setPixmap(QtGui.QPixmap('images/double-dip.png'))
        self.double_dip.setScaledContents(True)
        self.double_dip.setObjectName('double_dip')

        self.layoutWidget = QtWidgets.QWidget(self.centralwidget)
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
        self.layout_t.setPixmap(QtGui.QPixmap('images/money tree/layout_alpha.png'))
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
        self.lost_change.setPixmap(QtGui.QPixmap('images/money tree/lost_change.png'))
        self.lost_change.setScaledContents(True)
        self.lost_change.setObjectName('lost_change')
        self.lost_5050 = AnimationLabel(self.moneyTree)
        self.lost_5050.setGeometry(QtCore.QRect(0, 0, 411, 480))
        self.lost_5050.setText('')
        self.lost_5050.setPixmap(QtGui.QPixmap('images/money tree/lost_5050.png'))
        self.lost_5050.setScaledContents(True)
        self.lost_5050.setObjectName('lost_5050')
        self.lost_x2 = AnimationLabel(self.moneyTree)
        self.lost_x2.setGeometry(QtCore.QRect(0, 0, 411, 480))
        self.lost_x2.setText('')
        self.lost_x2.setPixmap(QtGui.QPixmap('images/money tree/lost_x2.png'))
        self.lost_x2.setScaledContents(True)
        self.lost_x2.setObjectName('lost_x2')

        self.background = QtWidgets.QLabel(self.centralwidget)
        self.background.setGeometry(QtCore.QRect(0, 0, 1100, 680))
        self.background.setText('')
        self.background.setPixmap(QtGui.QPixmap('images/background{}.jpg'.format(choice(list(map(str, range(1, 9)))))))
        self.background.setScaledContents(True)
        self.background.setObjectName('background')

        self.timer_view = QtWidgets.QLabel(self.centralwidget)
        self.timer_view.setGeometry(QtCore.QRect(215, 419, 678, 64))
        self.timer_view.setText('')
        self.timer_view.setScaledContents(True)
        self.timer_view.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.timer_view.setObjectName('timer')

        self.timer_text = QtWidgets.QLabel(self.centralwidget)
        self.timer_text.setGeometry(QtCore.QRect(509, 443, 89, 40))
        self.timer_text.setPalette(palette)
        font.setPointSize(27)
        font.setBold(True)
        font.setWeight(75)
        self.timer_text.setFont(font)
        self.timer_text.setText('')
        self.timer_text.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.timer_text.setObjectName('timer_text')

        self.layout_q.raise_()
        self.amount_q.raise_()
        self.current_state_q.raise_()
        self.current_state_q_2.raise_()
        self.current_state_q_3.raise_()
        self.question.raise_()
        self.answer_A.raise_()
        self.answer_B.raise_()
        self.answer_C.raise_()
        self.answer_D.raise_()
        self.double_dip.raise_()
        self.background.raise_()
        self.questionField.raise_()
        self.layoutWidget.raise_()
        self.timer_view.raise_()
        self.timer_text.raise_()

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


class Ui_Win(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName('Dialog')
        Dialog.setFixedSize(400, 150)
        font = QtGui.QFont()
        font.setFamily('PT Sans')
        font.setPointSize(9)
        Dialog.setFont(font)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName('horizontalLayout')
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName('verticalLayout')
        self.label = QtWidgets.QLabel(Dialog)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
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
        Dialog.setWindowTitle('Вы — миллионер!')
        self.label.setText(
            'Поздравляем! Вы выиграли и стали миллионером!\nВаш выигрыш составил заветные 3 000 000 руб!\n'
            'Начать новую игру?'
        )


class Ui_GameOver(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName('Dialog')
        Dialog.setFixedSize(400, 150)
        font = QtGui.QFont()
        font.setFamily('PT Sans')
        font.setPointSize(9)
        Dialog.setFont(font)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName('horizontalLayout')
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName('verticalLayout')
        self.label = QtWidgets.QLabel(Dialog)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
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
        Dialog.setWindowTitle('Вы проиграли!')
        self.label.setText('Вы проиграли! Правильный ответ: {0}.\nВаш выигрыш составил {1} руб.\nНачать новую игру?')


class Ui_ConfirmExit(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName('Dialog')
        Dialog.setFixedSize(400, 140)
        font = QtGui.QFont()
        font.setFamily('PT Sans')
        font.setPointSize(9)
        Dialog.setFont(font)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 90, 341, 32))
        self.buttonBox.setFont(font)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.No | QtWidgets.QDialogButtonBox.Yes)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName('buttonBox')
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(24, 20, 351, 50))
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.label.setWordWrap(True)
        self.label.setObjectName('label')

        self.setTextInUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def setTextInUi(self, Dialog):
        Dialog.setWindowTitle('Завершить игру?')
        self.label.setText('Действительно завершить текущую игру без сохранения?')


class Ui_ConfirmLeave(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName('Dialog')
        Dialog.setFixedSize(400, 140)
        font = QtGui.QFont()
        font.setFamily('PT Sans')
        font.setPointSize(9)
        Dialog.setFont(font)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 90, 341, 32))
        self.buttonBox.setFont(font)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.No | QtWidgets.QDialogButtonBox.Yes)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName('buttonBox')
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(24, 20, 351, 50))
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.label.setWordWrap(True)
        self.label.setObjectName('label')

        self.setTextInUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def setTextInUi(self, Dialog):
        Dialog.setWindowTitle('Покинуть игру?')
        self.label.setText('Вы действительно хотите покинуть игру с суммой в {} руб?')


class Ui_WinLeave(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName('Dialog')
        Dialog.setFixedSize(400, 150)
        font = QtGui.QFont()
        font.setFamily('PT Sans')
        font.setPointSize(9)
        Dialog.setFont(font)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName('horizontalLayout')
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName('verticalLayout')
        self.label = QtWidgets.QLabel(Dialog)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
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
        Dialog.setWindowTitle('Вы выиграли, но не всё!')
        self.label.setText(
            'Вы покинули игру! Правильный ответ на этот вопрос: {0}.\nВаш выигрыш составил {1} руб.\n'
            'Начать новую игру?'
        )


class Ui_ConfirmAgain(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName('Dialog')
        Dialog.setFixedSize(400, 140)
        font = QtGui.QFont()
        font.setFamily('PT Sans')
        font.setPointSize(9)
        Dialog.setFont(font)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 90, 341, 32))
        self.buttonBox.setFont(font)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.No | QtWidgets.QDialogButtonBox.Yes)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName('buttonBox')
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(24, 20, 351, 50))
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.label.setWordWrap(True)
        self.label.setObjectName('label')

        self.setTextInUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def setTextInUi(self, Dialog):
        Dialog.setWindowTitle('Начать новую игру?')
        self.label.setText('Действительно начать новую игру без сохранения текущей?')


class Ui_ResultsTable(object):
    def setupUi(self, Form):
        Form.setObjectName('Form')
        Form.setFixedSize(395, 385)
        font = QtGui.QFont()
        font.setFamily('PT Sans')
        font.setPointSize(9)
        Form.setFont(font)
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
        font = QtGui.QFont()
        font.setFamily('PT Sans')
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


class Ui_ConfirmClearAll(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName('Dialog')
        Dialog.setFixedSize(400, 140)
        font = QtGui.QFont()
        font.setFamily('PT Sans')
        Dialog.setFont(font)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 90, 341, 32))
        font.setPointSize(9)
        self.buttonBox.setFont(font)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.No | QtWidgets.QDialogButtonBox.Yes)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName('buttonBox')
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(24, 20, 351, 50))
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        self.label.setWordWrap(True)
        self.label.setObjectName('label')

        self.setTextInUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

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
        font = QtGui.QFont()
        font.setFamily('PT Sans')
        font.setPointSize(9)
        self.ruText.setFont(font)
        self.ruText.setScaledContents(False)
        self.ruText.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)  # type: ignore
        self.ruText.setWordWrap(True)
        self.ruText.setObjectName('ruText')
        self.ruText.setOpenExternalLinks(True)
        self.verticalLayout.addWidget(self.ruText)
        self.enText = QtWidgets.QLabel(Form)
        self.enText.setEnabled(True)
        self.enText.setFont(font)
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
        font = QtGui.QFont()
        font.setFamily('PT Sans')
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
            'написанная на Python и основанная на популярном интеллектуальном телешоу <br/>«Who Wants to Be a '
            'Millionaire?»</p><p><a href="https://github.com/snowlue/"><span style="text-decoration: underline; '
            'color:#3453D0;">© Павел Овчинников, {}</span></a></p></body></html>'.format(year)
        )
        self.enText.setText(
            '<html><body><p><span style="font-weight:600;">The Game «Who Want to Be a Millionaire?»</span></p><p>'
            'The game was written on Python and based<br/>on popular intellectual TV show <br/>«Who Wants to Be a '
            'Millionaire?»</p><p><a href="https://github.com/snowlue/"><span style="text-decoration: underline; '
            'color:#3453D0;">© Pavel Ovchinnikov, {}</span></a></p></body></html>'.format(year)
        )
        self.ruButton.setText('RU')
        self.enButton.setText('EN')
        self.okButton.setText('ОК')
