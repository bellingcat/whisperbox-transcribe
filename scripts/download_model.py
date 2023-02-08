import sys
from whisper import _download, _MODELS # type: ignore

if __name__ == "__main__":
    model_name = sys.argv[1]
    _download(_MODELS[model_name], "/models/", False)
    if model_name != "large":
        _download(_MODELS[f"{model_name}.en"], "/models/", False)
