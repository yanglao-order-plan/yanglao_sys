import cv2
compress_save_path = 'E:\GitHub\yanglao_sys\yoloWorld_detectSeg_backend\scripts/compress_save.jpg'

img_cv_ = cv2.imread(compress_save_path)

print(img_cv_.nbytes / 1024)