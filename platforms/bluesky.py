from atproto import Client
import os
#TODO: Handle Multiple pictures
def post(text:str, creds:dict, image_path:str=None) -> str:
    # Login
    handle, pw = creds.get("handle"), creds.get("app_password")
    
    if handle == None:
        return "Missing Handle"
    if pw == None:
        return "Missing Password"
    try:
        client = Client()
        client.login(handle, pw)
        
        if image_path == None:
            client.send_post(text=text)
        else:
            with open(image_path, "rb") as image:
                image_data = image.read()
            client.send_image(text=text, image=image_data, image_alt="")
        return "Posted!"
    
    except Exception as e:
        return f"ERROR: \n{e}"
