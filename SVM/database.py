import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('server.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            '''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, balance INTEGER DEFAULT 0)''')

    def close(self):
        self.conn.close()

    def user_exist(self, username):
        self.cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return self.cursor.fetchone() is not None

    def add_user(self, username, password):
        self.cursor.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, 0)", (username, password))
        self.conn.commit()

    def password_match(self, username, password):
        self.cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        return self.cursor.fetchone() is not None


    def get_balance(self, username):
        self.cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
        return self.cursor.fetchone()[0]