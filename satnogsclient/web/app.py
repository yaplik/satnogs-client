from flask import Flask, render_template

from satnogsclient import settings as client_settings


app = Flask(__name__)


@app.route("/")
def index():
    """View list of satnogs-client settings."""
    filters = [
        lambda x: not x.startswith('_'),
        lambda x: x.isupper()
    ]

    entries = client_settings.__dict__.items()
    settings = filter(lambda (x, y): all(f(x) for f in filters), entries)

    ctx = {
        'settings': sorted(settings, key=lambda x: x[0])
    }

    return render_template('index.j2', **ctx)
