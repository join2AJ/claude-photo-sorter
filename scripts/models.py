"""Download the free, open-source models once (about 135 MB) into models/.  python scripts/models.py

  face_detection_yunet  finds faces            OpenCV Zoo, MIT licence
  face_recognition_sface  face fingerprint     OpenCV Zoo, Apache 2.0
  age_googlenet / gender_googlenet  estimates  ONNX Model Zoo, Apache 2.0
  emotion-ferplus-8  emotion                   ONNX Model Zoo, Apache 2.0 (Microsoft FER+)
  mobilenetv2-12  what's in the photo (1000 everyday things)  ONNX Model Zoo, Apache 2.0
Text in screenshots is read with RapidOCR (Apache 2.0), which brings its own small models.
Everything runs on this computer. Only the model files are downloaded, nothing is uploaded.
"""
import os, sys, urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from common import MODELS

HF = "https://huggingface.co/{}/resolve/main/{}"
FILES = {
    "yunet.onnx": HF.format("opencv/face_detection_yunet", "face_detection_yunet_2023mar.onnx"),
    "sface.onnx": HF.format("opencv/face_recognition_sface", "face_recognition_sface_2021dec.onnx"),
    "age.onnx": HF.format("onnxmodelzoo/age_googlenet", "age_googlenet.onnx"),
    "gender.onnx": HF.format("onnxmodelzoo/gender_googlenet", "gender_googlenet.onnx"),
    "emotion.onnx": HF.format("onnxmodelzoo/emotion-ferplus-8", "emotion-ferplus-8.onnx"),
    "mobilenet.onnx": HF.format("onnxmodelzoo/mobilenetv2-12", "mobilenetv2-12.onnx"),
    "imagenet.json": "https://huggingface.co/datasets/huggingface/label-files/resolve/main/imagenet-1k-id2label.json",
}


def ensure(quiet=False):
    os.makedirs(MODELS, exist_ok=True)
    for name, url in FILES.items():
        path = os.path.join(MODELS, name)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            continue
        if not quiet:
            print(f"Downloading {name}...", flush=True)
        tmp = path + ".part"
        urllib.request.urlretrieve(url, tmp)
        os.replace(tmp, path)
    return MODELS


if __name__ == "__main__":
    ensure()
    print("Models ready in models/")
