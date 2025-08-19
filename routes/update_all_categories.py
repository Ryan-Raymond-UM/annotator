import collections
import filelock
import flask
import json
import os
import sklearn.metrics

blueprint = flask.Blueprint('update-all-categories', __name__)
@blueprint.route('/update-all-categories', methods=['POST'])
def update_all_categories():
    data = flask.request.get_json()
    job_id = data.get('job_id', '').strip()
    image_urls = data.get('image_urls', [])
    category = data.get('category', '').strip()

    if not job_id or not category or not image_urls:
        return flask.jsonify({"status": "error", "message": "Missing job_id, category, or image_urls"}), 400

    job_path = f"./data/{job_id}/job_parameters.json"
    lock_path = f'{job_path}.lock'

    if not os.path.exists(job_path):
        return flask.jsonify({"status": "error", "message": "Invalid job_id"}), 400
    try:
        with filelock.FileLock(lock_path):
            with open(job_path, "r") as f:
                job_parameters = json.load(f)

            corrected_labels = job_parameters.setdefault("corrected_labels", {})

            # Clean and update image URLs
            cleaned_urls = [url.replace("/image?path=", "").strip() for url in image_urls]
            for url in cleaned_urls:
                corrected_labels[url] = category

            predicted_labels = job_parameters.get("predicted_labels", {})

            predicted = []
            actual = []
            for key, value_list in predicted_labels.items():
                predicted_label = value_list[0]
                predicted.append(predicted_label)

                # Use corrected if available, otherwise fallback
                actual.append(corrected_labels.get(key, predicted_label))

            # Metrics
            Accuracy_Score = round(sklearn.metrics.accuracy_score(actual, predicted) * 100, 2)
            F1_Score = round(sklearn.metrics.f1_score(actual, predicted, average="weighted") * 100, 2)

            # Count actual vs predicted
            predicted_counts = collections.Counter([v[0] for v in predicted_labels.values()])
            corrected_counts = collections.Counter(corrected_labels.values())

            total_pred = sum(predicted_counts.values())
            total_corr = sum(corrected_counts.values())

            # Combine counts with label + (predicted count)
            labeled_data_counts = {
                f"{label} ({predicted_counts.get(label, 0)})": corrected_counts.get(label, 0)
                for label in set(predicted_counts.keys()).union(corrected_counts.keys())
            }
            labeled_data_counts[f"Total ({total_pred})"] = total_corr

            # Update scores in file
            job_parameters["Accuracy_Score"] = Accuracy_Score
            job_parameters["F1_Score"] = F1_Score
            job_parameters["labeled_data_counts"] = labeled_data_counts


            with open(job_path, "w") as f:
                json.dump(job_parameters, f, indent=4)

        return flask.jsonify({
            "status": "success",
            "message": "Categories updated successfully",
            "labeled_data_counts": labeled_data_counts,
            "accuracy_score": Accuracy_Score,
            "f1_score": F1_Score
        }), 200

    except Exception as exp:
        print( "Exception occured:" , exp )
        return flask.jsonify({"status": "error", "message": "Missing job_id, category, or image_urls"}), 400
