import sys
from whisper import _download, _MODELS # type: ignore

if __name__ == "__main__":
    args = sys.argv[1:]
    for name in args:
        _download(_MODELS[name], "/models/", False)
