import requests
import json
import sqlite3

# Настройка базы данных
conn = sqlite3.connect('cities.db')
cursor = conn.cursor()

# Создание таблицы, если она не существует
cursor.execute('''CREATE TABLE IF NOT EXISTS cities (
                    id_city INTEGER PRIMARY KEY,
                    city_name TEXT NOT NULL
                )''')

id_city_to = 2  # Minsk
bool_list = [False] * 500

def insert_city(id_city, city_name):
    cursor.execute('''INSERT OR IGNORE INTO cities (id_city, city_name) VALUES (?, ?)''', (id_city, city_name))
    conn.commit()  # Сохраняем изменения

def analyze_string(input_string):
    try:
        cities = json.loads(input_string)

        # Проверка наличия данных
        if 'stops_start' in cities and cities['stops_start']:
            city_info = cities['stops_start'][0]
            id_city = int(city_info['id_city'])
            city_name = city_info['city_name']

            if not bool_list[id_city]:
                print(f"{id_city}: {city_name}")
                insert_city(id_city, city_name)  # Сохраним город в базу данных
                bool_list[id_city] = True

    except (json.JSONDecodeError, IndexError) as e:
        print(f"Parsing error: {e}")

# Основной цикл
for j in range(1, 350):
    for i in range(1, 350):
        try:
            url = f"https://smilebus.by/api/v2/route/schedule-detail?id_city_from={i}&id_city_to={j}&date=18.05.2024"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                str2 = response.text
                analyze_string(str2)
            else:
                print(f"Error: {response.status_code} for {url}")

        except Exception as e:
            print(f"Error during request: {e}")

# Закрываем соединение с базой данных
conn.close()