from flask import Flask, render_template, request, redirect, url_for
import os
import psycopg2
from psycopg2.extras import DictCursor

app = Flask(__name__)

# 🔑 Renderのデータベース接続URLを取得する（ローカル検証用のバックアップ付き）
# 先ほどコピーした Internal Database URL を、"" の中（第二引数）に貼り付けてください！
DATABASE_URL = os.environ.get('DATABASE_URL', "postgresql://restaurant_db_4ntk_user:Gk3pldNQ6ngxL5lbMWek5zYSMZ5aJnfl@dpg-d85ts5f7f7vs73dfrfu0-a/restaurant_db_4ntk")

# データベースに接続する共通の関数
def get_db_connection():
    # PostgreSQLへの接続（辞書型でデータを扱えるように設定）
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# データベースの初期化（テーブルがなければ作る）
def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # 1. 食材用のテーブル（既存）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ingredients (
                    id SERIAL PRIMARY KEY,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    stock INTEGER DEFAULT 0,
                    order_qty INTEGER DEFAULT 0,
                    unit TEXT NOT NULL
                )
            ''')
            
            # 2. 📞 取引先（宛先）用の新しいテーブルを追加！
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,        -- 取引先の名（〇〇八百屋 など）
                    phone TEXT,                -- 電話番号
                    note TEXT                  -- メモ（LINEのリンクや担当者名など）
                )
            ''')
            conn.commit()

# 最初の一回だけサンプルデータを入れる関数
def insert_sample_data():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM ingredients")
            if cursor.fetchone()[0] == 0:
                samples = [
                    ("野菜", "キャベツ", 2, 3, "玉"),
                    ("野菜", "トマト", 0, 1, "箱"),
                    ("肉類", "鶏もも肉", 5, 0, "kg")
                ]
                for sample in samples:
                    cursor.execute(
                        "INSERT INTO ingredients (category, name, stock, order_qty, unit) VALUES (%s, %s, %s, %s, %s)",
                        sample
                    )
                conn.commit()

@app.route('/')
def index():
    with get_db_connection() as conn:
        # DictCursorを使って、sqlite3のRowと同じように辞書型で取得
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT * FROM ingredients ORDER BY id ASC")
            ingredients = cursor.fetchall()
    return render_template('index.html', ingredients=ingredients)

@app.route('/add', methods=['POST'])
def add_ingredient():
    name = request.form.get('name')
    category = request.form.get('category')
    unit = request.form.get('unit')
    
    if name:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # SQLiteの '?' から PostgreSQLの '%s' へプレースホルダーを変更
                cursor.execute(
                    "INSERT INTO ingredients (category, name, stock, order_qty, unit) VALUES (%s, %s, 0, 0, %s)",
                    (category, name, unit)
                )
                conn.commit()
    return redirect(url_for('index'))

@app.route('/action/<int:item_id>', methods=['POST'])
def action(item_id):
    action_type = request.form.get('action_type')
    order_qty = int(request.form.get('order_qty', 0))
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            if action_type == 'order':
                # 発注数を更新
                cursor.execute("UPDATE ingredients SET order_qty = %s WHERE id = %s", (order_qty, item_id))
            elif action_type == 'deliver':
                # 納品：在庫 ＝ 現在の在庫 ＋ 発注数、発注数を0に戻す
                cursor.execute("UPDATE ingredients SET stock = stock + order_qty, order_qty = 0 WHERE id = %s", (item_id,))
            conn.commit()
            
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    insert_sample_data()
    # Render環境のポートに自動対応させる設定
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)