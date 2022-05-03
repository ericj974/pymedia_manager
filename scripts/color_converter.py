import os
import argparse
import numpy as np
import cv2

from PIL import Image

COLOR_DIC = {
    'red' : (165,39,20),
    'green': (15,157,88)
}

# Main arguments that can override the config file parameters
argparser = argparse.ArgumentParser(description='Convert a white BG and black foreground into desired color')
argparser.add_argument('--input', '-i', help='Input file', type=str, default='/home/ericj/Downloads/coffeeshop.png')
argparser.add_argument('--color', help='Output color', type=str, default='red')

def main(file, color):
    # read and convert file
    assert os.path.exists(file), "File does not exist !"

    # BGR
    img = cv2.imread(file)
    img =  cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    rgb = COLOR_DIC[color]
    thresh = 150
    img_out = np.stack([(img <= thresh)*rgb[2], (img <= thresh)*rgb[1], (img <= thresh)*rgb[0], (img <= thresh)*255], axis=2)
    img_out = img_out + np.stack([(img > thresh)*255, (img > thresh)*255, (img > thresh)*255, (img > thresh)*0], axis=2)
    img_out = img_out.astype('uint8')

    # Save
    filename = os.path.splitext(os.path.basename(file))[0]
    file_out = os.path.join(os.path.dirname(file), filename + "_" + color + '.png')
    if os.path.exists(file_out):
        os.remove(file_out)
    cv2.imwrite(file_out, img_out)

if __name__ == '__main__':
    args = argparser.parse_args()
    file = args.input
    for color in COLOR_DIC.keys():
        main(file=file, color=color)