from tweepy import Client, OAuth1UserHandler, API
from platforms.utils import check_image_size
import os


def post(text:str, creds:dict, image_paths:list=None) -> str:
    picture_size_limit = 5 # mb
    api_key, api_secret = creds.get("api_key"), creds.get("api_secret")
    access_token, access_token_secret = creds.get("access_token"), creds.get("access_token_secret")

    if not api_key or not api_secret:
        return "API Key missing"
    if not access_token or not access_token_secret:
        return "Access Token Missing"
    
    try:
        client = Client(consumer_key=api_key, consumer_secret=api_secret,
                         access_token=access_token, access_token_secret=access_token_secret)
        
        if image_paths == None:
            client.create_tweet(text=text)
        else:            
            auth = OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
            v1client = API(auth)

            if len(image_paths) == 1:
                if check_image_size(image_paths[0], picture_size_limit):
                        return f"ERROR: \nImage exceeds size limit of {picture_size_limit} mb:{os.path.basename(image_paths[0])}"
                uploaded_image = v1client.media_upload(image_paths[0])
                client.create_tweet(text=text, media_ids=[uploaded_image.media_id])

            else:
                media_ids = []
                for i, image in enumerate(image_paths):
                    if check_image_size(image) > picture_size_limit:
                        return f"ERROR: \nImage exceeds size limit of {picture_size_limit} mb:{os.path.basename(image)}"
                    
                    # Only use the first 4 Pictures
                    if i >= 4:
                        break

                    uploaded = v1client.media_upload(image)
                    media_ids.append(uploaded.media_id)
                    

                client.create_tweet(text=text, media_ids=media_ids)
        return "✅ Posted!"

    except Exception as e:
        return f"ERROR: \n{e}"
