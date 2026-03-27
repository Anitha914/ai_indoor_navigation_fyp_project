import torch
import timm
import cv2
import numpy as np

device = "cuda" if torch.cuda.is_available() else "cpu"

model = timm.create_model("vit_small_patch16_224", pretrained=True)
model.eval().to(device)

def preprocess(frame):
    frame = cv2.resize(frame, (224, 224))
    frame = frame / 255.0
    frame = np.transpose(frame, (2, 0, 1))
    return torch.tensor(frame, dtype=torch.float32).unsqueeze(0).to(device)

def compute_embedding(frame):
    with torch.no_grad():
        img = preprocess(frame)
        feat = model.forward_features(img)
        emb = feat.mean(dim=1).cpu().numpy().flatten()
    return emb