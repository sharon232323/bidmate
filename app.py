import sqlite3

def init_db():
    conn = sqlite3.connect("bidmate.db")
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
    from flask import Flask, render_template, request, redirect
    import sqlite3

app = Flask(__name__)
init_db

# ---------- DATABASE ----------
def get_db_connection():
    conn = sqlite3.connect("bidmate.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    conn = get_db_connection()
    items = conn.execute("SELECT * FROM items").fetchall()
    conn.close()
    return render_template("index.html", items=items)

@app.route("/add", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        title = request.form["title"]
        price = request.form["price"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO items (title, price) VALUES (?, ?)",
            (title, price)
        )
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add_item.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)