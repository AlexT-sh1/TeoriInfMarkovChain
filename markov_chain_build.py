from collections import defaultdict
import psycopg2
import sys
import time


def normalize_text(text):

    text = text.lower()
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

    allowed_chars = set()

    russian_alphabet = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    for char in russian_alphabet:
        allowed_chars.add(char)

    special_chars = ' .,!?'
    for char in special_chars:
        allowed_chars.add(char)

    filtered_text = []
    for char in text:
        if char in allowed_chars:
            filtered_text.append(char)

    result = ''.join(filtered_text)

    while '  ' in result:
        result = result.replace('  ', ' ')

    return result.strip()


def create_and_save_markov_chains(text, db_params, max_length=14):

    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    cursor.execute("""
        DROP TABLE IF EXISTS markov_chains;
        CREATE TABLE markov_chains (
            id SERIAL PRIMARY KEY,
            chain_length INTEGER NOT NULL,
            state VARCHAR(50) NOT NULL,
            next_char CHAR(1) NOT NULL,
            probability DOUBLE PRECISION NOT NULL,
            state_length INTEGER GENERATED ALWAYS AS (CHAR_LENGTH(state)) STORED
        );
    """)

    conn.commit()

    for length in range(1, max_length + 1):
        print(f"\nСОЗДАНИЕ ЦЕПИ ДЛИНОЙ {length}")
        transitions = defaultdict(lambda: defaultdict(int))

        for i in range(len(text) - length):
            state = text[i:i + length]
            next_char = text[i + length]
            transitions[state][next_char] += 1

        probabilities = {}
        for state, next_chars in transitions.items():
            total = sum(next_chars.values())
            probabilities[state] = {
                char: count / total
                for char, count in next_chars.items()
            }

        print(f"Цепь создана")

        print(f"ЗАПИСЬ ЦЕПИ ДЛИНОЙ {length} В ТАБЛИЦУ")

        data_to_insert = []
        for state, next_chars in probabilities.items():
            for next_char, probability in next_chars.items():
                data_to_insert.append((length, state, next_char, probability))

        if data_to_insert:
            cursor.executemany(
                """INSERT INTO markov_chains (chain_length, state, next_char, probability) 
                   VALUES (%s, %s, %s, %s)""",
                data_to_insert
            )
            conn.commit()

        print(f"Цепь загружена в базу")

    cursor.execute("""
            CREATE INDEX idx_markov_main ON markov_chains(chain_length, state);
        """)

    cursor.execute("""
            CREATE INDEX idx_markov_state ON markov_chains(state);
        """)
    conn.commit()
    cursor.close()
    conn.close()

    return True


def main():

    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'markov_db',
        'user': 'postgres',
        'password': 'dcgbjm97'
    }

    with open('teorinf_1.txt', 'r', encoding='utf-8') as f:
        original_text = f.read()
    normalized_text = normalize_text(original_text)

    create_and_save_markov_chains(
        normalized_text,
        DB_CONFIG,
        max_length=14
    )


if __name__ == "__main__":
    main()