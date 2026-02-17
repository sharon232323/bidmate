from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------- DATABASE INIT ----------
def init_db():
    conn = sqlite3.connect("database.db")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        bio TEXT,
        profile_pic TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price TEXT,
        description TEXT,
        image TEXT,
        seller_email TEXT,
        status TEXT DEFAULT 'Available'
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS barter_offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        offered_by TEXT,
        offered_item TEXT,
        message TEXT,
        status TEXT DEFAULT 'Pending'
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- HOME ----------
@app.route("/")
def home():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    items = conn.execute("SELECT * FROM items WHERE status='Available'").fetchall()
    conn.close()
    return render_template("index.html", items=items)

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = sqlite3.connect("database.db")
        conn.execute("INSERT INTO users (email,password) VALUES (?,?)",(email,password))
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
        conn = sqlite3.connect("database.db")
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?",(email,password)).fetchone()
        conn.close()
        if user:
            session["user_email"] = email
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- ADD ITEM ----------
@app.route("/add_item", methods=["GET","POST"])
def add_item():
    if "user_email" not in session:
        return redirect("/login")

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        description = request.form["description"]
        image = request.files["image"]

        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = sqlite3.connect("database.db")
        conn.execute("""
        INSERT INTO items (name,price,description,image,seller_email)
        VALUES (?,?,?,?,?)
        """,(name,price,description,filename,session["user_email"]))
        conn.commit()
        conn.close()
        return redirect("/")

    return render_template("add_item.html")

# ---------- ITEM DETAIL ----------
@app.route("/item/<int:item_id>")
def item_detail(item_id):
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    item = conn.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
    conn.close()
    return render_template("item_detail.html", item=item)

# ---------- PROFILE ----------
@app.route("/profile", methods=["GET","POST"])
def profile():
    if "user_email" not in session:
        return redirect("/login")

    email = session["user_email"]
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    if request.method == "POST":
        bio = request.form["bio"]
        profile_pic = request.files["profile_pic"]

        filename = None
        if profile_pic and profile_pic.filename != "":
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            conn.execute("UPDATE users SET bio=?, profile_pic=? WHERE email=?",(bio,filename,email))
        else:
            conn.execute("UPDATE users SET bio=? WHERE email=?",(bio,email))
        conn.commit()

    user = conn.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
    conn.close()
    return render_template("profile.html", user=user)

if __name__ == "__main__":
    app.run(debug=True)
