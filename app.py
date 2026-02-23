import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from extensions import db, login_manager
from models import User, Item, Bid, Contact

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)

# Create database
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==============================
# HOME
# ==============================
@app.route("/")
def home():
    items = Item.query.order_by(Item.created_at.desc()).all()
    return render_template("home.html", items=items)


# ==============================
# SIGNUP
# ==============================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        year = request.form["year"]
        department = request.form["department"]
        id_card_file = request.files["id_card"]

        filename = secure_filename(id_card_file.filename)
        id_card_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        user = User(
            name=name,
            email=email,
            password=password,
            year=year,
            department=department,
            id_card=filename
        )

        # YOU are super admin
        if email == app.config["SUPER_ADMIN_EMAIL"]:
            user.is_admin = True
            user.is_approved = True

        db.session.add(user)
        db.session.commit()

        flash("Signup successful! Await admin approval.")
        return redirect(url_for("login"))

    return render_template("signup.html")


# ==============================
# LOGIN
# ==============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if not user.is_approved:
                flash("Account awaiting admin approval.")
                return redirect(url_for("login"))

            login_user(user)
            return redirect(url_for("home"))

        flash("Invalid credentials")

    return render_template("login.html")


# ==============================
# LOGOUT
# ==============================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# ==============================
# PROFILE
# ==============================
@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


# ==============================
# ROLE SWITCH
# ==============================
@app.route("/switch_role")
@login_required
def switch_role():
    if current_user.role == "buyer":
        current_user.role = "seller"
    else:
        current_user.role = "buyer"

    db.session.commit()
    return redirect(url_for("profile"))


# ==============================
# SELL ITEM
# ==============================
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        price = float(request.form["price"])
        category = request.form["category"]
        is_barter = True if request.form.get("barter") else False
        image_file = request.files["image"]

        filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        item = Item(
            title=title,
            description=description,
            price=price,
            category=category,
            image=filename,
            is_barter=is_barter,
            seller_id=current_user.id
        )

        db.session.add(item)
        db.session.commit()

        flash("Item listed successfully!")
        return redirect(url_for("sell"))

    return render_template("sell.html")


# ==============================
# DELETE ITEM
# ==============================
@app.route("/delete_item/<int:item_id>")
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)

    if item.seller_id == current_user.id or current_user.is_admin:
        db.session.delete(item)
        db.session.commit()

    return redirect(url_for("sell"))


# ==============================
# CATEGORIES
# ==============================
@app.route("/categories")
def categories():
    items = Item.query.all()
    return render_template("categories.html", items=items)


# ==============================
# BARTER ZONE
# ==============================
@app.route("/barter")
def barter():
    items = Item.query.filter_by(is_barter=True).all()
    return render_template("barter.html", items=items)


# ==============================
# ITEM DETAIL + BIDDING
# ==============================
@app.route("/item/<int:item_id>", methods=["GET", "POST"])
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    bids = Bid.query.filter_by(item_id=item_id).order_by(Bid.amount.desc()).all()

    highest_bid = bids[0].amount if bids else item.price

    if request.method == "POST":
        if not current_user.is_authenticated:
            return redirect(url_for("login"))

        bid_amount = float(request.form["bid_amount"])

        if bid_amount > highest_bid:
            bid = Bid(
                amount=bid_amount,
                bidder_id=current_user.id,
                item_id=item.id
            )
            db.session.add(bid)
            db.session.commit()
            flash("Bid placed successfully!")
        else:
            flash("Bid must be higher than current highest bid.")

        return redirect(url_for("item_detail", item_id=item.id))

    return render_template("item_detail.html",
                           item=item,
                           bids=bids,
                           highest_bid=highest_bid)


# ==============================
# CONTACT
# ==============================
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        contact = Contact(
            name=request.form["name"],
            year=request.form["year"],
            department=request.form["department"],
            reason=request.form["reason"]
        )

        db.session.add(contact)
        db.session.commit()

        flash("Message sent successfully!")
        return redirect(url_for("contact"))

    return render_template("contact.html")


# ==============================
# ADMIN DASHBOARD
# ==============================
@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for("home"))

    pending_users = User.query.filter_by(is_approved=False).all()
    total_users = User.query.count()
    total_items = Item.query.count()
    total_bids = Bid.query.count()

    return render_template("admin_dashboard.html",
                           pending_users=pending_users,
                           total_users=total_users,
                           total_items=total_items,
                           total_bids=total_bids)


# ==============================
# APPROVE USER
# ==============================
@app.route("/approve/<int:user_id>")
@login_required
def approve_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for("home"))

    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()

    return redirect(url_for("admin_dashboard"))


# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)