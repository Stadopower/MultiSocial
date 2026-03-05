import instagrapi
from instagrapi.exceptions import ChallengeRequired
import os
from platforms.utils import crop_to_vertical
import time

def handle_challenge(client, last_json):
    client.challenge_resolve(last_json)
    input("Approve the login on your Instagram app, then press Enter to continue...")
    return True

def post(text:str, creds:dict, image_path:str):
    username, password = creds.get('username'), creds.get('password')

    if not username or not password:
        return "Username or Password Missing"
    if not image_path:
        return "A Image is required to post on Instagram"
    # Cropping image
    
    client = instagrapi.Client()
    try:
        image_path = crop_to_vertical(image_path, 'instagram')

        SESSION_FILE = "instagram_session.json"

        if os.path.exists(SESSION_FILE):
            client.load_settings(SESSION_FILE)

        client.challenge_code_handler = handle_challenge

        client.login(username, password)
        client.dump_settings(SESSION_FILE)
        time.sleep(2)
        client.photo_upload(image_path, caption=text)
        return "Posted!"
    except Exception as e:
        return f"ERROR \n{e}"
