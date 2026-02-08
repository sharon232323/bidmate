import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# -------------------------
# Database configuration
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bidmate.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# Initialize DB on startup
init_db()

# -------------------------
# Routes
# -------------------------

@app.route("/")
def index():
    conn = get_db_connection()
    items = conn.execute("SELECT * FROM items").fetchall()
    conn.close()
    return render_template("index.html", items=items)


@app.route("/add", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO items (name, price) VALUES (?, ?)",
            (name, price)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    return render_template("add_item.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")
# -------------------------
# App runner
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)