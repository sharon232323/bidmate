import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE_URL = os.environ.get("DATABASE_URL")

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ================= DATABASE CONNECTION =================

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


# ================= HOME =================

@app.route("/")
def home():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, title, description, image, owner_email, status FROM items ORDER BY id DESC")
    rows = cur.fetchall()

    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "image": row[3],
            "owner_email": row[4],
            "status": row[5]
        })

    cur.close()
    conn.close()

    return render_template("index.html", items=items)


# ================= SIGNUP =================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Try inserting directly
            cur.execute(
                "INSERT INTO users (email, password) VALUES (%s, %s)",
                (email, password)
            )
            conn.commit()

        except Exception:
            conn.rollback()
            flash("Email already registered. Please login instead.")
            cur.close()
            conn.close()
            return redirect(url_for("signup"))

        cur.close()
        conn.close()

        flash("Account created successfully!")
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
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session["user"] = email
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
        cur.execute(
            "INSERT INTO items (title, description, image, owner_email, status) VALUES (%s, %s, %s, %s, %s)",
            (title, description, filename, session["user"], "Available")
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("Item listed successfully!")
        return redirect(url_for("home"))

    return render_template("add_item.html")


# ================= MY LISTINGS =================

@app.route("/my_listings")
def my_listings():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, title, description, image, status FROM items WHERE owner_email=%s",
                (session["user"],))
    rows = cur.fetchall()

    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "image": row[3],
            "status": row[4]
        })

    cur.close()
    conn.close()

    return render_template("my_listings.html", items=items)


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

    flash("Item deleted successfully!")
    return redirect(url_for("my_listings"))


# ================= MAKE OFFER =================

@app.route("/make_offer/<int:item_id>", methods=["POST"])
def make_offer(item_id):
    if "user" not in session:
        return redirect(url_for("login"))

    offer_text = request.form["offer_text"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO offers (item_id, buyer_email, offer_text, status) VALUES (%s, %s, %s, %s)",
                (item_id, session["user"], offer_text, "Pending"))

    conn.commit()
    cur.close()
    conn.close()

    flash("Offer sent!")
    return redirect(url_for("home"))


# ================= VIEW OFFERS (SELLER ONLY) =================

@app.route("/view_offers/<int:item_id>")
def view_offers(item_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    # Check ownership
    cur.execute("SELECT owner_email FROM items WHERE id=%s", (item_id,))
    owner = cur.fetchone()

    if not owner or owner[0] != session["user"]:
        flash("Unauthorized access!")
        return redirect(url_for("home"))

    cur.execute("SELECT id, buyer_email, offer_text, status FROM offers WHERE item_id=%s", (item_id,))
    rows = cur.fetchall()

    offers = []
    for row in rows:
        offers.append({
            "id": row[0],
            "buyer_email": row[1],
            "offer_text": row[2],
            "status": row[3]
        })

    cur.close()
    conn.close()

    return render_template("offers.html", offers=offers)


# ================= ACCEPT OFFER =================

@app.route("/accept_offer/<int:offer_id>")
def accept_offer(offer_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("UPDATE offers SET status='Accepted' WHERE id=%s", (offer_id,))
    cur.execute("""
        UPDATE items
        SET status='Bartered'
        WHERE id = (SELECT item_id FROM offers WHERE id=%s)
    """, (offer_id,))

    conn.commit()
    cur.close()
    conn.close()

    flash("Offer accepted!")
    return redirect(url_for("home"))


# ================= REJECT OFFER =================

@app.route("/reject_offer/<int:offer_id>")
def reject_offer(offer_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("UPDATE offers SET status='Rejected' WHERE id=%s", (offer_id,))
    conn.commit()

    cur.close()
    conn.close()

    flash("Offer rejected!")
    return redirect(url_for("home"))


# ================= BUYER DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, offer_text, status FROM offers WHERE buyer_email=%s",
                (session["user"],))
    rows = cur.fetchall()

    offers = []
    for row in rows:
        offers.append({
            "id": row[0],
            "offer_text": row[1],
            "status": row[2]
        })

    cur.close()
    conn.close()

    return render_template("dashboard.html", offers=offers)


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)
