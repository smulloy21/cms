from functools import wraps
import os

from flask import (
    flash,
    Flask,
    redirect,
    request,
    render_template,
    send_from_directory,
    session,
    url_for,
)
from markdown import markdown

from src.cms.utils import is_valid


app = Flask(__name__)
app.secret_key='secret123'


def get_data_path():
    if app.config['TESTING']:
        return os.path.join(os.path.dirname(__file__), 'tests', 'data')
    else:
        return os.path.join(os.path.dirname(__file__), 'src', 'cms', 'data')


def user_signed_in():
    return 'username' in session


def require_signed_in_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not user_signed_in():
            flash('You must be signed in to do that.', 'error')
            return redirect(url_for('show_signin'))

        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    data_dir = get_data_path()
    files = [os.path.basename(path) for path in os.listdir(data_dir)]
    return render_template('index.html', files=files)


@app.route('/<filename>')
def get_file(filename):
    data_dir = get_data_path()
    file_path = os.path.join(data_dir, filename)

    if not os.path.exists(file_path):
        flash(f'{filename} does not exist.', 'error')
        session.modified = True
        return redirect(url_for('index'))

    if filename.endswith('.md'):
        with open(file_path, 'r') as file:
            content = file.read()
        return render_template('markdown.html', content=markdown(content))

    return send_from_directory(data_dir, filename)


@app.route('/<filename>/edit')
@require_signed_in_user
def show_edit_file(filename):
    data_dir = get_data_path()
    file_path = os.path.join(data_dir, filename)

    if not os.path.exists(file_path):
        flash(f'{filename} does not exist.', 'error')
        session.modified = True
        return redirect(url_for('index'))

    with open(file_path, 'r') as file:
        contents = file.read()

    return render_template('edit_file.html', filename=filename, contents=contents)


@app.route('/<filename>/edit', methods=["POST"])
@require_signed_in_user
def edit_file(filename):
    content = request.form["file_content"].strip()
    data_dir = get_data_path()
    file_path = os.path.join(data_dir, filename)

    if not os.path.exists(file_path):
        flash(f'{filename} does not exist.', 'error')
        session.modified = True
        return redirect(url_for('index'))

    with open(file_path, 'w') as file:
        file.write(content)

    flash(f'{filename} successfully updated.', 'success')
    session.modified = True
    return redirect(url_for('index'))


@app.route('/new')
@require_signed_in_user
def show_new_document():
    return render_template('new_file.html')


@app.route('/new', methods=["POST"])
@require_signed_in_user
def create_file():
    filename = request.form['new_file_name'].strip()
    data_dir = get_data_path()
    file_path = os.path.join(data_dir, filename)

    if not filename:
        flash('A file name is required.', 'error')
        session.modified = True
        return redirect(url_for('show_new_document'))

    if os.path.exists(file_path):
        flash(f'{filename} already exists.', 'error')
        session.modified = True
        return redirect(url_for('index'))

    with open(file_path, "a") as f:
        pass

    flash(f'{filename} successfully created.', 'success')
    session.modified = True
    return redirect(url_for('index'))


@app.route('/<filename>/delete', methods=["POST"])
@require_signed_in_user
def delete_file(filename):
    data_dir = get_data_path()
    file_path = os.path.join(data_dir, filename)

    if not os.path.exists(file_path):
        flash(f'{filename} does not exist.', 'error')
        session.modified = True
        return redirect(url_for('index'))

    os.remove(file_path)

    flash(f'{filename} successfully deleted.', 'success')
    session.modified = True
    return redirect(url_for('index'))


@app.route('/users/signin')
def show_signin():
    return render_template('sign_in.html')


@app.route('/users/signin', methods=["POST"])
def sign_in_user():
    username = request.form['username'].strip()
    password = request.form['password'].strip()

    if not is_valid(username, password):
        flash('Credentials are invalid', 'error')
        session.modified = True
        return render_template('sign_in.html'), 422

    flash('Welcome!', 'success')
    session['username'] = username
    session.modified = True
    return redirect(url_for('index'))


@app.route("/users/signout", methods=['POST'])
def signout():
    session.pop('username', None)
    flash("You have been signed out.", 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5003)
