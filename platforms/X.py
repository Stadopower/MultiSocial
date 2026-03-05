from tweepy import Client, OAuth1UserHandler, API


def post(text:str, creds:dict, image_path:str=None) -> str:
    api_key, api_secret = creds.get("api_key"), creds.get("api_secret")
    access_token, access_token_secret = creds.get("access_token"), creds.get("access_token_secret")

    if not api_key or not api_secret:
        return "API Key missing"
    if not access_token or not access_token_secret:
        return "Access Token Missing"
    
    try:
        client = Client(consumer_key=api_key, consumer_secret=api_secret,
                         access_token=access_token, access_token_secret=access_token_secret)
        
        if image_path == None:
            client.create_tweet(text=text)
        else:
            auth = OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
            v1client = API(auth)
            uploaded_image = v1client.media_upload(image_path)
            client.create_tweet(text=text, media_ids=[uploaded_image.media_id])

    except Exception as e:
        return f"ERROR: \n{e}"
