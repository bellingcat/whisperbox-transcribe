import os
import sys
from whisper import _download, _MODELS  # type: ignore

if __name__ == "__main__":
    model_name = sys.argv[1].strip()
    _download(_MODELS[model_name], "/models/", False)
