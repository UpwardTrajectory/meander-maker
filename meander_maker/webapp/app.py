from flask import Flask, request, render_template, jsonify
from .. import goplaces as gp

app = Flask(__name__, static_url_path="")

@app.route("/")
def index():
    """Return the main page."""
    return render_template("index.html")


@app.route("/output", methods=["GET", "POST"])
def output():
    """Retun text from user input"""
    data = request.get_json(force=True)
    # every time the user_input identifier
    loc, topic = data['loc'], data['topic']
    output = gp.all_things(
        loc, topic, mode='walking', n=20, verbose=False, output='flask')
    return output
