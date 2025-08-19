import filelock
import flask
import glob
import json

blueprint = flask.Blueprint('jobs', __name__)
@blueprint.route('/jobs')
def jobs(message=None):

    all_jobs_path = glob.glob("./data/*/job_parameters.json")

    jobs_list = []

    for job_path in all_jobs_path:
        lock_path = f'{job_path}.lock'
        with filelock.FileLock(lock_path):
            with open(job_path) as f:
                jobs_list.append(json.load(f))

    return flask.render_template('jobs.html', jobs_list=jobs_list, message=message)
