from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

DATABASE = "bidmate.db"

# Initialize database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        price REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

init_db()

# Home Page
@app.route("/")
def home():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items ORDER BY id DESC")
    items = cursor.fetchall()
    conn.close()
    return render_template("index.html", items=items)

# Add Item
@app.route("/add-item", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        title = request.form.get("title")
        price = request.form.get("price")
        category = request.form.get("category")
        description = request.form.get("description")

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO items (title, price, category, description)
            VALUES (?, ?, ?, ?)
        """, (title, price, category, description))
        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    return render_template("add_item.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

if __name__ == "__main__":
    app.run(debug=True)
