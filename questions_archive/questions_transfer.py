from contextlib import suppress
import sqlite3
import pandas as pd  # type: ignore
import re

data_file = 'База КХСМ.xlsx'
start_row = 4

data = pd.read_excel(
    data_file,
    header=start_row,
    usecols='A:G',
    names=['level', 'question', 'option_a', 'option_b', 'option_c', 'option_d', 'answer'],
)


def replace_quotes_and_dots(text):
    def replacement(match):
        nonlocal count
        quote = '«' if count % 2 == 0 else '»'
        count += 1
        return quote

    count = 0
    if not isinstance(text, str):
        return text
    return re.sub(r'"', replacement, text.replace('…', '...'))


data = data.map(replace_quotes_and_dots)

conn = sqlite3.connect('database.sqlite3')
cursor = conn.cursor()

count = 0
for _, row in data.iterrows():
    table_name = f'{row["level"]}_questions'

    answers = {'A': row['option_a'], 'B': row['option_b'], 'C': row['option_c'], 'D': row['option_d']}

    correct_answer = answers[row['answer']]
    other_answers = [answers[option] for option in answers if option != row['answer']]

    with suppress(Exception):
        cursor.execute(
            f'INSERT INTO "{table_name}" (text, answer_c, answer_2, answer_3, answer_4) VALUES (?, ?, ?, ?, ?)',
            (row['question'], correct_answer, *other_answers),
        )
        count += 1

conn.commit()
conn.close()
print(f'В базу данных добавлено {count} новых вопросов.')
