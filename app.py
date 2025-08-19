import collections
import datetime
import flask
import flask_login
import glob
import hashlib
import json
import mimetypes
import os
import pandas as pd
import py7zr
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
import zipfile

from filelock import FileLock
from flask import Flask, render_template, request, jsonify
from flask import send_file, abort
from image_functions import perform_clustering, categories, category_mapping
from requests.exceptions import Timeout
from sklearn.metrics import accuracy_score, f1_score

import routes #local

class User(flask_login.UserMixin):
	def __init__(self, username):
		self.id = username

cwd = os.getcwd()
print("cwd:", cwd)
upload_folder = os.path.join( cwd ,  "data/uploaded/")
print( "upload_folder:", upload_folder )

app = Flask(__name__)
app.secret_key = "ISuckBalls"

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

PUBLIC_ROUTES = {'login.login'}

users = {'ryanray': {'password-hash': hashlib.sha256('ISuckBalls'.encode()).hexdigest()}}
app.config['USERS'] = users
app.config['USER'] = User

@app.before_request
def require_login():
	if request.endpoint in PUBLIC_ROUTES:
		return # Is public, do nothing
	if flask_login.current_user.is_authenticated:
		return # User is logged in, do nothing
	return flask.redirect('/login')#flask.url_for('login'))

# https://flask-login.readthedocs.io/en/latest/#how-it-works
@login_manager.user_loader
def load_user(user_id):
	if user_id in users:
		return User(user_id)
	return None

app.register_blueprint(routes.admin)
app.register_blueprint(routes.index)
app.register_blueprint(routes.login)
app.register_blueprint(routes.jobs)

