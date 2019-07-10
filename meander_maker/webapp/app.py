#import base64
import uuid
from flask import Flask, request, render_template, jsonify
from .. import goplaces as gp

app = Flask(__name__, static_url_path="")

@app.route("/")
def index():
    """Return the main page."""
    return render_template("index.html")


@app.route("/output", methods=["GET", "POST"])
def generate_output():
    """Return HTML based on user input"""
    data = request.get_json(force=True)
    # every time the user_input identifier
    loc, topic, mode = data['loc'], data['topic'], data['mode']
    html_map = gp.all_things(
        loc, topic, mode, n=20, verbose=False, output='flask')
#     html_map_b64 = base64.b64encode(html_map.encode('utf-8'))
#     return (
#         b'''<iframe src="data:text/html;charset=utf-8;base64,'''
#         + html_map_b64
#         + b'''"></iframe>'''
#     )
    map_id = uuid.uuid4()
    with open(f'meander_maker/webapp/static/maps/{map_id}.html', 'w') as f:
        f.write(html_map)
    return f'<iframe src="/maps/{map_id}.html"></iframe>'
    