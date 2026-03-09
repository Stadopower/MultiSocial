from atproto import Client
import os
import traceback
from platforms.utils import check_image_size

def post(text:str, creds:dict, image_paths:list=None) -> str:
    # Login
    handle, pw = creds.get("handle"), creds.get("app_password")
    picture_size_limit = 1 # mb
    
    if handle == None or handle == "":
        return "Missing Handle"
    if pw == None:
        return "Missing Password"
    
    try:
        client = Client()
        client.login(handle, pw)
        if image_paths == None or image_paths == []:
            client.send_post(text=text)
            return "✅ Posted!"

        for i, image in enumerate(image_paths):
            if check_image_size(image, picture_size_limit):
                return f"ERROR:\nImage exceeds size limit of {picture_size_limit} mb: {os.path.basename(image)}"
            with open(image, "rb") as image:
                image_paths[i] = image.read()
                if i > 3:
                    break
        if len(image_paths) == 1:
            client.send_image(text=text, image=image_paths[0], image_alt="")
        else:
            client.send_images(text=text, images=image_paths[:4], image_alts=[""])
        return "✅ Posted!"
    
    except Exception as e:
        print(traceback.format_exc())
        return f"ERROR \n{traceback.format_exc()}"
