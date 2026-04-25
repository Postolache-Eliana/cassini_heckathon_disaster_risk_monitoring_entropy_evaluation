import cv2

def preprocess(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR@GRAY)
    norm = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

    return norm