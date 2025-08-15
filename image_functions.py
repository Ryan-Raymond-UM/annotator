# import torch
import gc
import numpy as np
import socket
import json
from sklearn.cluster import KMeans
import datetime
from filelock import FileLock
import os
import traceback

import logging
# Set up basic logging
logging.basicConfig(
    filename='app.log',  # Or use 'logs/app.log'
    level=logging.ERROR,
    format='%(asctime)s [%(levelname)s] %(message)s'
)


categories =   [ 'Accommodations',
                 'Adult_Magazine_News',
                 'Agriculture',
                 'Alcoholic_Products',
                 'Architecture',
                 'Arts_&_Cultural_Events',
                 'Automotive',
                 'Books_eBooks',
                 'CBD_&_Hemp_Products',
                 'Business_&_Commercial',
                 'Connection_Error',
                 'Entertainment_Venues_Activities',
                 'Games',
                 'Nudity',
                 'Parked_Adult',
                 'Parked_Domains',
                 'Adult_Porn',
                 'Sexual_Services',
                 'Shopping_Retail',
                 'Smoking',
                 'Illegal_Activities',
                 'Illegal_Drugs',
                 'Medication',
                 'Marijuana',
                 'Terrorism_Extremists',
                 'Weapons',
                 'Hate_Slander',
                 'Violence',
                 'Advocacy_in_general',
                 'Guns',
                 'Ammunition',
                 'Knives',
                 'Paintball',
                 'Self_Harm',
                 'Abortion',
                 'Adult_Search_Links',
                 'Child_Abuse',
                 'Hacking_Cracking',
                 'Malware',
                 'Remote_Proxies',
                 'Search_Engine_Caches',
                 'Translators',
                 'Remote_Desktop_Control',
                 'Dating',
                 'Weddings_Matrimony',
                 'Market_Rates',
                 'Online_Trading',
                 'Insurance',
                 'Finance_and_Banking',
                 'Cryptocurrency',
                 'Hosted_Payment_Gateways',
                 'Gambling_in_general',
                 'Lottery',
                 'Online_games',
                 'Auctions',
                 'Real_Estate',
                 'IT_Online_Shopping',
                 'Web_based_Chat',
                 'Instant_Messages',
                 'Web_based_Mail',
                 'Email_Subscriptions',
                 'Bulletin_Boards',
                 'IT_Bulletin_Boards',
                 'Personal_Web_Pages_Blogs',
                 'Downloads',
                 'Program_Downloads',
                 'Storage_Services',
                 'Streaming_Media',
                 'Employment',
                 'Career_Advancement',
                 'Side_Business',
                 'Grotesque',
                 'Special_Events',
                 'Popular_Topics',
                 'Drinking',
                 'Fetish',
                 'Sexual_Expression_text',
                 'Costume_Play_Enjoyment',
                 'Occult',
                 'Home_&_Family',
                 'Professional_Sports',
                 'Sports_in_general',
                 'Life_Events',
                 'Travel_&_Tourism',
                 'Public_Agency_Tourism',
                 'Public_Transit',
                 'Music_and_Streaming_Audio',
                 'Horoscope_Astrology_Fortune_Telling',
                 'Entertainer_Celebrity_Pop_Culture',
                 'Dining_Gourmet',
                 'Traditional_Religions',
                 'Religions',
                 'Politics',
                 'Advertisements_Banners',
                 'Sweepstakes_Prizes',
                 'Tracking_Sites',
                 'SPAM',
                 'News',
                 'Computing_&_Internet',
                 'Education',
                 'Government',
                 'Health',
                 'Fitness',
                 'Internet_Telephony',
                 'Military',
                 'Peer_to_Peer_Torrents',
                 'Recreation_&_Hobbies',
                 'Home_&_Garden',
                 'Reference',
                 'Search_Engines_&_Portals',
                 'Sex_Education',
                 'SMS_&_Mobile_Telephony_Services',
                 'Mobile_Apps_&_Publishers',
                 'Spyware',
                 'Content_Delivery_Networks_&_Infrastructure',
                 'Kids_Sites',
                 'Swimsuits_&_Lingerie',
                 'Hosting_Sites',
                 'Philanthropy_&_Non_Profit_Organizations',
                 'Photo_Search_&_Photo_Sharing_Sites',
                 'Ringtones',
                 'Fashion_&_Beauty',
                 'Mobile_App_Stores',
                 'Emoticons',
                 'Mobile_Operators',
                 'Botnets',
                 'Infected_Sites',
                 'Phishing_Sites',
                 'Keyloggers',
                 'Mobile_Malware',
                 'No_Content',
                 'Associations_Trade_Groups_Unions',
                 'BOT_Phone_Home',
                 'DDNS',
                 'Unsupported_URL',
                 'Law',
                 'Local_Communities',
                 'Miscellaneous',
                 'Online_Magazines',
                 'Pets_Veterinarian',
                 'Piracy_&_Copyright_Theft',
                 'Private_IP_Addresses',
                 'Recycling_Environment',
                 'Science',
                 'Society_&_Culture',
                 'Transport_Services_&_Freight',
                 'Photography_&_Film',
                 'Museums_&_History',
                 'eLearning',
                 'Social_Networks_in_General',
                 'DoH_DoT',
                 'Infrastructure_&_Backend_Services',
                 'Newly_Registered_Domains',
                 'Fireworks',
                 'Cyberbullying',
                 'VPN',
                 'Web_Conferencing',
                 'Fandom',
                 'Child_Safety_and_Government_Help_Lines',
                 'Self_Help',
                 'Code_Repositories',
                 'Cheating',
                 'Artificial_Intelligence',
                 'Facebook',
                 'Facebook_Posting',
                 'Facebook_Commenting',
                 'Facebook_Friends',
                 'Facebook_Photo Upload',
                 'Facebook_Events',
                 'Facebook_Apps',
                 'Facebook_Chat',
                 'Facebook_Questions',
                 'Facebook_Video Upload',
                 'Facebook_Groups',
                 'Facebook_Games',
                 'LinkedIn',
                 'LinkedIn_Updates',
                 'LinkedIn_Mail',
                 'LinkedIn_Connections',
                 'LinkedIn_Jobs',
                 'Twitter',
                 'Twitter_Posting',
                 'Twitter_Mail',
                 'Twitter_Follow',
                 'YouTube',
                 'YouTube_Commenting',
                 'YouTube_Video Upload',
                 'YouTube_Sharing',
                 'Instagram',
                 'Instagram_Upload',
                 'Instagram_Commenting',
                 'Instagram_Private Message',
                 'Tumblr',
                 'Tumblr_Posting',
                 'Tumblr_Commenting',
                 'Tumblr_Photo_or_Video_Upload',
                 'Google+',
                 'Google+_Posting',
                 'Google+_Commenting',
                 'Google+_Photo_Upload',
                 'Google+_Video_Upload',
                 'Google+_Video_Chat',
                 'Pinterest',
                 'Pinterest_Pin',
                 'Pinterest_Commenting',
                 'Ask_fm',
                 'Ask_fm_Ask',
                 'Ask_fm_Answer',
                 'Wordpress',
                 'Wordpress_Posting',
                 'Wordpress_Upload',
                 'TikTok',
                 'other']


