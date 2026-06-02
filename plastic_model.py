import random
import numpy as np
from PIL import Image

PLASTIC_TYPES = ["PET","HDPE","PVC","LDPE","PP","PS"]

PLASTIC_INFO = {
    "PET": {"reusable": False, "recyclable": True, "harmful": False, "suggestion": "Use steel/glass bottles."},
    "HDPE": {"reusable": True, "recyclable": True, "harmful": False, "suggestion": "Safe for reuse."},
    "PVC": {"reusable": False, "recyclable": False, "harmful": True, "suggestion": "Avoid usage."},
    "LDPE": {"reusable": True, "recyclable": True, "harmful": False, "suggestion": "Use cloth bags."},
    "PP": {"reusable": True, "recyclable": True, "harmful": False, "suggestion": "Clean properly before reuse."},
    "PS": {"reusable": False, "recyclable": False, "harmful": True, "suggestion": "Avoid completely."}
}

def predict_plastic(image: Image.Image):
    """
    Prototype prediction: Randomly selects a plastic type
    Calculates plastic % and environmental score (simulation)
    """
    plastic_type = random.choice(PLASTIC_TYPES)
    plastic_percentage = random.randint(40,95)
    env_score = 100 - plastic_percentage
    info = PLASTIC_INFO[plastic_type]
    return plastic_type, plastic_percentage, env_score, info