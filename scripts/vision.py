"""Everything the computer can see in a picture, with free open-source models (see models.py).
Runs fully offline once the models are downloaded.

  faces(img)      -> boxes, a 128-number face fingerprint, estimated age, gender and emotion
  tags(img)       -> the main things in the picture (dog, pizza, car, beach...)
  read_text(img)  -> text in screenshots and documents (RapidOCR)
img is an OpenCV BGR array (see load()).
"""
import json, os, sys

import cv2
import numpy as np
import onnxruntime as ort

sys.path.insert(0, os.path.dirname(__file__))
from common import MODELS
from models import ensure

AGES = ["0-2", "4-6", "8-12", "15-20", "25-32", "38-43", "48-53", "60+"]
AGE_MID = [1, 5, 10, 18, 28, 40, 50, 65]
EMOTIONS = ["neutral", "happy", "surprised", "sad", "angry", "disgusted", "scared", "contempt"]
SAME_PERSON = 0.42  # cosine similarity of two SFace fingerprints; OpenCV suggests 0.363, a bit stricter = fewer mix-ups

_m = {}


def _model(name):
    if name not in _m:
        ensure(quiet=True)
        p = os.path.join(MODELS, name)
        if name == "yunet.onnx":
            _m[name] = cv2.FaceDetectorYN.create(p, "", (320, 320), 0.75, 0.3, 5000)
        elif name == "sface.onnx":
            _m[name] = cv2.FaceRecognizerSF.create(p, "")
        elif name == "ocr":
            from rapidocr_onnxruntime import RapidOCR
            _m[name] = RapidOCR()
        elif name == "imagenet.json":
            _m[name] = {int(k): v.split(",")[0] for k, v in json.load(open(p)).items()}
        else:
            o = ort.SessionOptions()
            o.log_severity_level = 3
            o.intra_op_num_threads = 2
            _m[name] = ort.InferenceSession(p, o, providers=["CPUExecutionProvider"])
    return _m[name]


def load(path, max_side=1600):
    """Read any photo (HEIC too) as BGR, upright, at most max_side pixels."""
    from PIL import Image, ImageOps
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        pass
    with Image.open(path) as im:
        im.draft("RGB", (max_side, max_side))
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((max_side, max_side))
        return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)


def _softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()


def _crop(img, box, margin=0.4):
    x, y, w, h = box
    mx, my = w * margin, h * margin
    H, W = img.shape[:2]
    x0, y0 = int(max(0, x - mx)), int(max(0, y - my))
    x1, y1 = int(min(W, x + w + mx)), int(min(H, y + h + my))
    return img[y0:y1, x0:x1]


def faces(img, min_size=36):
    """Every face bigger than min_size pixels, with its fingerprint and estimates."""
    H, W = img.shape[:2]
    det = _model("yunet.onnx")
    det.setInputSize((W, H))
    _, found = det.detect(img)
    out = []
    for f in (found if found is not None else []):
        x, y, w, h = f[:4]
        if min(w, h) < min_size:
            continue
        rec = _model("sface.onnx")
        emb = rec.feature(rec.alignCrop(img, f)).flatten()
        emb = emb / (np.linalg.norm(emb) + 1e-9)
        face = _crop(img, (x, y, w, h))
        blob = cv2.resize(face, (224, 224)).astype(np.float32) - np.array([104, 117, 123], np.float32)
        blob = blob.transpose(2, 0, 1)[None]
        age_p = _model("age.onnx").run(None, {"input": blob})[0][0]  # these two already give probabilities
        age_p = age_p / age_p.sum()
        gen_p = _model("gender.onnx").run(None, {"input": blob})[0][0]
        gen_p = gen_p / gen_p.sum()
        tight = _crop(img, (x, y, w, h), 0.05)
        g = cv2.resize(cv2.cvtColor(tight, cv2.COLOR_BGR2GRAY), (64, 64)).astype(np.float32)[None, None]
        emo_p = _softmax(_model("emotion.onnx").run(None, {"Input3": g})[0][0])
        a = int(age_p.argmax())
        small = min(w, h) < 64  # too few pixels to guess age, gender or mood
        out.append({
            "box": [int(x), int(y), int(w), int(h)], "score": round(float(f[14]), 3),
            "embedding": emb.astype(np.float32),
            "age": None if small else AGES[a], "age_years": None if small else int(round(float((age_p * AGE_MID).sum()))),
            "gender": None if small else "male" if gen_p[0] > gen_p[1] else "female",
            "gender_conf": None if small else round(float(gen_p.max()), 2),
            "emotion": None if small else EMOTIONS[int(emo_p.argmax())],
            "emotion_conf": None if small else round(float(emo_p.max()), 2),
            "area": float(w * h) / (W * H),
        })
    return out


def face_thumb(img, box, size=160):
    c = _crop(img, box, 0.25)
    h, w = c.shape[:2]
    s = min(h, w)
    c = c[(h - s) // 2:(h - s) // 2 + s, (w - s) // 2:(w - s) // 2 + s]
    return cv2.resize(c, (size, size))


def tags(img, top=5, min_p=0.08):
    """Top things in the picture from the 1,000 everyday ImageNet classes."""
    names = _model("imagenet.json")
    x = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), (224, 224)).astype(np.float32) / 255
    x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).astype(np.float32).transpose(2, 0, 1)[None]
    p = _softmax(_model("mobilenet.onnx").run(None, {"input": x})[0][0])
    idx = p.argsort()[::-1][:top]
    return [(int(i), names[int(i)], round(float(p[i]), 3)) for i in idx if p[i] >= min_p]


def read_text(img):
    """All text in the picture, top to bottom."""
    res, _ = _model("ocr")(img)
    if not res:
        return ""
    res.sort(key=lambda r: (round(r[0][0][1] / 12), r[0][0][0]))
    return "\n".join(r[1] for r in res if float(r[2]) > 0.5)


def same_person(a, b):
    return float(np.dot(a, b))
