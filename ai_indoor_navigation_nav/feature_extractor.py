
# import cv2
# import numpy as np

# orb = cv2.ORB_create(nfeatures=2000)

# def detect_and_descr(img):

#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#     kps, des = orb.detectAndCompute(gray, None)

#     if des is None:
#         return [], None

#     return kps, des


# def match_descriptors(des1, des2):

#     if des1 is None or des2 is None:
#         return []

#     bf = cv2.BFMatcher(cv2.NORM_HAMMING)

#     matches = bf.knnMatch(des1, des2, k=2)

#     good = []

#     for pair in matches:

#         # Sometimes OpenCV returns only 1 match
#         if len(pair) < 2:
#             continue

#         m, n = pair

#         if m.distance < 0.75 * n.distance:
#             good.append(m)

#     return good

import torch
import torchvision.models as models
import torchvision.transforms as transforms
import numpy as np

# Load pretrained MobileNetV2
model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
model = model.features
model.eval()

transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224,224)),
    transforms.ToTensor(),
])

def extract_embedding(frame):
    img = transform(frame).unsqueeze(0)

    with torch.no_grad():
        features = model(img)

    features = features.mean([2,3])  # global average pooling
    features = features / (features.norm() + 1e-10)  # normalize

    return features.numpy().flatten()