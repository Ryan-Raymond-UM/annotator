import flask

blueprint = flask.Blueprint('admin', __name__)
@blueprint.route('/admin')
def index():
    return flask.render_template('index.html')
