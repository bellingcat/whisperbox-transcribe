import os
from whisper import _download, _MODELS  # type: ignore

if __name__ == "__main__":
    for name in os.environ["WHISPER_MODELS"].split(","):
        _download(_MODELS[name], "/models/", False)
        if name != "large":
            _download(_MODELS[f"{name}.en"], "/models/", False)
