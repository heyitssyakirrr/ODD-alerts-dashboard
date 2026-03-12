from flask import Flask, render_template, jsonify, request
from services.data_services import get_years, get_months_by_year, get_dates_by_month

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/years")
def api_years():
    return jsonify(get_years())


@app.route("/api/months")
def api_months():
    selected_year = request.args.get("year", "")
    return jsonify(get_months_by_year(selected_year))


@app.route("/api/dates")
def api_dates():
    selected_month = request.args.get("month", "")
    return jsonify(get_dates_by_month(selected_month))


if __name__ == "__main__":
    app.run(debug=True)