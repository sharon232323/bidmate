import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

DATABASE_URL = os.environ.get("DATABASE_URL")


# ================= DATABASE CONNECTION =================

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


# ================= AUTO CREATE TABLES =================

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(200) NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id SERIAL PRIMARY KEY,
        title VARCHAR(200),
        description TEXT,
        image VARCHAR(200),
        owner_id INTEGER REFERENCES users(id),
        status VARCHAR(50) DEFAULT 'Available'
    );
    """)

    conn.commit()
    cur.close()
    conn.close()


with app.app_context():
    create_tables()


# ================= HOME =================

@app.route("/")
def home():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items ORDER BY id DESC")
    items = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("dashboard.html", items=items)


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, password)
            )
            conn.commit()
            flash("Registered successfully! Please login.")
            return redirect(url_for("login"))
        except:
            flash("Username or Email already exists.")
        finally:
            cur.close()
            conn.close()

    return render_template("register.html")


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Login successful!")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials")

    return render_template("login.html")


# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect(url_for("home"))


# ================= ADD ITEM =================

@app.route("/add_item", methods=["GET", "POST"])
def add_item():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        image_file = request.files["image"]

        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image_file.save(image_path)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO items (title, description, image, owner_id) VALUES (%s, %s, %s, %s)",
            (title, description, filename, session["user_id"])
        )

        conn.commit()
        cur.close()
        conn.close()

        flash("Item added successfully!")
        return redirect(url_for("home"))

    return render_template("add_item.html")


# ================= ITEM DETAIL =================

@app.route("/item/<int:item_id>")
def item_detail(item_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE id=%s", (item_id,))
    item = cur.fetchone()
    cur.close()
    conn.close()

    return render_template("item_detail.html", item=item)


# ================= MY LISTINGS =================

@app.route("/my_listings")
def my_listings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM items WHERE owner_id=%s ORDER BY id DESC",
        (session["user_id"],)
    )
    items = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("my_listings.html", items=items)


# ================= DELETE ITEM =================

@app.route("/delete_item/<int:item_id>")
def delete_item(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM items WHERE id=%s AND owner_id=%s",
        (item_id, session["user_id"])
    )

    conn.commit()
    cur.close()
    conn.close()

    flash("Item deleted successfully.")
    return redirect(url_for("my_listings"))


# ================= BARTER =================

@app.route("/barter/<int:item_id>")
def barter_item(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE items SET status='Bartered' WHERE id=%s",
        (item_id,)
    )

    conn.commit()
    cur.close()
    conn.close()

    flash("Item marked as Bartered!")
    return redirect(url_for("home"))


@app.route("/barter")
def barter_page():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE status='Bartered'")
    items = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("barter.html", items=items)


# ================= PROFILE =================

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("profile.html")


# ================= CONTACT =================

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("Message sent successfully!")
        return redirect(url_for("contact"))

    return render_template("contact.html")


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)