category_num_2_text =  { 0: 'Accommodations',
                         1: 'Adult_Magazine_News',
                         2: 'Agriculture',
                         3: 'Alcoholic_Products',
                         4: 'Architecture',
                         5: 'Arts_&_Cultural_Events',
                         6: 'Automotive',
                         7: 'Books_eBooks',
                         8: 'CBD_&_Hemp_Products',
                         9: 'Business_&_Commercial',
                         10: 'Connection_Error',
                         11: 'Entertainment_Venues_Activities',
                         12: 'Games',
                         13: 'Nudity',
                         14: 'Parked_Adult',
                         15: 'Parked_Domains',
                         16: 'Adult_Porn',
                         17: 'Sexual_Services',
                         18: 'Shopping_Retail',
                         19: 'Smoking',
                         20: 'Illegal_Activities',
                         21: 'Illegal_Drugs',
                         22: 'Medication',
                         23: 'Marijuana',
                         24: 'Terrorism_Extremists',
                         25: 'Weapons',
                         26: 'Hate_Slander',
                         27: 'Violence',
                         28: 'Advocacy_in_general',
                         29: 'Guns',
                         30: 'Ammunition',
                         31: 'Knives',
                         32: 'Paintball',
                         33: 'Self_Harm',
                         34: 'Abortion',
                         35: 'Adult_Search_Links',
                         36: 'Child_Abuse',
                         37: 'Hacking_Cracking',
                         38: 'Malware',
                         39: 'Remote_Proxies',
                         40: 'Search_Engine_Caches',
                         41: 'Translators',
                         42: 'Remote_Desktop_Control',
                         43: 'Dating',
                         44: 'Weddings_Matrimony',
                         45: 'Market_Rates',
                         46: 'Online_Trading',
                         47: 'Insurance',
                         48: 'Finance_and_Banking',
                         49: 'Cryptocurrency',
                         50: 'Hosted_Payment_Gateways',
                         51: 'Gambling_in_general',
                         52: 'Lottery',
                         53: 'Online_games',
                         54: 'Auctions',
                         55: 'Real_Estate',
                         56: 'IT_Online_Shopping',
                         57: 'Web_based_Chat',
                         58: 'Instant_Messages',
                         59: 'Web_based_Mail',
                         60: 'Email_Subscriptions',
                         61: 'Bulletin_Boards',
                         62: 'IT_Bulletin_Boards',
                         63: 'Personal_Web_Pages_Blogs',
                         64: 'Downloads',
                         65: 'Program_Downloads',
                         66: 'Storage_Services',
                         67: 'Streaming_Media',
                         68: 'Employment',
                         69: 'Career_Advancement',
                         70: 'Side_Business',
                         71: 'Grotesque',
                         72: 'Special_Events',
                         73: 'Popular_Topics',
                         74: 'Drinking',
                         75: 'Fetish',
                         76: 'Sexual_Expression_text',
                         77: 'Costume_Play_Enjoyment',
                         78: 'Occult',
                         79: 'Home_&_Family',
                         80: 'Professional_Sports',
                         81: 'Sports_in_general',
                         82: 'Life_Events',
                         83: 'Travel_&_Tourism',
                         84: 'Public_Agency_Tourism',
                         85: 'Public_Transit',
                         86: 'Music_and_Streaming_Audio',
                         87: 'Horoscope_Astrology_Fortune_Telling',
                         88: 'Entertainer_Celebrity_Pop_Culture',
                         89: 'Dining_Gourmet',
                         90: 'Traditional_Religions',
                         91: 'Religions',
                         92: 'Politics',
                         93: 'Advertisements_Banners',
                         94: 'Sweepstakes_Prizes',
                         95: 'Tracking_Sites',
                         96: 'SPAM',
                         97: 'News',
                         98: 'Computing_&_Internet',
                         99: 'Education',
                         100: 'Government',
                         101: 'Health',
                         102: 'Fitness',
                         103: 'Internet_Telephony',
                         104: 'Military',
                         105: 'Peer_to_Peer_Torrents',
                         106: 'Recreation_&_Hobbies',
                         107: 'Home_&_Garden',
                         108: 'Reference',
                         109: 'Search_Engines_&_Portals',
                         110: 'Sex_Education',
                         111: 'SMS_&_Mobile_Telephony_Services',
                         112: 'Mobile_Apps_&_Publishers',
                         113: 'Spyware',
                         114: 'Content_Delivery_Networks_&_Infrastructure',
                         115: 'Kids_Sites',
                         116: 'Swimsuits_&_Lingerie',
                         117: 'Hosting_Sites',
                         118: 'Philanthropy_&_Non_Profit_Organizations',
                         119: 'Photo_Search_&_Photo_Sharing_Sites',
                         120: 'Ringtones',
                         121: 'Fashion_&_Beauty',
                         122: 'Mobile_App_Stores',
                         123: 'Emoticons',
                         124: 'Mobile_Operators',
                         125: 'Botnets',
                         126: 'Infected_Sites',
                         127: 'Phishing_Sites',
                         128: 'Keyloggers',
                         129: 'Mobile_Malware',
                         130: 'No_Content',
                         131: 'Associations_Trade_Groups_Unions',
                         132: 'BOT_Phone_Home',
                         133: 'DDNS',
                         134: 'Unsupported_URL',
                         135: 'Law',
                         136: 'Local_Communities',
                         137: 'Miscellaneous',
                         138: 'Online_Magazines',
                         139: 'Pets_Veterinarian',
                         140: 'Piracy_&_Copyright_Theft',
                         141: 'Private_IP_Addresses',
                         142: 'Recycling_Environment',
                         143: 'Science',
                         144: 'Society_&_Culture',
                         145: 'Transport_Services_&_Freight',
                         146: 'Photography_&_Film',
                         147: 'Museums_&_History',
                         148: 'eLearning',
                         149: 'Social_Networks_in_General',
                         150: 'DoH_DoT',
                         151: 'Infrastructure_&_Backend_Services',
                         152: 'Newly_Registered_Domains',
                         153: 'Fireworks',
                         154: 'Cyberbullying',
                         155: 'VPN',
                         156: 'Web_Conferencing',
                         157: 'Fandom',
                         158: 'Child_Safety_and_Government_Help_Lines',
                         159: 'Self_Help',
                         160: 'Code_Repositories',
                         161: 'Cheating',
                         162: 'Artificial_Intelligence',
                         163: 'Facebook',
                         164: 'Facebook_Posting',
                         165: 'Facebook_Commenting',
                         166: 'Facebook_Friends',
                         167: 'Facebook_Photo Upload',
                         168: 'Facebook_Events',
                         169: 'Facebook_Apps',
                         170: 'Facebook_Chat',
                         171: 'Facebook_Questions',
                         172: 'Facebook_Video Upload',
                         173: 'Facebook_Groups',
                         174: 'Facebook_Games',
                         175: 'LinkedIn',
                         176: 'LinkedIn_Updates',
                         177: 'LinkedIn_Mail',
                         178: 'LinkedIn_Connections',
                         179: 'LinkedIn_Jobs',
                         180: 'Twitter',
                         181: 'Twitter_Posting',
                         182: 'Twitter_Mail',
                         183: 'Twitter_Follow',
                         184: 'YouTube',
                         185: 'YouTube_Commenting',
                         186: 'YouTube_Video Upload',
                         187: 'YouTube_Sharing',
                         188: 'Instagram',
                         189: 'Instagram_Upload',
                         190: 'Instagram_Commenting',
                         191: 'Instagram_Private Message',
                         192: 'Tumblr',
                         193: 'Tumblr_Posting',
                         194: 'Tumblr_Commenting',
                         195: 'Tumblr_Photo_or_Video_Upload',
                         196: 'Google+',
                         197: 'Google+_Posting',
                         198: 'Google+_Commenting',
                         199: 'Google+_Photo_Upload',
                         200: 'Google+_Video_Upload',
                         201: 'Google+_Video_Chat',
                         202: 'Pinterest',
                         203: 'Pinterest_Pin',
                         204: 'Pinterest_Commenting',
                         205: 'Ask_fm',
                         206: 'Ask_fm_Ask',
                         207: 'Ask_fm_Answer',
                         208: 'Wordpress',
                         209: 'Wordpress_Posting',
                         210: 'Wordpress_Upload',
                         211: 'TikTok',
                         212: 'other'}

