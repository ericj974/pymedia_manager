import logging
import os
import argparse
from PIL import Image
import shutil

CONFIG_PATH_DEFAULT = '/home/ericj/Documents/SachaPhotos'

argparser = argparse.ArgumentParser(
    description='Reduce image size using a target size in bytes')

argparser.add_argument('--dirpath',
                       help='Locations of the folder containing images.',
                       type=str, default=CONFIG_PATH_DEFAULT)


# Extensions supported for images
EXTENSIONS = ['.jpeg', '.jpg', '.png', '.bmp']
# Minimum size
H_MIN = 1080
W_MIN = 1920

def reduce_size(dirpath, target_size = 1000000):
    assert  os.path.exists(dirpath) and os.path.isdir(dirpath), f'Dirpath {dirpath} does not exist or is not a folder !'
    # First create a out folder
    out_foldername = 'out'
    out_dirpath = os.path.join(dirpath, out_foldername)
    if not os.path.exists(out_dirpath):
        os.mkdir(out_dirpath)

    # List files in the folder
    files = [file.path for file in os.scandir(dirpath) if file.is_file()]
    # Filter out non image files
    files =  [filepath for filepath in files if filepath.lower().endswith(tuple(EXTENSIONS))]
    # sort
    files.sort()

    for path in files:
        filename = os.path.basename(path)
        filesize = os.stat(path).st_size
        path_out = os.path.join(out_dirpath, filename)

        # Check the initial size. If ok, just copy the file to out
        if filesize <= target_size:
            shutil.copyfile(path,path_out)
            continue


        # Open images, reduce size and close
        img = Image.open(path)
        # Keep the ration while reducing size
        ratio = img.size[0] / img.size[1]

        height = H_MIN
        width = int(H_MIN / ratio)
        img = img.resize((height,width),Image.ANTIALIAS)
        img.save(path_out, optimize=True, quality=75)

if __name__ == '__main__':
    args = argparser.parse_args()
    # Get the parameters
    dirpath = args.dirpath

    reduce_size(dirpath=dirpath)
