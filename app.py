from flask import Flask, render_template, request, redirect, session, url_for
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "secret_key"  # Used to secure sessions

# MongoDB configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/flask_roles_db"
mongo = PyMongo(app)


# Route to determine where to redirect user after login based on their role
@app.route("/")
def index():
    if "user_id" in session:
        user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("user_dashboard"))
    return render_template("Accueil.html")


# User registration route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Extract form data
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = generate_password_hash(request.form["password"])  # Hash the password

        # Check if email already exists
        if mongo.db.users.find_one({"email": email}):
            return "Email already exists"

        # Insert new user with default role "user"
        mongo.db.users.insert_one({
            "name": name,
            "email": email,
            "phone": phone,
            "password": password,
            "role": "user"
        })
        return redirect(url_for("login"))
    return render_template("register.html")


# User login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Extract login form data
        email = request.form["email"]
        password = request.form["password"]

        # Check user credentials
        user = mongo.db.users.find_one({"email": email})
        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])  # Store user ID in session
            return redirect(url_for("index"))
        return "Invalid credentials"
    return render_template("login.html")


# Logout route
@app.route("/logout")
def logout():
    session.clear()  # Clear session
    return redirect(url_for("login"))


# Dashboard for regular users
@app.route("/user/dashboard")
def user_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
    if user["role"] != "user":
        return "Unauthorized"
    return render_template("user_dashboard.html", name=user["name"])



# Service selection form (GET/POST)
@app.route("/select_service/<service_name>", methods=["GET", "POST"])
def select_service(service_name):
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("service_form.html", service_name=service_name)



# Handle submission of a selected service request
@app.route("/submit_service_form", methods=["POST"])
def submit_service_form():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})

    # Extract form data
    service_name = request.form["service_name"]
    sub_service = request.form["sub_service"]
    description = request.form["description"]
    quantity = int(request.form["quantity"])

    # Store the request in the database
    # Store the request in the database
    mongo.db.requests.insert_one({
        "user_id": user["_id"],
        "name": user["name"],
        "email": user["email"],
        "phone": user["phone"],
        "service": service_name,
        "sub_service": sub_service,
        "description": description,
        "quantity": quantity,
        "status": "Pending"  # Default status
    })

    return render_template("request_submitted.html")


@app.route("/admin/update_status/<request_id>", methods=["POST"])
def update_status(request_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
    if user["role"] != "admin":
        return "Unauthorized"

    new_status = request.form.get("status")
    mongo.db.requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": new_status}}
    )
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_request/<request_id>", methods=["POST"])
def delete_request(request_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
    if user["role"] != "admin":
        return "Unauthorized"

    mongo.db.requests.delete_one({"_id": ObjectId(request_id)})
    return redirect(url_for("admin_dashboard"))

@app.route("/track_requests")
def track_requests():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = ObjectId(session["user_id"])
    user_requests = list(mongo.db.requests.find({"user_id": user_id}))
    return render_template("track_request.html", requests=user_requests)



# Admin dashboard that displays all user requests
@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
    if user["role"] != "admin":
        return "Unauthorized"

    # Fetch all service requests
    requests = list(mongo.db.requests.find())
    return render_template("admin_dashboard.html", name=user["name"], requests=requests)


# Custom 404 error page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404




# About us page
@app.route('/À propos de nous')
def AboutUs():
    return render_template('AboutUs.html')


# Start the Flask development server
if __name__ == "__main__":
    app.run(debug=True)
