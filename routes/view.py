import filelock
import flask
import image_functions
import json
import os

blueprint = flask.Blueprint('view', __name__)
@blueprint.route('/view')
def view_job():

	job_id = flask.request.args.get('id')
	job_path = f'./data/{job_id}/job_parameters.json'
	lock_path = f'{job_path}.lock'

	if not os.path.exists(job_path):
		return flask.render_template('job_not_found.html'), 404

	with filelock.FileLock(lock_path):
		with open(job_path) as f:
			job_parameters = json.load(f)

	status_file_path = os.path.join(job_parameters["job_path"],'job.status')
	# Create a lock for the status file to avoid race conditions
	lock_path = f'{status_file_path}.lock'
	with filelock.FileLock(lock_path) as lock:
		with open(status_file_path, "r") as status_file:
			job_status = json.load(status_file)

	if job_status["status"] == "completed":

		# Assume clusters_dict is already generated
		selected_cluster = flask.request.args.get( "cluster", "0" )
		page = int(flask.request.args.get("page", 0))

		clusters_dict = job_parameters["clusters"]

		images_per_page = 40
		start = page * images_per_page
		end = start + images_per_page
		image_paths = clusters_dict[selected_cluster][start:end]

		Accuracy_Score = job_parameters["Accuracy_Score"]
		F1_Score = job_parameters["F1_Score"]
		labeled_data_counts = job_parameters["labeled_data_counts"]
		checkbox_status = job_parameters.get("checkbox_status", {})



		return flask.render_template('view_job.html',
			job=job_parameters,
			job_status=job_status,
			categories = image_functions.categories,
			labeled_data_counts = labeled_data_counts,
			accuracy_score = Accuracy_Score,
			f1_score = F1_Score,
			checkbox_status = checkbox_status,

			clusters_dict=clusters_dict,
			selected_cluster= int(selected_cluster),
			image_paths=image_paths,
			page=page,
			total_clusters=len(clusters_dict),
			total_images = len(clusters_dict[selected_cluster])
			)
	else:
		return flask.render_template('view_job.html',
			job=job_parameters,
			job_status=job_status,
			categories = image_functions.categories,
			checkbox_status = {},
			labeled_data_counts = {},
			accuracy_score = 0,
			f1_score = 0,
			clusters_dict={},
			selected_cluster= 0,
			image_paths=[],
			page=0,
			total_clusters=0,
			total_images = 0
			)