category_text_2_num =  { 'Accommodations': 0,
                         'Adult_Magazine_News': 1,
                         'Agriculture': 2,
                         'Alcoholic_Products': 3,
                         'Architecture': 4,
                         'Arts_&_Cultural_Events': 5,
                         'Automotive': 6,
                         'Books_eBooks': 7,
                         'CBD_&_Hemp_Products': 8,
                         'Business_&_Commercial': 9,
                         'Connection_Error': 10,
                         'Entertainment_Venues_Activities': 11,
                         'Games': 12,
                         'Nudity': 13,
                         'Parked_Adult': 14,
                         'Parked_Domains': 15,
                         'Adult_Porn': 16,
                         'Sexual_Services': 17,
                         'Shopping_Retail': 18,
                         'Smoking': 19,
                         'Illegal_Activities': 20,
                         'Illegal_Drugs': 21,
                         'Medication': 22,
                         'Marijuana': 23,
                         'Terrorism_Extremists': 24,
                         'Weapons': 25,
                         'Hate_Slander': 26,
                         'Violence': 27,
                         'Advocacy_in_general': 28,
                         'Guns': 29,
                         'Ammunition': 30,
                         'Knives': 31,
                         'Paintball': 32,
                         'Self_Harm': 33,
                         'Abortion': 34,
                         'Adult_Search_Links': 35,
                         'Child_Abuse': 36,
                         'Hacking_Cracking': 37,
                         'Malware': 38,
                         'Remote_Proxies': 39,
                         'Search_Engine_Caches': 40,
                         'Translators': 41,
                         'Remote_Desktop_Control': 42,
                         'Dating': 43,
                         'Weddings_Matrimony': 44,
                         'Market_Rates': 45,
                         'Online_Trading': 46,
                         'Insurance': 47,
                         'Finance_and_Banking': 48,
                         'Cryptocurrency': 49,
                         'Hosted_Payment_Gateways': 50,
                         'Gambling_in_general': 51,
                         'Lottery': 52,
                         'Online_games': 53,
                         'Auctions': 54,
                         'Real_Estate': 55,
                         'IT_Online_Shopping': 56,
                         'Web_based_Chat': 57,
                         'Instant_Messages': 58,
                         'Web_based_Mail': 59,
                         'Email_Subscriptions': 60,
                         'Bulletin_Boards': 61,
                         'IT_Bulletin_Boards': 62,
                         'Personal_Web_Pages_Blogs': 63,
                         'Downloads': 64,
                         'Program_Downloads': 65,
                         'Storage_Services': 66,
                         'Streaming_Media': 67,
                         'Employment': 68,
                         'Career_Advancement': 69,
                         'Side_Business': 70,
                         'Grotesque': 71,
                         'Special_Events': 72,
                         'Popular_Topics': 73,
                         'Drinking': 74,
                         'Fetish': 75,
                         'Sexual_Expression_text': 76,
                         'Costume_Play_Enjoyment': 77,
                         'Occult': 78,
                         'Home_&_Family': 79,
                         'Professional_Sports': 80,
                         'Sports_in_general': 81,
                         'Life_Events': 82,
                         'Travel_&_Tourism': 83,
                         'Public_Agency_Tourism': 84,
                         'Public_Transit': 85,
                         'Music_and_Streaming_Audio': 86,
                         'Horoscope_Astrology_Fortune_Telling': 87,
                         'Entertainer_Celebrity_Pop_Culture': 88,
                         'Dining_Gourmet': 89,
                         'Traditional_Religions': 90,
                         'Religions': 91,
                         'Politics': 92,
                         'Advertisements_Banners': 93,
                         'Sweepstakes_Prizes': 94,
                         'Tracking_Sites': 95,
                         'SPAM': 96,
                         'News': 97,
                         'Computing_&_Internet': 98,
                         'Education': 99,
                         'Government': 100,
                         'Health': 101,
                         'Fitness': 102,
                         'Internet_Telephony': 103,
                         'Military': 104,
                         'Peer_to_Peer_Torrents': 105,
                         'Recreation_&_Hobbies': 106,
                         'Home_&_Garden': 107,
                         'Reference': 108,
                         'Search_Engines_&_Portals': 109,
                         'Sex_Education': 110,
                         'SMS_&_Mobile_Telephony_Services': 111,
                         'Mobile_Apps_&_Publishers': 112,
                         'Spyware': 113,
                         'Content_Delivery_Networks_&_Infrastructure': 114,
                         'Kids_Sites': 115,
                         'Swimsuits_&_Lingerie': 116,
                         'Hosting_Sites': 117,
                         'Philanthropy_&_Non_Profit_Organizations': 118,
                         'Photo_Search_&_Photo_Sharing_Sites': 119,
                         'Ringtones': 120,
                         'Fashion_&_Beauty': 121,
                         'Mobile_App_Stores': 122,
                         'Emoticons': 123,
                         'Mobile_Operators': 124,
                         'Botnets': 125,
                         'Infected_Sites': 126,
                         'Phishing_Sites': 127,
                         'Keyloggers': 128,
                         'Mobile_Malware': 129,
                         'No_Content': 130,
                         'Associations_Trade_Groups_Unions': 131,
                         'BOT_Phone_Home': 132,
                         'DDNS': 133,
                         'Unsupported_URL': 134,
                         'Law': 135,
                         'Local_Communities': 136,
                         'Miscellaneous': 137,
                         'Online_Magazines': 138,
                         'Pets_Veterinarian': 139,
                         'Piracy_&_Copyright_Theft': 140,
                         'Private_IP_Addresses': 141,
                         'Recycling_Environment': 142,
                         'Science': 143,
                         'Society_&_Culture': 144,
                         'Transport_Services_&_Freight': 145,
                         'Photography_&_Film': 146,
                         'Museums_&_History': 147,
                         'eLearning': 148,
                         'Social_Networks_in_General': 149,
                         'DoH_DoT': 150,
                         'Infrastructure_&_Backend_Services': 151,
                         'Newly_Registered_Domains': 152,
                         'Fireworks': 153,
                         'Cyberbullying': 154,
                         'VPN': 155,
                         'Web_Conferencing': 156,
                         'Fandom': 157,
                         'Child_Safety_and_Government_Help_Lines': 158,
                         'Self_Help': 159,
                         'Code_Repositories': 160,
                         'Cheating': 161,
                         'Artificial_Intelligence': 162,
                         'Facebook': 163,
                         'Facebook_Posting': 164,
                         'Facebook_Commenting': 165,
                         'Facebook_Friends': 166,
                         'Facebook_Photo Upload': 167,
                         'Facebook_Events': 168,
                         'Facebook_Apps': 169,
                         'Facebook_Chat': 170,
                         'Facebook_Questions': 171,
                         'Facebook_Video Upload': 172,
                         'Facebook_Groups': 173,
                         'Facebook_Games': 174,
                         'LinkedIn': 175,
                         'LinkedIn_Updates': 176,
                         'LinkedIn_Mail': 177,
                         'LinkedIn_Connections': 178,
                         'LinkedIn_Jobs': 179,
                         'Twitter': 180,
                         'Twitter_Posting': 181,
                         'Twitter_Mail': 182,
                         'Twitter_Follow': 183,
                         'YouTube': 184,
                         'YouTube_Commenting': 185,
                         'YouTube_Video Upload': 186,
                         'YouTube_Sharing': 187,
                         'Instagram': 188,
                         'Instagram_Upload': 189,
                         'Instagram_Commenting': 190,
                         'Instagram_Private Message': 191,
                         'Tumblr': 192,
                         'Tumblr_Posting': 193,
                         'Tumblr_Commenting': 194,
                         'Tumblr_Photo_or_Video_Upload': 195,
                         'Google+': 196,
                         'Google+_Posting': 197,
                         'Google+_Commenting': 198,
                         'Google+_Photo_Upload': 199,
                         'Google+_Video_Upload': 200,
                         'Google+_Video_Chat': 201,
                         'Pinterest': 202,
                         'Pinterest_Pin': 203,
                         'Pinterest_Commenting': 204,
                         'Ask_fm': 205,
                         'Ask_fm_Ask': 206,
                         'Ask_fm_Answer': 207,
                         'Wordpress': 208,
                         'Wordpress_Posting': 209,
                         'Wordpress_Upload': 210,
                         'TikTok': 211,
                         'other': 212}



