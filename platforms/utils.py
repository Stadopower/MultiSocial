# Utility Functions
from PIL import Image
import os

def crop_to_vertical(image_path:str, app_name:str):
    """
    Function that Crops and Image to the correct format for the specified social Media. Assumes Input is 16:9.

    Attributes:
    image_path: String where the Image is located
    app_name: lowercase Name of the Socialmedia to post to. (Instagram or Pinterest)
    """
    im = Image.open(image_path)
    path, format = os.path.splitext(image_path)
    width, height = im.width, im.height

    if app_name == 'instagram':
        # Instagram: 1080x1350 4:5
        half_crop = (width - (height * 0.8)) / 2
        box = (0+half_crop, 0, width-half_crop, height)
        im = im.crop(box=box)
        im.save(path+'_insta'+format)
        return f"{path}_insta{format}"
    
    if app_name =='pinterest':
        # Pinterest: 1000x1500 2:3
        new_width = height*(2/3)
        half_crop = (width-new_width)/2
        box = (0+half_crop, 0, width-half_crop, height)
        im = im.crop(box=box)
        im.save(path+'_pint'+format)
        return f"{path}_pint{format}"


if __name__ == "__main__":
    image_path = "images/test.jpg"
    app_name = 'pinterest'
    crop_to_vertical(image_path, app_name)


