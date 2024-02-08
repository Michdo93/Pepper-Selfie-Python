import cv2

class ImagePlayer:
    def __init__(self, window_name, caption):
        self.window_name = window_name
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowTitle(window_name, caption)

    def update(self, image):
        cv2.imshow(self.window_name, image)
        cv2.waitKey(1)

    def get_current_image(self):
        return cv2.getWindowImageRect(self.window_name)[1]

    def dispose(self):
        cv2.destroyWindow(self.window_name)
