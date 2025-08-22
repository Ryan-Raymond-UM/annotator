import api
import flask

blueprint = flask.Blueprint('user', __name__)
@blueprint.route('/users', methods=['GET', 'POST'])
@blueprint.route('/users/<username>', methods=['GET', 'PATCH', 'DELETE'])
def f(username=None):
	user_db = flask.current_app.config['user_db']
	data = flask.request.get_json(force=True, silent=True) or flask.request.form.to_dict()

	match flask.request.method:
		case 'POST':
			try:
				username = data['username']
				api.user.create(user_db, username, data)
				return api.user.read(user_db, username), 201
			except api.user.UserAlreadyExistsError:
				flask.abort(409)
		case 'GET':
			try:
				return api.user.read(user_db, username), 200
			except api.user.UserNotFoundError:
				flask.abort(404)
		case 'PATCH':
			try:
				api.user.update(user_db, username, data)
				return api.user.read(user_db, username), 200
			except api.user.UserNotFoundError:
				flask.abort(400)
		case 'DELETE':
			try:
				api.user.delete(user_db, username)
				return '', 200
			except api.user.UserNotFoundError:
				flask.abort(404)
