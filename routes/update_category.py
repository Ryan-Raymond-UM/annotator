import collections
import filelock
import flask
import json
import os
import sklearn.metrics

blueprint = flask.Blueprint('update-category', __name__)
@blueprint.route('/update-category', methods=['POST'])
def update_category():
    data = flask.request.get_json()
    job_id = data.get('job_id', '').strip()
    image_url = data.get('image_url', '').strip()
    category = data.get('category', '').strip()
    operation = data.get('operation', '').strip()
    source = data.get('source', '').strip()

    if not job_id or not image_url or not category:
        return flask.jsonify({"status": "error", "message": "Missing job_id, image_url, or category"}), 400

    cleaned_image_url = image_url.replace("/image?path=", "").strip()
    # print(f"Updating category for '{cleaned_image_url}' to '{category}'")

    job_path = f"./data/{job_id}/job_parameters.json"
    lock_path = f'{job_path}.lock'

    if not os.path.exists(job_path):
        return flask.jsonify({"status": "error", "message": "Invalid job_id."}), 400

    with filelock.FileLock(lock_path):
        with open(job_path, "r") as f:
            job_parameters = json.load(f)

        corrected_labels = job_parameters.setdefault("corrected_labels", {})
        predicted_labels = job_parameters.get("predicted_labels", {})
        checkbox_status = job_parameters.get("checkbox_status", {})

        if operation == "add":
            corrected_labels[cleaned_image_url] = category
            if source == "checkbox":
                checkbox_status[cleaned_image_url] = "checked"
        else:
            if cleaned_image_url in corrected_labels:
                del corrected_labels[cleaned_image_url]
            if source == "checkbox":
                checkbox_status[cleaned_image_url] = ""

        predicted = []
        actual = []
        for key, value_list in predicted_labels.items():
            predicted_label = value_list[0]
            predicted.append(predicted_label)

            actual_label = corrected_labels.get(key, predicted_label)
            actual.append(actual_label)

        # Compute metrics
        Accuracy_Score = round(sklearn.metrics.accuracy_score(actual, predicted) * 100, 2)
        F1_Score = round(sklearn.metrics.f1_score(actual, predicted, average="weighted") * 100, 2)

        # Count actual vs predicted
        predicted_counts = collections.Counter([v[0] for v in predicted_labels.values()])
        corrected_counts = collections.Counter(corrected_labels.values())

        total_pred = sum(predicted_counts.values())
        total_corr = sum(corrected_counts.values())

        # Build labeled data counts with merged keys
        all_labels = set(predicted_counts.keys()) | set(corrected_counts.keys())
        labeled_data_counts = {
            f"{label} ({predicted_counts.get(label, 0)})": corrected_counts.get(label, 0)
            for label in all_labels
        }
        labeled_data_counts[f"Total ({total_pred})"] = total_corr

        # Store updated metrics
        job_parameters["Accuracy_Score"] = Accuracy_Score
        job_parameters["F1_Score"] = F1_Score
        job_parameters["labeled_data_counts"] = labeled_data_counts
        job_parameters["checkbox_status"] = checkbox_status


        with open(job_path, "w") as f:
            json.dump(job_parameters, f, indent=4)

    return flask.jsonify({
        "status": "success",
        "message": "Category updated successfully",
        "labeled_data_counts": labeled_data_counts,
        "accuracy_score": Accuracy_Score,
        "f1_score": F1_Score
    }), 200
