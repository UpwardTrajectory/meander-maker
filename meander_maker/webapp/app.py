from flask import Flask, request, render_template, jsonify
from .. import goplaces as gp

app = Flask(__name__, static_url_path="")

@app.route("/")
def index():
    """Return the main page."""
    return render_template("index.html")


@app.route("/output", methods=["GET", "POST"])
def output():
    """Return HTML based on user input"""
    data = request.get_json(force=True)
    # every time the user_input identifier
    loc, topic, mode = data['loc'], data['topic'], data['mode']
    html_map = gp.all_things(
        loc, topic, mode, n=20, verbose=False, output='flask'
    )
    return str(loc)+str(topic)+str(mode)  # For Testing Only
    #return html_map
    