from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request

from stock_data import get_consecutive_boards

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/boards")
def api_boards():
    date = request.args.get("date") or datetime.now().strftime("%Y%m%d")
    min_boards = int(request.args.get("min", 2))

    try:
        data, used_date = get_consecutive_boards(date, min_boards=min_boards)
    except Exception as e:
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500

    total = sum(len(v) for v in data.values())
    return jsonify({
        "ok": True,
        "requested_date": date,
        "data_date": used_date,
        "total": total,
        "groups": data,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