category_mapping = {'accommodation': 'Accommodations',
                    'agriculture': 'Agriculture',
                    'alcohol': 'Alcoholic_Products',
                    'architecture': 'Architecture',
                    'arts_and_culture': 'Arts_&_Cultural_Events',
                    'automotive': 'Automotive',
                    'books': 'Books_eBooks',
                    'cbd_hemp': 'CBD_&_Hemp_Products',
                    'commercial': 'Business_&_Commercial',
                    'connection_error': "Connection_Error",
                    'entertainment': 'Entertainment_Venues_Activities',
                    'gambling': 'Gambling_in_general',
                    'games': 'Games',
                    'parked_domain': 'Parked_Domains',
                    'porn': 'Adult_Porn',
                    'sexual_service': 'Sexual_Services',
                    'shopping': 'Shopping_Retail',
                    'smoking': 'Smoking'
                    }


def read_embeddings(all_images_path):
    
    try:
        all_embeddings = []
        for image_path in all_images_path:
            embedding_path = image_path.replace(".png", ".img.npy")
            lock_path = embedding_path + ".lock"
            with FileLock(lock_path):
                all_embeddings.append( np.load(embedding_path) )
                
    except Exception:
        print("Exception occurred while reading embeddings.")
        traceback.print_exc()
    
    return all_embeddings


