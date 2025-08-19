import flask
import flask_login
import hashlib

blueprint = flask.Blueprint('login', __name__)
@blueprint.route('/login', methods=['GET', 'POST'])
def login():
	users = flask.current_app.config['USERS']
	User = flask.current_app.config['USER']
	if flask.request.method == 'POST':
		username = flask.request.form['username']
		password = flask.request.form['password']
		password_hash = hashlib.sha256(password.encode()).hexdigest()
		if username in users and users[username]['password-hash'] == password_hash:
			flask_login.login_user(User(username))
			return flask.redirect('/')
	return flask.render_template('login.html')
