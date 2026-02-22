from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "super_secret_bidmate"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "bidmate.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# ------------------ MODEL ------------------

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    current_bid = db.Column(db.Float, default=0)
    category = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(200))
    is_barter = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------ ROUTES ------------------

@app.route("/")
def home():
    items = Item.query.filter_by(is_barter=False).order_by(Item.created_at.desc()).all()
    return render_template("index.html", items=items)

@app.route("/sell", methods=["GET", "POST"])
def sell():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        price = float(request.form["price"])
        category = request.form["category"]
        barter = True if request.form.get("barter") else False

        image_file = request.files["image"]
        image_filename = None

        if image_file:
            image_filename = image_file.filename
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_filename)
            image_file.save(image_path)

        new_item = Item(
            title=title,
            description=description,
            price=price,
            current_bid=price,
            category=category,
            image=image_filename,
            is_barter=barter
        )

        db.session.add(new_item)
        db.session.commit()

        flash("Item listed successfully!")
        return redirect(url_for("my_listings"))

    return render_template("sell.html")

@app.route("/bid/<int:item_id>", methods=["POST"])
def bid(item_id):
    item = Item.query.get_or_404(item_id)
    bid_amount = float(request.form["bid_amount"])

    if bid_amount > item.current_bid:
        item.current_bid = bid_amount
        db.session.commit()
        flash("Bid placed successfully!")
    else:
        flash("Bid must be higher than current bid.")

    return redirect(url_for("item_detail", item_id=item.id))

@app.route("/delete/<int:item_id>")
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Item deleted successfully!")
    return redirect(url_for("my_listings"))

@app.route("/categories")
def categories():
    categories_list = [
        "Books and notes",
        "Hostel essentials",
        "Electronic and gadget",
        "Arts and craft",
        "Project components",
        "Fashion and accessories",
        "Furniture and miscellaneous"
    ]
    items = Item.query.filter_by(is_barter=False).all()
    barter_items = Item.query.filter_by(is_barter=True).all()

    return render_template("categories.html",
                           categories=categories_list,
                           items=items,
                           barter_items=barter_items)

@app.route("/barter")
def barter():
    barter_items = Item.query.filter_by(is_barter=True).all()
    return render_template("barter.html", barter_items=barter_items)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("Message sent successfully!")
        return redirect(url_for("contact"))
    return render_template("contact.html")

@app.route("/my_listings")
def my_listings():
    items = Item.query.order_by(Item.created_at.desc()).all()
    return render_template("my_listings.html", items=items)

@app.route("/item/<int:item_id>")
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template("item_detail.html", item=item)

# ------------------ INIT ------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)