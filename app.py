from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Home / Landing Page
@app.route("/")
def home():
    return render_template("index.html")

# Contact Page
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        print("Contact Message:", name, email, message)

        return redirect(url_for("contact"))

    return render_template("contact.html")

# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        print("Login:", email, password)
        return redirect(url_for("home"))

    return render_template("login.html")

# Signup Page
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        print("Signup:", name, email)
        return redirect(url_for("login"))

    return render_template("signup.html")

# Add Item / Sell Page
@app.route("/add-item", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        title = request.form.get("title")
        price = request.form.get("price")
        description = request.form.get("description")

        print("New Item:", title, price, description)

        return redirect(url_for("home"))

    return render_template("add_item.html")

if __name__ == "__main__":
    app.run(debug=True)
