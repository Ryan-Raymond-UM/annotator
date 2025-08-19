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
