import requests
import base64
from platforms.utils import crop_to_vertical
def post(text: str,  creds: dict, title:str=None, image_path: str = None,) -> str:
    title = title or text
    token = creds.get("access_token")
    board_id = creds.get("board_id")

    # guard checks here
    if not token:
        return "No Acess Token"
    if not board_id:
        return "No board id"
    if not image_path:
        return "A Image is required to post on Instagram"
    
    try:
        image_path = crop_to_vertical(image_path, 'pinterest')
        with open(image_path, 'rb') as image:
            im = image.read()
        b64_string = base64.b64encode(im)
        b64_string = b64_string.decode("utf-8")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        body = {
            "board_id": board_id,
            "title": title,
            'description': text,
            "media_source": {
                "source_type": "image_base64",
                "content_type": "image/jpeg",
                "data": b64_string,
            }
        }

        response = requests.post("https://api.pinterest.com/v5/pins", headers=headers, json=body)
        
        if response.status_code == 201: # what code means success?
            return "✅ Posted!"
        else:
            return f"❌ {response.status_code}: {response.json()}"
    except Exception as e:
        return f"ERROR: \n{e}"