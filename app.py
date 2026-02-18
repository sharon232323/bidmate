from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ================= DATABASE CONNECTION =================

def get_db():
    conn = sqlite3.connect("database.db", timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ================= INITIALIZE DATABASE =================

def init_db():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        profile_pic TEXT DEFAULT 'default.png'
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        image TEXT,
        owner TEXT,
        status TEXT DEFAULT 'Available'
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        buyer_email TEXT,
        message TEXT,
        status TEXT DEFAULT 'Pending'
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ================= HOME =================

@app.route("/")
def home():
    conn = get_db()
    items = conn.execute(
        "SELECT * FROM items WHERE status='Available'"
    ).fetchall()
    conn.close()
    return render_template("index.html", items=items)


# ================= SIGNUP =================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users (email,password) VALUES (?,?)",
                (email, password)
            )
            conn.commit()
            conn.close()
            flash("Account created! Please login.")
            return redirect("/login")

        except sqlite3.IntegrityError:
            flash("Email already exists.")
            return redirect("/signup")

    return render_template("signup.html")


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()
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

        if not image_file or image_file.filename == "":
            return "Please upload an image"

        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image_file.save(image_path)

        conn = get_db()
        conn.execute("""
            INSERT INTO items (title, description, image, owner)
            VALUES (?, ?, ?, ?)
        """, (title, description, filename, session["user"]))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add_item.html")


# ================= ITEM DETAIL =================

@app.route("/item/<int:item_id>")
def item_detail(item_id):
    conn = get_db()

    item = conn.execute(
        "SELECT * FROM items WHERE id=?",
        (item_id,)
    ).fetchone()

    offers = conn.execute(
        "SELECT * FROM offers WHERE item_id=?",
        (item_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "item_detail.html",
        item=item,
        offers=offers
    )


# ================= MAKE OFFER =================

@app.route("/make_offer/<int:item_id>", methods=["POST"])
def make_offer(item_id):
    if "user" not in session:
        return redirect("/login")

    message = request.form["message"]

    conn = get_db()
    conn.execute("""
        INSERT INTO offers (item_id, buyer_email, message)
        VALUES (?, ?, ?)
    """, (item_id, session["user"], message))

    conn.commit()
    conn.close()

    return redirect(f"/item/{item_id}")


# ================= ACCEPT OFFER =================

@app.route("/accept_offer/<int:offer_id>")
def accept_offer(offer_id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()

    offer = conn.execute(
        "SELECT * FROM offers WHERE id=?",
        (offer_id,)
    ).fetchone()

    item = conn.execute(
        "SELECT * FROM items WHERE id=?",
        (offer["item_id"],)
    ).fetchone()

    # Only seller can accept
    if item["owner"] != session["user"]:
        conn.close()
        return "Unauthorized"

    # Accept this offer
    conn.execute(
        "UPDATE offers SET status='Accepted' WHERE id=?",
        (offer_id,)
    )

    # Reject other offers
    conn.execute(
        "UPDATE offers SET status='Rejected' WHERE item_id=? AND id!=?",
        (offer["item_id"], offer_id)
    )

    # Mark item as Bartered
    conn.execute(
        "UPDATE items SET status='Bartered' WHERE id=?",
        (offer["item_id"],)
    )

    conn.commit()
    conn.close()

    return redirect(f"/item/{offer['item_id']}")


# ================= REJECT OFFER =================

@app.route("/reject_offer/<int:offer_id>")
def reject_offer(offer_id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()

    offer = conn.execute(
        "SELECT * FROM offers WHERE id=?",
        (offer_id,)
    ).fetchone()

    item = conn.execute(
        "SELECT * FROM items WHERE id=?",
        (offer["item_id"],)
    ).fetchone()

    if item["owner"] != session["user"]:
        conn.close()
        return "Unauthorized"

    conn.execute(
        "UPDATE offers SET status='Rejected' WHERE id=?",
        (offer_id,)
    )

    conn.commit()
    conn.close()

    return redirect(f"/item/{offer['item_id']}")


# ================= BUYER DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()

    my_offers = conn.execute("""
        SELECT offers.*, items.title
        FROM offers
        JOIN items ON offers.item_id = items.id
        WHERE buyer_email=?
    """, (session["user"],)).fetchall()

    conn.close()

    return render_template("dashboard.html", offers=my_offers)


# ================= PROFILE =================

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()

    if request.method == "POST":
        file = request.files["profile_pic"]

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            conn.execute("""
                UPDATE users SET profile_pic=?
                WHERE email=?
            """, (filename, session["user"]))

            conn.commit()

    user = conn.execute(
        "SELECT * FROM users WHERE email=?",
        (session["user"],)
    ).fetchone()

    conn.close()

    return render_template("profile.html", user=user)


# ================= CONTACT =================

@app.route("/contact")
def contact():
    return render_template("contact.html")


# ================= RENDER DEPLOY =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
