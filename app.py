from flask import Flask, render_template, jsonify, request
from services.data_services import (get_names, get_years_by_name, get_months_by_name_and_year,)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/names")
def api_names():
    return jsonify(get_names())


@app.route("/api/years")
def api_years():
    selected_name = request.args.get("name", "")

    if not selected_name:
        return jsonify([])
    
    return jsonify(get_years_by_name(selected_name))


@app.route("/api/months")
def api_months():
    selected_name = request.args.get("name", "")
    selected_year = request.args.get("year", "")

    if not selected_name or not selected_year:
        return jsonify([])

    return jsonify(get_months_by_name_and_year(selected_name, selected_year))


if __name__ == "__main__":
    app.run(debug=True)