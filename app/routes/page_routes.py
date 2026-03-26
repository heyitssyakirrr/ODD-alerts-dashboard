from flask import render_template, redirect


def register_page_routes(app):
    @app.route("/")
    def home():
        return redirect("/dashboard/")

    @app.route("/explorer")
    def explorer():
        return render_template("index.html")