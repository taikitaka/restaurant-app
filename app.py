import os
from flask import Flask, render_template, request, redirect
import psycopg2
from psycopg2.extras import DictCursor

app = Flask(__name__)

# 👑 データベース接続関数
def get_db_connection():
    DATABASE_URL = "postgresql://restaurant_db_4ntk_user:Gk3pldNQ6ngxL5lbMWek5zYSMZ5aJnfl@dpg-d85ts5f7f7vs73dfrfu0-a.oregon-postgres.render.com/restaurant_db_4ntk"
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

# 👑 初回起動時にテーブルを用意する
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 食材テーブル
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id SERIAL PRIMARY KEY,
            category TEXT,
            name TEXT,
            stock INTEGER DEFAULT 0,
            unit TEXT DEFAULT '個',
            order_qty INTEGER DEFAULT 0,
            status TEXT DEFAULT '未発注'
        );
    ''')
    
    # 取引先テーブル
    cur.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            name TEXT,
            phone TEXT,
            note TEXT
        );
    ''')
    
    # カラムの追加確認
    try:
        cur.execute("ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS status TEXT DEFAULT '未発注';")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS unit TEXT DEFAULT '個';")
    except Exception:
        pass

    conn.commit()
    cur.close()
    conn.close()

init_db()

# 🏠 トップ画面（一覧表示）
@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    cur.execute('SELECT * FROM ingredients ORDER BY id ASC;')
    ingredients = cur.fetchall()
    
    cur.execute('SELECT * FROM contacts ORDER BY id ASC;')
    contacts = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('index.html', ingredients=ingredients, contacts=contacts)

# ➕ 食材の追加（methods に修正しました！）
@app.route('/add', methods=['POST'])
def add_ingredient():
    category = request.form['category']
    name = request.form['name']
    unit = request.form['unit']
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO ingredients (category, name, unit, stock, order_qty, status) VALUES (%s, %s, %s, 0, 0, '未発注');",
        (category, name, unit)
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

# ➕ 取引先の追加（methods に修正しました！）
@app.route('/add_contact', methods=['POST'])
def add_contact():
    name = request.form['name']
    phone = request.form['phone']
    note = request.form['note']
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO contacts (name, phone, note) VALUES (%s, %s, %s);', (name, phone, note))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

# 🔄 各食材のアクションを一括受付（methods に修正しました！）
@app.route('/action/<int:item_id>', methods=['POST'])
def handle_action(item_id):
    action_type = request.form.get('action_type')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    if action_type == 'update_ingredient':
        stock = request.form.get('stock', 0)
        unit = request.form.get('unit', '個')
        order_qty = request.form.get('order_qty', 0)
        
        cur.execute(
            'UPDATE ingredients SET stock = %s, unit = %s, order_qty = %s WHERE id = %s;',
            (stock, unit, order_qty, item_id)
        )
        
    elif action_type == 'ordered':
        order_qty = request.form.get('order_qty', 0)
        cur.execute(
            "UPDATE ingredients SET status = '発注済み', order_qty = %s WHERE id = %s;",
            (order_qty, item_id)
        )
        
    elif action_type == 'deliver':
        order_qty = int(request.form.get('order_qty', 0))
        cur.execute(
            "UPDATE ingredients SET stock = stock + %s, order_qty = 0, status = '未発注' WHERE id = %s;",
            (order_qty, item_id)
        )
        
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

# 🗑️ 食材の削除機能を追加
@app.route('/action/delete/<int:item_id>', methods=['POST'])
def delete_ingredient(item_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 指定されたIDの食材をデータベースから削除するSQL
    cur.execute('DELETE FROM ingredients WHERE id = %s;', (item_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)