@app.route('/submit', methods=['POST'])
def submit():
    
    # Get the input method selected by the user
    input_method = request.form.get('inputMethod')
    print( "input_method:" , input_method )
    job_parameters = {"input_method" : input_method}
    
    
    # Get the ZIP file or folder path
    if input_method == 'zip':
        
        zip_file = request.files.get('fileUpload')  # Retrieve the uploaded ZIP file
        handle_zip_upload(zip_file, upload_folder)
    
        extract_folder = os.path.join( upload_folder, os.path.splitext( zip_file.filename )[0] )

        job_parameters["zip_filename"] = zip_file.filename
        job_parameters["folder_path"] = extract_folder

        print( "Zip file extracted in folder:", extract_folder  )

        images_path = glob.glob(  os.path.join( extract_folder , "*/*.png" ) )
        html_files_path = [path.replace(".png",  ".html") for path in images_path if os.path.isfile( path.replace(".png",  ".html") ) ]
        
        images_npy_path = glob.glob(  os.path.join( extract_folder , "*/*.img.npy" ) )
        

        #print("Total valid folders having both PNG and HTML:", len(images_path))
        
        job_parameters["images_path_list"] = images_path
        job_parameters["html_files_path_list"] = html_files_path
        
    
        job_parameters["total_samples"] = len(images_path)

        if len(images_path) == 0:
            return "The zip file does not have data in correct format."
        
        elif len(images_npy_path) == 0:
            return "The zip file does not have pre-computed embeddings."
        else:
            print( "The zip file contains total samples:", len(images_path) )
            

    elif input_method == 'path':
        folder_path = request.form.get('folderPath')  # Retrieve the folder path input
        
        if folder_path:

            job_parameters["folder_path"] = folder_path
            
            print(f'Folder path entered: {folder_path}')
            print( os.path.join(folder_path , "*/*.png" )  )

            images_path = glob.glob(  os.path.join( folder_path , "*/*.png" ) )
            html_files_path = [path.replace(".png",  ".html") for path in images_path if os.path.isfile( path.replace(".png",  ".html") ) ]
            
            images_npy_path = glob.glob(  os.path.join( folder_path , "*/*.img.npy" ) )
            
             
            job_parameters["images_path_list"] = images_path
            job_parameters["html_files_path_list"] = html_files_path
            
        
            job_parameters["total_samples"] = len(images_path)
    
            if len(images_path) == 0:
                return "The provided path does not have data in correct format."
            
            elif len(images_npy_path) == 0:
                return "The provided path does not have pre-computed embeddings."
            else:
                print( "The provided path contains total samples:", len(images_path) )
        
        else:
            print('No folder path provided.')

    elif input_method == 'cloud':
        pass
            

    job_description = request.form.get('jobDescription')
    print(f'Job Description: {job_description}')
    job_parameters["job_description"] = job_description

    # Get the clustering algorithm selected
    clustering_algorithm = request.form.get('clusteringAlgorithm')
    print(f'Clustering Algorithm: {clustering_algorithm}')
    job_parameters["clustering_algorithm"] = clustering_algorithm

    # Get the number of clusters input
    num_clusters = request.form.get('numClusters')
    print(f'Number of clusters: {num_clusters}')
    job_parameters["num_clusters"] = num_clusters

    # Get the input type (image, text, or both)
    input_type = request.form.get('inputType')
    print(f'Input Type: {input_type}')
    job_parameters["input_type"] = input_type

    # Get the encoding model (image or text encoding based on input type)
    if input_type == 'image':
        image_encoding = request.form.get('imageEncoding')
        print(f'Image Encoding Model: {image_encoding}')
        job_parameters["image_encoding"] = image_encoding
        
    elif input_type == 'text':
        text_encoding = request.form.get('textEncoding')
        print(f'Text Encoding Model: {text_encoding}')
        job_parameters["text_encoding"] = text_encoding
        
    else:
        image_encoding = request.form.get('imageEncoding')
        print(f'Image Encoding Model: {image_encoding}')
        
        text_encoding = request.form.get('textEncoding')
        print(f'Text Encoding Model: {text_encoding}')

        job_parameters["image_encoding"] = image_encoding
        job_parameters["text_encoding"] = text_encoding

    # You can process the data here, e.g., initiate clustering, etc.

    unique_id, job_path = create_job_path()

    job_parameters["job_id"] = unique_id
    job_parameters["job_path"] = job_path
    job_parameters["corrected_labels"] = {}
    job_parameters["checkbox_status"]  = {}

    predicted_labels = {}
    for image_path in job_parameters["images_path_list"]:
        pred_path = image_path.replace( ".png", ".prediction" )
        job_parameters["checkbox_status"][ image_path.replace(upload_folder, "") ] = ""
        if os.path.isfile( pred_path ):
            lock_path = pred_path + ".lock"
            lock = FileLock(lock_path)
            with lock:
                with open(pred_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        try:
                            mapped_label = ( category_mapping[ json.loads(content)[0][0] ] , json.loads(content)[0][1] )
                            predicted_labels[image_path.replace(upload_folder, "")] = mapped_label
                        except json.JSONDecodeError as e:
                            print(f"Invalid JSON in {pred_path}: {e}")
                            predicted_labels[image_path.replace(upload_folder, "")] = ""
                    else:
                        print(f"Empty prediction file: {pred_path}")
                        predicted_labels[image_path.replace(upload_folder, "")] = ""
        else:
            predicted_labels[ image_path.replace( upload_folder , "" ) ] = ""

    job_parameters["predicted_labels"] = predicted_labels
    
    # Store updated metrics
    job_parameters["Accuracy_Score"] = 100
    job_parameters["F1_Score"] = 100
    labeled_data_counts = { key + f" ({value})":0 for key , value in dict( Counter([v[0] for v in predicted_labels.values()]) ).items() }
    labeled_data_counts[ f"Total ({len(predicted_labels)})" ] = 0
    job_parameters["labeled_data_counts"] = labeled_data_counts

    
    # Get the current date and time
    job_parameters["job_submission_time"] = datetime.datetime.now().isoformat()
    
    with open( os.path.join(job_path , "job_parameters.json") , "w" ) as f:
        json.dump( job_parameters , f )
    
    message = f"Job submitted successfully, with job id {unique_id}."
    
    threading.Thread(target=perform_clustering, args=(job_parameters,upload_folder, )).start()
    
    return jobs( message )

@app.route('/view')
def view_job():
    
    job_id = request.args.get('id')
    job_path = f"./data/{job_id}/job_parameters.json"
    lock_path = job_path + ".lock"
    
    if not os.path.exists(job_path):
        return (
                "Job does not exist, please check other jobs at "
                "<a href='/jobs'>Job List</a>",
                404
        )
                
    with FileLock(lock_path):
        with open( job_path ) as f:
            job_parameters = json.load( f ) 

    status_file_path = os.path.join( job_parameters["job_path"], 'job.status')
    # Create a lock for the status file to avoid race conditions
    lock_path = status_file_path + ".lock"
    lock = FileLock(lock_path)
    with lock:
        with open(status_file_path, "r") as status_file:
            job_status = json.load(status_file)

    

    if job_status["status"] == "completed":

        # Assume clusters_dict is already generated
        selected_cluster = request.args.get( "cluster", "0" )
        page = int(request.args.get("page", 0))
    
        clusters_dict = job_parameters["clusters"]
        
        images_per_page = 40
        start = page * images_per_page
        end = start + images_per_page
        image_paths = clusters_dict[selected_cluster][start:end]

        Accuracy_Score = job_parameters["Accuracy_Score"]
        F1_Score = job_parameters["F1_Score"]
        labeled_data_counts = job_parameters["labeled_data_counts"]
        checkbox_status = job_parameters.get("checkbox_status", {})


		
        return render_template('view_job.html', 
                               job=job_parameters, 
                               job_status=job_status,
                               categories = categories, 
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

        return render_template('view_job.html', 
                               job=job_parameters, 
                               job_status=job_status,
                               categories = categories, 

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
        



# @app.route('/download', methods=['GET'])
# def download_job():
#     job_id = request.args.get('id')
#     job_dir = os.path.abspath(f"./data/{job_id}")
#     job_path = os.path.join(job_dir, "job_parameters.json")
#     job_lock_path = job_path + ".lock"

#     if not os.path.exists(job_path):
#         return Response(
#             "Job does not exist. Please check other jobs at "
#             "<a href='/jobs'>Job List</a>",
#             status=404,
#             mimetype='text/html'
#         )

#     # Load job parameters safely
#     try:
#         with FileLock(job_lock_path, timeout=5):
#             with open(job_path, 'r') as f:
#                 job_parameters = json.load(f)
#     except Timeout:
#         abort(503, description="Job file is currently locked. Try again shortly.")
#     except Exception as e:
#         abort(500, description=f"Error reading job parameters: {e}")

#     # Load job status safely
#     status_path = os.path.join(job_parameters.get("job_path", job_dir), "job.status")
#     status_lock_path = status_path + ".lock"

#     try:
#         with FileLock(status_lock_path, timeout=5):
#             with open(status_path, "r") as f:
#                 job_status = json.load(f)
#     except FileNotFoundError:
#         abort(404, description="Job status file not found.")
#     except Timeout:
#         abort(503, description="Status file is currently locked. Try again shortly.")
#     except Exception as e:
#         abort(500, description=f"Error reading job status: {e}")

#     if job_status.get("status") != "completed":
#         return "Job is not completed yet. Please try again later.", 409
    
#     corrected_labels = job_parameters.get("corrected_labels", {})
#     if not corrected_labels:
#         return "Please label some data before downloading the job.", 400

#     try:
        
#         with tempfile.TemporaryDirectory() as tmp_dir:
#             root_output_path = os.path.join(tmp_dir, "download")

#             csv_data = [ ["F1-Score" , str(job_parameters["F1_Score"]) , "" , "" ], 
#                          ["Accuracy-Score" , str(job_parameters["Accuracy_Score"]) , "" , "" ],
#                          ["" , "" , "" , "" ],
#                          ["URL", "Cat1", "Cat1_Prob", "Manual_Label"]
#                        ]
#             for image_path, category in corrected_labels.items():
                
                
#                 domain_folder = os.path.dirname(image_path)
#                 domain_name = os.path.basename(domain_folder)
#                 domain_folder_path = os.path.join(upload_folder, domain_folder)

#                 csv_data.append( [domain_name.replace("_", ".")  ,
#                                   job_parameters[ "predicted_labels" ][image_path][0],
#                                   str( round(job_parameters[ "predicted_labels" ][image_path][1]*100 , 2) ),
#                                   category ] )
                
                
#                 if not os.path.exists(domain_folder_path):
#                     continue  # Skip missing domains

#                 category_path = os.path.join(root_output_path, category)
#                 os.makedirs(category_path, exist_ok=True)

#                 shutil.copytree(
#                     domain_folder_path,
#                     os.path.join(category_path, os.path.basename(domain_folder_path)),
#                     dirs_exist_ok=True
#                 )

            
#             csv_data_pd = pd.DataFrame(csv_data, columns=["URL", "Cat1", "Cat1_Prob", "Manual_Label"])
#             csv_file_path = os.path.join(root_output_path, "summary.csv")
#             csv_data_pd.to_csv(csv_file_path, sep = "\t" ,  index=False, header=False)
            
#             # Create ZIP
#             zip_path = os.path.join(job_dir, "download.zip")
#             with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
#                 for foldername, _, filenames in os.walk(root_output_path):
#                     for filename in filenames:
#                         file_path = os.path.join(foldername, filename)
#                         arcname = os.path.relpath(file_path, root_output_path)
#                         zipf.write(file_path, arcname)
        
#     except Exception as exp:
#         print( exp )
#         abort(500, description=f"Exception occurred while preparing download: {exp}")

#     # Return the file if all good
#     if not os.path.exists(zip_path):
#         abort(500, description="Result ZIP file not found after creation.")

#     try:
#         return send_file(zip_path, as_attachment=True)
#     except Exception as e:
#         abort(500, description=f"Error sending result file: {e}")


def get_job_paths(job_id):
    job_dir = os.path.abspath(f"./data/{job_id}")
    job_path = os.path.join(job_dir, "job_parameters.json")
    status_path = os.path.join(job_dir, "job.status")
    zip_path = os.path.join(job_dir, "download.zip")
    progress_path = os.path.join(job_dir, "progress.json")
    return job_dir, job_path, status_path, zip_path, progress_path

def save_progress(progress_path, progress):
    with FileLock(progress_path + ".lock", timeout=5):
        with open(progress_path, "w") as f:
            json.dump(progress, f)

def load_progress(progress_path):
    try:
        with FileLock(progress_path + ".lock", timeout=5):
            if os.path.exists(progress_path):
                with open(progress_path, "r") as f:
                    return json.load(f)
    except Exception:
        pass
    return {"status": "not_started", "progress": 0}

# ---------- Endpoint: Prepare Download ----------

@app.route('/prepare-download', methods=['POST'])
def prepare_download():
    job_id = request.args.get('id')
    job_dir, job_path, status_path, zip_path, progress_path = get_job_paths(job_id)

    # Return early if already prepared
    if os.path.exists(zip_path):
        save_progress(progress_path, {"status": "ready", "progress": 100})
        return jsonify({"status": "ready", "progress": 100})

    try:
        # ---- Load job parameters ----
        with FileLock(job_path + ".lock", timeout=5):
            with open(job_path, "r") as f:
                job_parameters = json.load(f)

        with FileLock(status_path + ".lock", timeout=5):
            with open(status_path, "r") as f:
                job_status = json.load(f)

        if job_status.get("status") != "completed":
            return jsonify({"status": "not_ready", "message": "Job not completed"}), 409

        corrected_labels = job_parameters.get("corrected_labels", {})
        if not corrected_labels:
            return jsonify({"status": "error", "message": "No labeled data to export"}), 400

        total = len(corrected_labels)
        completed = 0

        with tempfile.TemporaryDirectory() as tmp_dir:
            root_output_path = os.path.join(tmp_dir, "download")

            csv_data = [
                ["F1-Score", str(job_parameters.get("F1_Score", "")), "", ""],
                ["Accuracy-Score", str(job_parameters.get("Accuracy_Score", "")), "", ""],
                ["", "", "", ""],
                ["URL", "Cat1", "Cat1_Prob", "Manual_Label"]
            ]

            for image_path, category in corrected_labels.items():
                completed += 1
                save_progress(progress_path, {
                    "status": "preparing",
                    "progress": int((completed / total) * 100)
                })

                domain_folder = os.path.dirname(image_path)
                domain_name = os.path.basename(domain_folder)
                domain_folder_path = os.path.join( upload_folder , domain_folder)

                csv_data.append([
                    domain_name.replace("_", "."),
                    job_parameters["predicted_labels"][image_path][0],
                    str(round(job_parameters["predicted_labels"][image_path][1] * 100, 2)),
                    category
                ])

                if not os.path.exists(domain_folder_path):
                    continue

                category_path = os.path.join(root_output_path, category)
                os.makedirs(category_path, exist_ok=True)

                shutil.copytree(
                    domain_folder_path,
                    os.path.join(category_path, os.path.basename(domain_folder_path)),
                    dirs_exist_ok=True
                )

            # Save CSV
            df = pd.DataFrame(csv_data, columns=["URL", "Cat1", "Cat1_Prob", "Manual_Label"])
            df.to_csv(os.path.join(root_output_path, "summary.csv"), sep="\t", index=False, header=False)

            # Create ZIP
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for foldername, _, filenames in os.walk(root_output_path):
                    for filename in filenames:
                        file_path = os.path.join(foldername, filename)
                        arcname = os.path.relpath(file_path, root_output_path)
                        zipf.write(file_path, arcname)

        save_progress(progress_path, {"status": "ready", "progress": 100})
        return jsonify({"status": "ready", "progress": 100})

    except Timeout:
        return jsonify({"status": "error", "message": "Resource is locked. Try again later."}), 503
    except Exception as e:
        save_progress(progress_path, {"status": "error", "message": str(e)})
        abort(500, description=f"Error during preparation: {e}")

# ---------- Endpoint: Check Progress ----------

@app.route('/download-status', methods=['GET'])
def download_status():
    job_id = request.args.get('id')
    _, _, _, _, progress_path = get_job_paths(job_id)
    progress = load_progress(progress_path)
    return jsonify(progress)

# ---------- Endpoint: Download File ----------

@app.route('/download', methods=['GET'])
def download_file():
    job_id = request.args.get('id')
    job_dir, _, _, zip_path, _ = get_job_paths(job_id)

    if not os.path.exists(zip_path):
        abort(404, description="ZIP file not found. Please prepare it first.")

    try:
        return send_file(zip_path, as_attachment=True)
    except Exception as e:
        abort(500, description=f"Failed to send file: {e}")






ALLOWED_BASE_DIR = upload_folder

@app.route('/image')
def serve_image():
    image_path = request.args.get('path')
    #print( "image_path:" , image_path )
    full_path = ALLOWED_BASE_DIR + image_path

    if not os.path.isfile(full_path):

        if not os.path.isfile(image_path):
            print( "File does not exist ****" )
            print( "ALLOWED_BASE_DIR:" , ALLOWED_BASE_DIR )
            print( "image_path:" , image_path )
            print( "*****" )
            abort(403)  # Forbidden
        else:
            #File is outside of upload directory let the front-end read it
            full_path = image_path

    mime_type, _ = mimetypes.guess_type(full_path)
    return send_file(full_path, mimetype=mime_type or 'application/octet-stream')


@app.route('/rerun')
def run_job():
    
    job_id = request.args.get('id')
    job_path = f"./data/{job_id}/job_parameters.json"
    lock_path = job_path + ".lock"

    with FileLock(lock_path):
        with open( job_path ) as f:
            job_parameters = json.load( f ) 

    threading.Thread(target=perform_clustering, args=(job_parameters,)).start()
    
    message = "Running"
    return render_template( 'view_job.html', job=job_parameters , message=message )
    

def create_job_path():
    retries = 5  # Set number of retries if the path creation fails
    
    for _ in range(retries):
        # Generate a unique UUID and corresponding job path
        unique_id = str(uuid.uuid4())
        job_path = f"./data/{unique_id}"
        
        try:
            # Try to create the job directory
            os.makedirs(job_path)
            return unique_id, job_path
        except OSError as e:
            # Log the error (you could log this in real applications)
            print(f"Error creating path {job_path}: {e}")
    
    # If directory creation fails after retries, raise an exception or handle it
    raise Exception("Failed to create job directory after several attempts.")




def handle_zip_upload(uploaded_file, upload_folder):
    if uploaded_file:
        filename = uploaded_file.filename
        filepath = os.path.join(upload_folder, filename)
        uploaded_file.save(filepath)

        extract_folder = upload_folder
        os.makedirs(extract_folder, exist_ok=True)

        file_ext = os.path.splitext(filename)[1].lower()

        try:
            if file_ext == '.zip':
                with zipfile.ZipFile(filepath, 'r') as archive:
                    for file in archive.namelist():
                        # Filter only desired extensions
                        _, ext = os.path.splitext(file)
                        if ext.lower() in ['.png', '.html', '.npy', '.txt', '.json']:
                            extract_path = os.path.join(extract_folder, file)

                            # Create subdirectories if needed
                            os.makedirs(os.path.dirname(extract_path), exist_ok=True)

                            with archive.open(file) as source, open(extract_path, 'wb') as target:
                                target.write(source.read())

            elif file_ext == '.7z':
                with py7zr.SevenZipFile(filepath, mode='r') as archive:
                    all_files = archive.getnames()
                    extracted_data = archive.read(all_files)

                    for file in all_files:
                        _, ext = os.path.splitext(file)
                        if ext.lower() in ['.png', '.html', '.npy', '.txt', '.json']:
                            extract_path = os.path.join(extract_folder, file)

                            # Create subdirectories if needed
                            os.makedirs(os.path.dirname(extract_path), exist_ok=True)

                            with open(extract_path, 'wb') as out_file:
                                out_file.write(extracted_data[file].read())

            else:
                print("Unsupported file format:", file_ext)

        except Exception as e:
            print(f"Error while extracting: {e}")




@app.route('/update-category', methods=['POST'])
def update_category():
    data = request.get_json()
    job_id = data.get('job_id', '').strip()
    image_url = data.get('image_url', '').strip()
    category = data.get('category', '').strip()
    operation = data.get('operation', '').strip()
    source = data.get('source', '').strip()

    if not job_id or not image_url or not category:
        return jsonify({"status": "error", "message": "Missing job_id, image_url, or category"}), 400

    cleaned_image_url = image_url.replace("/image?path=", "").strip()
    # print(f"Updating category for '{cleaned_image_url}' to '{category}'")

    job_path = f"./data/{job_id}/job_parameters.json"
    lock_path = job_path + ".lock"

    if not os.path.exists(job_path):
        return jsonify({"status": "error", "message": "Invalid job_id."}), 400

    with FileLock(lock_path):
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
            if (source == "checkbox") :
                checkbox_status[cleaned_image_url] = ""
            

        


        predicted = []
        actual = []
        for key, value_list in predicted_labels.items():
            predicted_label = value_list[0]
            predicted.append(predicted_label)

            actual_label = corrected_labels.get(key, predicted_label)
            actual.append(actual_label)

        # Compute metrics
        Accuracy_Score = round(accuracy_score(actual, predicted) * 100, 2)
        F1_Score = round(f1_score(actual, predicted, average="weighted") * 100, 2)

        # Count actual vs predicted
        predicted_counts = Counter([v[0] for v in predicted_labels.values()])
        corrected_counts = Counter(corrected_labels.values())
        
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

    return jsonify({
        "status": "success",
        "message": "Category updated successfully",
        "labeled_data_counts": labeled_data_counts,
        "accuracy_score": Accuracy_Score,
        "f1_score": F1_Score
    }), 200


@app.route('/update-all-categories', methods=['POST'])
def update_all_categories():

    data = request.get_json()

    job_id = data.get('job_id', '').strip()
    image_urls = data.get('image_urls', [])
    category = data.get('category', '').strip()

    if not job_id or not category or not image_urls:
        return jsonify({"status": "error", "message": "Missing job_id, category, or image_urls"}), 400

    job_path = f"./data/{job_id}/job_parameters.json"
    lock_path = job_path + ".lock"

    if not os.path.exists(job_path):
        return jsonify({"status": "error", "message": "Invalid job_id"}), 400
    try:
        with FileLock(lock_path):
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
            Accuracy_Score = round(accuracy_score(actual, predicted) * 100, 2)
            F1_Score = round(f1_score(actual, predicted, average="weighted") * 100, 2)
    
            # Count actual vs predicted
            predicted_counts = Counter([v[0] for v in predicted_labels.values()])
            corrected_counts = Counter(corrected_labels.values())
    
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
    
        return jsonify({
            "status": "success",
            "message": "Categories updated successfully",
            "labeled_data_counts": labeled_data_counts,
            "accuracy_score": Accuracy_Score,
            "f1_score": F1_Score
        }), 200
        
    except Exception as exp:
        print( "Exception occured:" , exp )
        return jsonify({"status": "error", "message": "Missing job_id, category, or image_urls"}), 400

    

if __name__ == '__main__':
    
    app.run( host="0.0.0.0", port=8080, debug=True)
