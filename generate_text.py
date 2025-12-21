import psycopg2
import random

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'markov_db',
    'user': 'postgres',
    'password': 'dcgbjm97'
}


while True:
    try:
        temp_input = input("\nТемпература (0.1-2.0, Enter=1.0): ").strip()
        if not temp_input:
            temperature = 1.0
        else:
            temperature = float(temp_input)

        print(f"\nГенерация с температурой {temperature}...")

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        text = " "
        state = text
        for i in range(500):
            found = False
            for length in range(min(len(state), 14), 0, -1):
                current_state = state[-length:]

                cursor.execute("""
                    SELECT next_char, probability 
                    FROM markov_chains 
                    WHERE chain_length = %s AND state = %s
                """, (length, current_state))

                results = cursor.fetchall()

                if results:
                    chars = [r[0] for r in results]
                    probs = [r[1] for r in results]
                    if temperature < 1.0:
                        max_prob = max(probs)
                        best_chars = [char for char, prob in zip(chars, probs) if prob == max_prob]
                        next_char = random.choice(best_chars)
                    elif temperature > 1.0:
                        next_char = random.choice(chars)
                    else:
                        rand = random.random()
                        cum_prob = 0
                        for char, prob in zip(chars, probs):
                            cum_prob += prob
                            if rand <= cum_prob:
                                next_char = char
                                break
                        else:
                            next_char = chars[-1]

                    text += next_char
                    state = text[-14:]
                    found = True
                    break

            if not found:
                text += " "
                state = text[-14:]

        cursor.close()
        conn.close()

        if text:
            text = text[0].upper() + text[1:]
            if text[-1] not in '.!?':
                text += '.'

        print(text)
        choice = input("\nСгенерировать еще? (y/n): ").lower()
        if choice != 'y':
            print("Выход")
            break

    except ValueError:
        print("Ошибка: введите число")
    except KeyboardInterrupt:
        print("\nВыход")
        break
    except Exception as e:
        print(f"Ошибка: {e}")
        break