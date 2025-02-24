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
    l_1col = lambda x: 831 <= x <= 878  # noqa: E731
    l_2col = lambda x: 892 <= x <= 939  # noqa: E731
    l_3col = lambda x: 955 <= x <= 1002  # noqa: E731
    l_4col = lambda x: 1017 <= x <= 1064  # noqa: E731
    l_1row = lambda y: 43 <= y <= 73  # noqa: E731
    l_2row = lambda y: 77 <= y <= 107  # noqa: E731

    q_1col = lambda x: 200 <= x <= 538  # noqa: E731
    q_2col = lambda x: 568 <= x <= 915  # noqa: E731
    q_1row = lambda y: 601 <= y <= 642  # noqa: E731
    q_2row = lambda y: 653 <= y <= 693  # noqa: E731

    r_1col = lambda x: 12 <= x <= 100  # noqa: E731
    r_2col = lambda x: 140 <= x <= 228  # noqa: E731
    r_3col = lambda x: 268 <= x <= 354  # noqa: E731
    r_4col = lambda x: 395 <= x <= 483  # noqa: E731
    r_5col = lambda x: 523 <= x <= 612  # noqa: E731
    r_1row = lambda y: 703 <= y <= 759  # noqa: E731
    r_2row = lambda y: 767 <= y <= 823  # noqa: E731

    show_btn = lambda x, y: 521 <= x <= 584 and 627 <= y <= 665  # noqa: E731
    ans_A = lambda x, y: COORDS.q_1col(x) and COORDS.q_1row(y)  # noqa: E731
    ans_B = lambda x, y: COORDS.q_2col(x) and COORDS.q_1row(y)  # noqa: E731
    ans_C = lambda x, y: COORDS.q_1col(x) and COORDS.q_2row(y)  # noqa: E731
    ans_D = lambda x, y: COORDS.q_2col(x) and COORDS.q_2row(y)  # noqa: E731
    l_5050 = lambda x, y: COORDS.l_1col(x) and COORDS.l_1row(y)  # noqa: E731
    l_ata = lambda x, y: COORDS.l_2col(x) and COORDS.l_1row(y)  # noqa: E731
    l_x2 = lambda x, y: COORDS.l_3col(x) and COORDS.l_1row(y)  # noqa: E731
    l_change = lambda x, y: COORDS.l_4col(x) and COORDS.l_1row(y)  # noqa: E731
    l_revival = lambda x, y: COORDS.l_1col(x) and COORDS.l_2row(y)  # noqa: E731
    l_immunity = lambda x, y: COORDS.l_2col(x) and COORDS.l_2row(y)  # noqa: E731
    l_ftc = lambda x, y: COORDS.l_3col(x) and COORDS.l_2row(y)  # noqa: E731
    home = lambda x, y: COORDS.l_4col(x) and COORDS.l_2row(y)  # noqa: E731
    safety_net = lambda x, y: 441 <= x <= 611 and 46 <= y <= 313  # noqa: E731
    ping1 = lambda x, y: COORDS.r_1col(x) and COORDS.r_1row(y)  # noqa: E731
    ping2 = lambda x, y: COORDS.r_2col(x) and COORDS.r_1row(y)  # noqa: E731
    ping3 = lambda x, y: COORDS.r_3col(x) and COORDS.r_1row(y)  # noqa: E731
    ping4 = lambda x, y: COORDS.r_4col(x) and COORDS.r_1row(y)  # noqa: E731
    ping5 = lambda x, y: COORDS.r_2col(x) and COORDS.r_2row(y)  # noqa: E731
    ping6 = lambda x, y: COORDS.r_3col(x) and COORDS.r_2row(y)  # noqa: E731
    ping7 = lambda x, y: COORDS.r_4col(x) and COORDS.r_2row(y)  # noqa: E731
    ping8 = lambda x, y: COORDS.r_5col(x) and COORDS.r_2row(y)  # noqa: E731


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


def rules_regions_generator(x, y):
    return {
        'safety_net': COORDS.safety_net(x, y),
        'ping1': COORDS.ping1(x, y),
        'ping2': COORDS.ping2(x, y),
        'ping3': COORDS.ping3(x, y),
        'ping4': COORDS.ping4(x, y),
        'ping5': COORDS.ping5(x, y),
        'ping6': COORDS.ping6(x, y),
        'ping7': COORDS.ping7(x, y),
        'ping8': COORDS.ping8(x, y),
    }
