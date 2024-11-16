import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('server.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            '''CREATE TABLE IF NOT EXISTS users (
                                username TEXT PRIMARY KEY NOT NULL,
                                password TEXT NOT NULL,
                                balance INTEGER DEFAULT 0);''')
        self.cursor.execute(
            '''CREATE TABLE IF NOT EXISTS shop (
                                username TEXT,
                                order_item TEXT,
                                Logistics_Info TEXT,
                                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE);''')
        self.cursor.execute(
            '''CREATE TABLE IF NOT EXISTS game (
                                username TEXT PRIMARY KEY NOT NULL,
                                game_level INTEGER DEFAULT 1 NOT NULL,
                                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE);''')
        self.cursor.execute(
            '''CREATE TABLE IF NOT EXISTS game_own (
                                username TEXT,
                                game_item TEXT,
                                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE);''')

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

    def update_balance(self, username, balance):
        pr_balance = self.get_balance(username)
        balance_int = int(balance) + int(pr_balance)
        self.cursor.execute("UPDATE users SET balance = ? WHERE username = ?", (str(balance_int), username))
        self.conn.commit()

    def get_order_info(self, username):
        self.cursor.execute("SELECT order_item FROM shop WHERE username = ?", (username,))
        return self.cursor.fetchone()

    def get_logistics_info(self, username):
        self.cursor.execute("SELECT Logistics_Info FROM shop WHERE username = ?", (username,))
        return self.cursor.fetchone()

    def get_game_info(self, username):
        self.cursor.execute("SELECT game_level FROM game WHERE username = ?", (username,))
        info_str = self.cursor.fetchone()
        self.cursor.execute("SELECT game_item FROM game_own WHERE username = ?", (username,))
        info_str += self.cursor.fetchone()
        return info_str

    @staticmethod
    def get_game_fes_info():
        return """活动「游戏开发部的一日女仆」已经开启！活动期间，限定角色「才羽桃井（女仆）」、「才羽绿（女仆）」、「天童爱丽丝（女仆）」的卡池概率提升！
                参与活动更可获得限定角色「花冈柚子（女仆）」与千年科技学院学生角色升级材料"""

# 数据库测试桩
if __name__ == '__main__':
    db = Database()
    input_str = input()
    if input_str.startswith("_login"):
        t_username, t_password = input_str.split()[1:]
        print(t_username, t_password)
        print(db.password_match(t_username, t_password))
    elif input_str.startswith("_register"):
        t_username, t_password = input_str.split()[1:]
        db.add_user(t_username, t_password)
    elif input_str.startswith("_balance"):
        t_username = input_str.split()[1]
        print(db.get_balance(t_username))
    elif input_str.startswith("_order"):
        t_username = input_str.split()[1]
        print(db.get_order_info(t_username))
    elif input_str.startswith("_logistics"):
        t_username = input_str.split()[1]
        print(db.get_logistics_info(t_username))
    elif input_str.startswith("_game"):
        t_username = input_str.split()[1]
        print(db.get_game_info(t_username))
    db.close()