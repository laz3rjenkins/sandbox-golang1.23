import os
from collections import namedtuple
import tempfile

ExecuteResult = namedtuple('ExecuteResult', ('result', 'error'))


def opener(path, flags):
    return os.open(path, flags, mode=0o777)

class GoFile:
    def __init__(self, code: str):
        self.tmpdir = tempfile.mkdtemp()
        self.filepath_go = os.path.join(self.tmpdir, "main.go")
        self.filepath_out = os.path.join(self.tmpdir, "main.out")
        with open(self.filepath_go, "w") as f:
            f.write(code)

    def remove(self):
        try:
            os.remove(self.filepath_go)
            os.remove(self.filepath_out)
            os.rmdir(self.tmpdir)
        except Exception:
            pass
