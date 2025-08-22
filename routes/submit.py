import collections
import datetime
import filelock
import flask
import glob
import image_functions
import json
import os
import py7zr
import threading
import uuid
import zipfile

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

blueprint = flask.Blueprint('submit', __name__)
@blueprint.route('/submit', methods=['POST'])
def submit():
    upload_folder = flask.current_app.config['UPLOAD_FOLDER']

    # Get the input method selected by the user
    input_method = flask.request.form.get('inputMethod')
    print( "input_method:" , input_method )
    job_parameters = {"input_method" : input_method}


    # Get the ZIP file or folder path
    if input_method == 'zip':

        zip_file = flask.request.files.get('fileUpload')  # Retrieve the uploaded ZIP file
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
        folder_path = flask.request.form.get('folderPath')  # Retrieve the folder path input

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


    job_description = flask.request.form.get('jobDescription')
    print(f'Job Description: {job_description}')
    job_parameters["job_description"] = job_description

    # Get the clustering algorithm selected
    clustering_algorithm = flask.request.form.get('clusteringAlgorithm')
    print(f'Clustering Algorithm: {clustering_algorithm}')
    job_parameters["clustering_algorithm"] = clustering_algorithm

    # Get the number of clusters input
    num_clusters = flask.request.form.get('numClusters')
    print(f'Number of clusters: {num_clusters}')
    job_parameters["num_clusters"] = num_clusters

    # Get the input type (image, text, or both)
    input_type = flask.request.form.get('inputType')
    print(f'Input Type: {input_type}')
    job_parameters["input_type"] = input_type

    # Get the encoding model (image or text encoding based on input type)
    if input_type == 'image':
        image_encoding = flask.request.form.get('imageEncoding')
        print(f'Image Encoding Model: {image_encoding}')
        job_parameters["image_encoding"] = image_encoding

    elif input_type == 'text':
        text_encoding = flask.request.form.get('textEncoding')
        print(f'Text Encoding Model: {text_encoding}')
        job_parameters["text_encoding"] = text_encoding

    else:
        image_encoding = flask.request.form.get('imageEncoding')
        print(f'Image Encoding Model: {image_encoding}')

        text_encoding = flask.request.form.get('textEncoding')
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
            lock = filelock.FileLock(lock_path)
            with lock:
                with open(pred_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        try:
                            mapped_label = (image_functions.category_mapping[ json.loads(content)[0][0] ] , json.loads(content)[0][1] )
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
    labeled_data_counts = { key + f" ({value})":0 for key , value in dict( collections.Counter([v[0] for v in predicted_labels.values()]) ).items() }
    labeled_data_counts[ f"Total ({len(predicted_labels)})" ] = 0
    job_parameters["labeled_data_counts"] = labeled_data_counts


    # Get the current date and time
    job_parameters["job_submission_time"] = datetime.datetime.now().isoformat()

    with open( os.path.join(job_path , "job_parameters.json") , "w" ) as f:
        json.dump( job_parameters , f )

    message = f"Job submitted successfully, with job id {unique_id}."

    threading.Thread(target=image_functions.perform_clustering, args=(job_parameters,upload_folder, )).start()

    return flask.redirect(flask.url_for('jobs.jobs')+f'?message={message}')
