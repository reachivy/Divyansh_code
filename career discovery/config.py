import os

# Gemini (Google Generative AI) config
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyB1oVamAm1Ivvb03J0aCHkyAbsECAXESmk")
GEMINI_MODEL_NAME = "gemini-2.0-flash"

# Whisper config (for voice_processor.py)
WHISPER_MODEL_NAME = "base"
# If torch is used here, you can check the device (optional):
try:
    import torch
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    DEVICE = "cpu"
