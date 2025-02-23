from dataclasses import dataclass

from PyQt5.QtGui import QIcon

MONEY_TREE_AMOUNTS = [
    0,
    500,
    1_000,
    2_000,
    3_000,
    5_000,
    10_000,
    15_000,
    25_000,
    50_000,
    100_000,
    200_000,
    400_000,
    800_000,
    1_500_000,
    3_000_000,
]

SAFETY_NETS = [0] * 5 + [5_000] * 5 + [100_000] * 5

SECONDS_FOR_QUESTION = {'1-4': 15, 5: 15} | {i: 30 for i in range(6, 11)} | {i: 45 for i in range(11, 15)} | {15: 90}

SECONDS_PRICE = {'1-4': 30, 5: 30} | {i: 308 for i in range(6, 11)} | {i: 1650 for i in range(11, 15)} | {15: 3945}

LOOP_POINTS = (
    {f'sounds/{i}/before_clock.mp3': 15975 for i in range(6, 16)}
    | {f'sounds/{i}/bed.mp3': 0 for i in range(5, 16)}
    | {'sounds/1-4/bed.mp3': 0, 'sounds/rules/bed.mp3': 0}
    | {'sounds/double/first_wrong.mp3': 17017}
)

# noinspection PyTypeChecker
APP_ICON: QIcon = None  # Will be set in application.py


@dataclass
class COORDS:
    show_btn = lambda x, y: 521 <= x <= 584 and 627 <= y <= 665  # noqa: E731
    home = lambda x, y: 1017 <= x <= 1064 and 77 <= y <= 107  # noqa: E731
    ans_A = lambda x, y: 200 <= x <= 538 and 601 <= y <= 642  # noqa: E731
    ans_B = lambda x, y: 568 <= x <= 915 and 601 <= y <= 642  # noqa: E731
    ans_C = lambda x, y: 200 <= x <= 538 and 653 <= y <= 693  # noqa: E731
    ans_D = lambda x, y: 568 <= x <= 915 and 653 <= y <= 693  # noqa: E731
    l_5050 = lambda x, y: 831 <= x <= 878 and 43 <= y <= 73  # noqa: E731
    l_ata = lambda x, y: 892 <= x <= 939 and 43 <= y <= 73  # noqa: E731
    l_x2 = lambda x, y: 955 <= x <= 1002 and 43 <= y <= 73  # noqa: E731
    l_change = lambda x, y: 1017 <= x <= 1064 and 43 <= y <= 73  # noqa: E731
    l_revival = lambda x, y: 831 <= x <= 878 and 77 <= y <= 107  # noqa: E731
    l_immunity = lambda x, y: 892 <= x <= 939 and 77 <= y <= 107  # noqa: E731
    l_ftc = lambda x, y: 955 <= x <= 1002 and 77 <= y <= 107  # noqa: E731


def lifelines_regions_generator(x, y, mode):
    return {
        '5050': COORDS.l_5050(x, y),
        'ata': COORDS.l_ata(x, y),
        'x2': COORDS.l_x2(x, y),
        'change': COORDS.l_change(x, y),
        'revival': COORDS.l_revival(x, y),
        'immunity': COORDS.l_immunity(x, y),
        'ftc': COORDS.l_ftc(x, y) and mode == 'clock',
    }


def answers_regions_generator(x, y):
    return {
        'A': COORDS.ans_A(x, y),
        'B': COORDS.ans_B(x, y),
        'C': COORDS.ans_C(x, y),
        'D': COORDS.ans_D(x, y),
    }