def update_job_status(job_parameters, status_update={}):
    """
    Updates the job status in a thread-safe manner by locking the file before reading/writing.

    Args:
        job_parameters (dict): Dictionary with job parameters including 'job_submission_time' and 'images_path_list'.
        status_update (dict): Dictionary containing the status updates to be applied.
    
    Returns:
        bool: Returns True if the status was successfully updated, False if an error occurred.
    """

    status_file_path = os.path.join( job_parameters["job_path"], 'job.status')
    
    # Create a lock for the status file to avoid race conditions
    lock_path = status_file_path + ".lock"
    lock = FileLock(lock_path)

    try:
        # Acquire the lock before reading/writing to the file
        with lock:
            # Read the existing job status (if it exists)
            try:
                with open(status_file_path, "r") as status_file:
                    job_status = json.load(status_file)
                    
            except (FileNotFoundError, json.JSONDecodeError):
                # If the file does not exist or is empty, create a new status dictionary
                job_status = {
                    "status": "running",
                    "job_start_time": job_parameters["job_submission_time"],
                    "job_end_time": "",
                    "total_progress": "0.5%",
                    "converting_images_to_embeddings_progress": "1%",
                    "start_time_converting_images_to_embeddings": datetime.datetime.now().isoformat(),
                    "end_time_converting_images_to_embeddings": "",
                    "time_taken_to_compute_embeddings": "0s",
                    "images_processed_for_embeddings": 0,
                    "total_images": len(job_parameters["images_path_list"]),
                    "gpu_memory_usage_converting_images": "0MB",
                    "performing_clustering_progress": "0%",
                    "start_time_performing_clustering": "",
                    "end_time_performing_clustering": "",
                    "time_taken_to_perform_clustering": "0s",
                    "gpu_memory_usage_clustering": "0MB",
                    "job_status_message": "Converting images to embeddings.",
                    "estimated_time_left": "Unknown",
                }

            # Update job status with the new data
            job_status.update(status_update)

            if "end_time_converting_images_to_embeddings" in status_update:
                # compute end-start difference
                start = datetime.datetime.fromisoformat(job_status["start_time_converting_images_to_embeddings"])
                end   = datetime.datetime.fromisoformat(job_status["end_time_converting_images_to_embeddings"])
                time_taken = (end - start).total_seconds()  # or just (end - start) if you want timedelta
                job_status["time_taken_to_compute_embeddings"] = time_taken


            if "end_time_performing_clustering" in status_update:
                # compute end-start difference
                # compute end-start difference
                start = datetime.datetime.fromisoformat(job_status["start_time_performing_clustering"])
                end   = datetime.datetime.fromisoformat(job_status["end_time_performing_clustering"])
                time_taken = (end - start).total_seconds()  # or just (end - start) if you want timedelta
                job_status["time_taken_to_perform_clustering"] = time_taken
                
            
            # Save the updated status back to the file
            with open(status_file_path, "w") as status_file:
                json.dump(job_status, status_file, indent=4)

        return True

    except Exception as e:
        print(f"Error updating job status: {e}")
        return False




