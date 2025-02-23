# Who Wants to Be a Millionaire?
[![ru](https://img.shields.io/badge/lang-RU-blue?style=flat-square)](https://github.com/snowlue/wwtbam/blob/main/README.md)

[![Made with Python 3.9](https://img.shields.io/badge/Made_with-Python_3.9-336E9E?style=flat-square)][1]
[![Using QT Designer](https://img.shields.io/badge/Using-QT_Designer-25AF37?style=flat-square)][2]
[![Using SQLiteStudio](https://img.shields.io/badge/Using-SQLiteStudio-337CCF?style=flat-square)][3]  
[![PyQt5](https://img.shields.io/badge/PyQt5-40CD52?style=flat-square)][4]
[![SQLite3](https://img.shields.io/badge/SQLite3-107FCB?style=flat-square)][5]
[![PyInstaller](https://img.shields.io/badge/PyInstaller-FFEB5E?style=flat-square)][6]

The popular TV show "Who Wants to Be a Millionaire?" is now available on your PC! 💙  
Hints, questions, virtual rubles, and all the game’s features — everything you love in one application. 💰  
Beat your records and compete with your friends using the high-score table. 🏆  
Get smarter and test your knowledge! 📚

![App screenshot](https://github.com/user-attachments/assets/24ba3f9a-86ec-49cd-b2a2-8cbe9c8297e8)

## How to Run:

0. Install [Python 3.9][1] on your computer.
1. Open a terminal in the repository folder.
2. Enter the following commands:
    ```bash
    pip install -r requirements.txt
    python main.py
    ```
    OR (if Python is not installed, for Windows only)
    ```bash
    cd bin
    main.exe
    ```
3. Enjoy the game! ^_^

⠀(4.) Additionally, the "bin" folder is standalone and can be used on any Windows 7+ system, even if Python is not installed.

## Game Controls:

- At the start of the game, you can choose a timed mode (similar to the Clock Format introduced in the U.S. in 2008).
- Answer questions by clicking on A, B, C, or D with your mouse or pressing Q, W, A, S on your keyboard:
    - ₽5,000 at question 5 and ₽100,000 at question 10 are guaranteed amounts — if you pass these milestones, you will receive the sum even if you lose.
    - Your main goal is to reach ₽3,000,000.
- Use up to three lifelines by clicking on them with your mouse or pressing from 1 to 7 on your keyboard:
    - 50:50 removes two incorrect answers to make it easier
    - "Ask the Audience" shows the audience answer statistics to help you choose the correct answer
    - "Double Dip" allows you to answer again if your first answer is wrong
    - "Switch the Question" swaps the current question with another of the same difficulty
    - "Revival" lets you use one of the lifelines you have already used
    - "Immunity" protects you from a wrong answer — if you make a mistake, you will leave the game with the sum you have already earned
    - "Freeze the Timer" stops the timer until you answer the question
- You can take the money and leave the game by clicking on the home icon or pressing 8 on your keyboard.
- View the high-score table and add your results by playing the game.


[1]: https://www.python.org/downloads/release/python-3913/
[2]: https://doc.qt.io/qt-5/qtdesigner-manual.html
[3]: https://sqlitestudio.pl
[4]: https://pypi.org/project/PyQt5
[5]: https://www.sqlite.org
[6]: https://www.pyinstaller.org
