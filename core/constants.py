MONEYTREE_AMOUNTS = [
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
    | {'sounds/1-4/bed.mp3': 0, 'sounds/rules_bed.mp3': 0}
    | {'sounds/double/first_wrong.mp3': 17017}
)
