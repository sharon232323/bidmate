from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)
DATABASE = "items.db"

# ---------- DATABASE INIT ----------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- HOME ----------
@app.route("/")
def home():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM items ORDER BY id DESC")
    items = cursor.fetchall()

    conn.close()
    return render_template("index.html", items=items)

# ---------- ADD ITEM ----------
@app.route("/add-item", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        category = request.form["category"]
        description = request.form["description"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO items (name, price, category, description)
            VALUES (?, ?, ?, ?)
        """, (name, price, category, description))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add_item.html")

# ---------- PRODUCT DETAIL ----------
@app.route("/item/<int:item_id>")
def item_detail(item_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()

    conn.close()

    if item is None:
        return "Item not found"

    return render_template("item_detail.html", item=item)

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        """, (username, email, password))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users WHERE email = ? AND password = ?
        """, (email, password))

        user = cursor.fetchone()
        conn.close()

        if user:
            return redirect("/")
        else:
            return "Invalid credentials"

    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)
