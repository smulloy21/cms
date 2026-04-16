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
from markdown import markdown


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
    file_path = os.path.join(data_dir, filename)

    if not os.path.exists(file_path):
        flash(f'{filename} does not exist.', 'error')
        session.modified = True
        return redirect(url_for('index'))

    if filename.endswith('.md'):
        with open(file_path, 'r') as file:
            content = file.read()
        return markdown(content)

    return send_from_directory(data_dir, filename)


if __name__ == '__main__':
    app.run(debug=True, port=5003)
