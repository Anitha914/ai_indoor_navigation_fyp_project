# import cv2
# import os

# proto = os.path.join("models", "MobileNetSSD_deploy.prototxt")
# weights = os.path.join("models", "MobileNetSSD_deploy.caffemodel")

# net = cv2.dnn.readNetFromCaffe(proto, weights)
# print("Model loaded successfully!")
import cv2
weights = r"D:\ai_indoor_navigation\models\frozen_inference_graph.pb" #"models/frozen_inference_graph.pb"
config  = r"D:\ai_indoor_navigation\models\ssd_mobilenet_v2_coco.pbtxt" #"models/ssd_mobilenet_v2_coco_2018_03_29.pbtxt"

#MODEL_WEIGHTS = r"D:\ai_indoor_navigation\models\frozen_inference_graph.pb" #os.path.join("models", "frozen_inference_graph.pb")
#MODEL_CONFIG  = r"D:\ai_indoor_navigation\models\ssd_mobilenet_v2_coco.pbtxt" #os.path.join("models", "ssd_mobilenet_v2_coco.pbtxt")

net = cv2.dnn_DetectionModel(weights, config)
net.setInputSize(300, 300)
net.setInputScale(1.0/127.5)
net.setInputMean((127.5,127.5,127.5))
net.setInputSwapRB(True)

print("Model loaded successfully!")