def perform_clustering(job_parameters , upload_folder ):
    try:
        update_job_status(job_parameters)

        images_path_list = job_parameters["images_path_list"]
        batch_size = 50
        total_images = len(images_path_list)
        all_embeddings = []

        for i in range(0, total_images, batch_size):
            batch = images_path_list[i:i + batch_size]
            batch_embedding = read_embeddings(batch)  # Fixed: changed from image_paths to batch

            if ( i == 0 ) and ( len(batch_embedding)>0 ):
                print("batch_embedding:", batch_embedding[0].shape)

            all_embeddings.extend(batch_embedding)

            # Progress calculation
            processed = i + len(batch)
            progress_percent = int((processed / total_images) * 100)

            status_update = {
                "total_progress": f"{int(progress_percent / 2)}%",
                "converting_images_to_embeddings_progress": f"{progress_percent}%",
                "images_processed_for_embeddings": processed,
                "job_status_message": f"Converting images to embeddings: {processed}/{total_images}"
            }
            update_job_status(job_parameters, status_update)

        status_update = {
            "total_progress": "50%",
            "converting_images_to_embeddings_progress": "100%",
            "end_time_converting_images_to_embeddings": datetime.datetime.now().isoformat(),
            "images_processed_for_embeddings": len(images_path_list),
            "performing_clustering_progress": "1%",
            "start_time_performing_clustering": datetime.datetime.now().isoformat(),
            "job_status_message": "Performing clustering.",
        }
        update_job_status(job_parameters, status_update)

        images_embeddings = np.array(all_embeddings, dtype=float)

        print("images_embeddings:", images_embeddings.shape)

        # Use scikit-learn's KMeans
        kmeans = KMeans(n_clusters=int(job_parameters["num_clusters"]), random_state=42, init='k-means++')
        kmeans.fit(images_embeddings)

        status_update = {
            "total_progress": "75%",
            "performing_clustering_progress": "50%",
        }
        update_job_status(job_parameters, status_update)

        pred_categorize = kmeans.predict(images_embeddings)

        status_update = {
            "total_progress": "95%",
            "performing_clustering_progress": "90%",
        }
        update_job_status(job_parameters, status_update)

        distances = kmeans.transform(images_embeddings)

        status_update = {
            "total_progress": "98%",
            "performing_clustering_progress": "95%",
        }
        update_job_status(job_parameters, status_update)

        # Softmax conversion of distances to probabilities
        def softmax(x):
            e_x = np.exp(x - np.max(x, axis=1, keepdims=True))  # Numerical stability
            return e_x / e_x.sum(axis=1, keepdims=True)

        probabilities = softmax(-distances)
        probabilities = np.max(probabilities, axis=1)

        status_update = {
            "status": "completed",
            "total_progress": "100%",
            "performing_clustering_progress": "100%",
            "end_time_performing_clustering": datetime.datetime.now().isoformat(),
            "job_status_message": "All jobs have been successfully completed.",
        }
        update_job_status(job_parameters, status_update)

        clusters = {c: [] for c in range(int(job_parameters["num_clusters"]))}

        for i, category in enumerate(pred_categorize):
            remove_path = upload_folder
            clusters[int(category)].append(
                job_parameters["images_path_list"][i].replace(remove_path, "")
            )

        job_parameters["clusters"] = clusters

        job_path = f"./data/{job_parameters['job_id']}/job_parameters.json"
        lock_path = job_path + ".lock"

        with FileLock(lock_path):
            with open(job_path, "w") as f:
                json.dump(job_parameters, f)

    except Exception as exp:
        status_update = {
            "status": "Error",
            "job_status_message": str(exp)
        }
        update_job_status(job_parameters, status_update)
        logging.error("Error in running the clustering code.", exc_info=True)
