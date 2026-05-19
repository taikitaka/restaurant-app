from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DB_NAME = 'inventory.db'

# データベースの初期化（テーブルがなければ作る）
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                stock INTEGER DEFAULT 0,
                order_qty INTEGER DEFAULT 0,
                unit TEXT NOT NULL
            )
        ''')
        conn.commit()

# 最初の一回だけサンプルデータを入れる関数
def insert_sample_data():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ingredients")
        if cursor.fetchone()[0] == 0:
            samples = [
                ("野菜", "キャベツ", 2, 3, "玉"),
                ("野菜", "トマト", 0, 1, "箱"),
                ("肉類", "鶏もも肉", 5, 0, "kg")
            ]
            cursor.executemany("INSERT INTO ingredients (category, name, stock, order_qty, unit) VALUES (?, ?, ?, ?, ?)", samples)
            conn.commit()

@app.route('/')
def index():
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row  # 辞書型でデータを取得できるようにする
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ingredients")
        ingredients = cursor.fetchall()
    return render_template('index.html', ingredients=ingredients)

@app.route('/add', methods=['POST'])
def add_ingredient():
    name = request.form.get('name')
    category = request.form.get('category')
    unit = request.form.get('unit')
    
    if name:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ingredients (category, name, stock, order_qty, unit) VALUES (?, ?, 0, 0, ?)", (category, name, unit))
            conn.commit()
    return redirect(url_for('index'))

@app.route('/action/<int:item_id>', methods=['POST'])
def action(item_id):
    action_type = request.form.get('action_type')
    order_qty = int(request.form.get('order_qty', 0))
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        if action_type == 'order':
            # 発注数を更新
            cursor.execute("UPDATE ingredients SET order_qty = ? WHERE id = ?", (order_qty, item_id))
        elif action_type == 'deliver':
            # 納品：在庫 ＝ 現在の在庫 ＋ 発注数、発注数を0に戻す
            cursor.execute("UPDATE ingredients SET stock = stock + order_qty, order_qty = 0 WHERE id = ?", (item_id, item_id))
        conn.commit()
            
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    insert_sample_data()
    app.run(debug=True)