import instagrapi
import os
import time
import traceback
from pathlib import Path
from platforms.utils import crop_to_vertical

def handle_challenge(client, last_json):
    client.challenge_resolve(last_json)
    input("Approve the login on your Instagram app, then press Enter to continue...")
    return True

def post(text:str, creds:dict, image_paths):
    username, password = creds.get('username'), creds.get('password')
    images = []
    if not username or not password:
        return "Username or Password Missing"
    if not image_paths:
        return "A Image is required to post on Instagram"
    # Cropping image
    
    client = instagrapi.Client()
    try:
        for i, image in enumerate(image_paths):
            image = Path(crop_to_vertical(image, 'instagram'))
            images.append(image)
            if i > 9:
                break

        SESSION_FILE = "instagram_session.json"

        if os.path.exists(SESSION_FILE):
            client.load_settings(SESSION_FILE)

        client.challenge_code_handler = handle_challenge

        client.login(username, password)
        client.dump_settings(SESSION_FILE)
        time.sleep(2)
        if len(images) == 1:
            client.photo_upload(path=images[0], caption=text)
        else:
            client.album_upload(paths=images, caption=text)

        return "Posted!"
    except Exception as e:

        return f"ERROR \n{traceback.format_exc()}"
