import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE_URL = os.environ.get("DATABASE_URL")

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


# ================= HOME =================

@app.route("/")
def home():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items ORDER BY id DESC")
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", items=items)


# ================= SIGNUP =================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
            conn.commit()
        except:
            conn.rollback()
            flash("Email already registered.")
            cur.close()
            conn.close()
            return redirect(url_for("signup"))

        cur.close()
        conn.close()

        flash("Account created. Please login.")
        return redirect(url_for("login"))

    return render_template("signup.html")


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = user["email"]
            flash("Login successful.")
            return redirect(url_for("home"))

        flash("Invalid credentials.")
        return redirect(url_for("login"))

    return render_template("login.html")


# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for("home"))


# ================= ADD ITEM =================

@app.route("/add_item", methods=["GET", "POST"])
def add_item():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        image = request.files["image"]

        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO items (title, description, image, owner_email, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, description, filename, session["user"], "Available"))
        conn.commit()
        cur.close()
        conn.close()

        flash("Item added successfully.")
        return redirect(url_for("home"))

    return render_template("add_item.html")


# ================= DELETE ITEM =================

@app.route("/delete_item/<int:item_id>")
def delete_item(item_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE id=%s AND owner_email=%s",
                (item_id, session["user"]))
    conn.commit()
    cur.close()
    conn.close()

    flash("Item deleted.")
    return redirect(url_for("my_listings"))


# ================= MY LISTINGS =================

@app.route("/my_listings")
def my_listings():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE owner_email=%s", (session["user"],))
    items = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("my_listings.html", items=items)


# ================= MAKE OFFER =================

@app.route("/make_offer/<int:item_id>", methods=["POST"])
def make_offer(item_id):
    if "user" not in session:
        return redirect(url_for("login"))

    offer_text = request.form["offer_text"]

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO offers (item_id, buyer_email, offer_text, status)
        VALUES (%s, %s, %s, %s)
    """, (item_id, session["user"], offer_text, "Pending"))
    conn.commit()
    cur.close()
    conn.close()

    flash("Offer sent.")
    return redirect(url_for("home"))


# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM offers WHERE buyer_email=%s", (session["user"],))
    offers = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("dashboard.html", offers=offers)


if __name__ == "__main__":
    app.run(debug=True)
