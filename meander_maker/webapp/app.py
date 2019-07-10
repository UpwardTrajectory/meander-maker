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
    n = int(data['patience']) * 20
    results = gp.all_things(
        loc, topic, mode, n=n, verbose=False, output='flask')
    html_map = results['html']
    best_cluster = results['best_cluster']
    map_id = uuid.uuid4()
    with open(f'meander_maker/webapp/static/maps/{map_id}.html', 'w') as f:
        f.write(html_map)
    iframe = f'<iframe class="meander_map" src="/maps/{map_id}.html"></iframe>'
    return jsonify({'iframe': iframe,
                   'best_cluster': best_cluster.to_dict(orient='records')})
    