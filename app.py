from flask import Flask, render_template, request, redirect, session, flash
import psycopg2
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

DATABASE_URL = os.environ.get("DATABASE_URL")


# ================= DB CONNECTION =================

def get_db():
    return psycopg2.connect(DATABASE_URL)


# ================= INIT TABLES =================

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE,
        password TEXT,
        profile_pic TEXT DEFAULT 'default.png'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id SERIAL PRIMARY KEY,
        title TEXT,
        description TEXT,
        image TEXT,
        owner TEXT,
        status TEXT DEFAULT 'Available'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS offers (
        id SERIAL PRIMARY KEY,
        item_id INTEGER,
        buyer_email TEXT,
        message TEXT,
        status TEXT DEFAULT 'Pending'
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


init_db()


# ================= HOME =================

@app.route("/")
def home():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE status='Available'")
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", items=items)


# ================= SIGNUP =================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (email,password) VALUES (%s,%s)",
                (email, password)
            )
            conn.commit()
            cur.close()
            conn.close()
            flash("Account created! Please login.")
            return redirect("/login")

        except Exception:
            flash("Email already exists.")
            return redirect("/signup")

    return render_template("signup.html")


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session["user"] = email
            return redirect("/")
        else:
            flash("Invalid credentials.")
            return redirect("/login")

    return render_template("login.html")


# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= ADD ITEM =================

@app.route("/add_item", methods=["GET", "POST"])
def add_item():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        image_file = request.files.get("image")

        filename = "default.png"

        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO items (title, description, image, owner)
            VALUES (%s, %s, %s, %s)
        """, (title, description, filename, session["user"]))
        conn.commit()
        cur.close()
        conn.close()

        return redirect("/")

    return render_template("add_item.html")


# ================= ITEM DETAIL =================

@app.route("/item/<int:item_id>")
def item_detail(item_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM items WHERE id=%s", (item_id,))
    item = cur.fetchone()

    cur.execute("SELECT * FROM offers WHERE item_id=%s", (item_id,))
    offers = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("item_detail.html", item=item, offers=offers)


# ================= MAKE OFFER =================

@app.route("/make_offer/<int:item_id>", methods=["POST"])
def make_offer(item_id):
    if "user" not in session:
        return redirect("/login")

    message = request.form.get("message")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO offers (item_id, buyer_email, message)
        VALUES (%s, %s, %s)
    """, (item_id, session["user"], message))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/item/{item_id}")

# ================= DELETE ITEM =================

@app.route("/delete_item/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    # Check item ownership
    cur.execute("SELECT owner FROM items WHERE id=%s", (item_id,))
    item = cur.fetchone()

    if not item:
        cur.close()
        conn.close()
        return "Item not found"

    if item[0] != session["user"]:
        cur.close()
        conn.close()
        return "Unauthorized"

    # Delete related offers first
    cur.execute("DELETE FROM offers WHERE item_id=%s", (item_id,))

    # Delete item
    cur.execute("DELETE FROM items WHERE id=%s", (item_id,))

    conn.commit()
    cur.close()
    conn.close()

    flash("Item deleted successfully.")
    return redirect("/")


if __name__ == "__main__":
    app.run()
