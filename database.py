import sqlite3

def init_db():
	conn = sqlite3.connect('pet_data.db')
	cursor = conn.cursor()
	cursor.execute('''CREATE TABLE IF NOT EXISTS pets
		(user_id INTEGER PRIMARY KEY,
		pet_name TEXT DEFAULT 'Livestock Pet',
		weight FLOAT DEFAULT 150.0,
		calories_today INTEGER DEFAULT 0,
		last_fed DATE DEFAULT NULL)''')
	conn.commit()
	conn.close()

init_db()