import os

from flask import (
    flash,
    Flask,
    redirect,
    render_template,
    send_from_directory,
    session,
    url_for,
)


app = Flask(__name__)
app.secret_key='secret123'


@app.route('/')
def index():
    root = os.path.abspath(os.path.dirname(__file__))
    data_dir = os.path.join(root, "src", "cms", "data")
    files = [os.path.basename(path) for path in os.listdir(data_dir)]
    return render_template('index.html', files=files)


@app.route('/<filename>')
def get_file(filename):
    root = os.path.abspath(os.path.dirname(__file__))
    data_dir = os.path.join(root, "src", "cms", "data")

    if not os.path.exists(f"{data_dir}/{filename}"):
        flash(f'{filename} does not exist.', 'error')
        session.modified = True
        return redirect(url_for('index'))

    return send_from_directory(data_dir, filename)


if __name__ == '__main__':
    app.run(debug=True, port=5003)
