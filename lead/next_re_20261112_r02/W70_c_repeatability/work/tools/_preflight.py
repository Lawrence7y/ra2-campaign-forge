# -*- coding: utf-8 -*-
r"""W70 preflight: confirm this python process can (a) capture a child
process's stdout via pipes, (b) see the interactive desktop (EnumWindows),
(c) ImageGrab.grab().  Read-only; writes nothing outside this card."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w70_lib as L

print("python:", sys.version)
r = subprocess.run([sys.executable, "-c", "print('PIPE_OK')"],
                   capture_output=True, text=True, timeout=30)
print("subprocess pipe:", r.returncode, repr(r.stdout.strip()))

tops = []
L.u.EnumWindows(L.ENUM(lambda h, _l: tops.append(h) or True), 0)
vis = sum(1 for h in tops if L.u.IsWindowVisible(h))
print("EnumWindows total=%d visible=%d" % (len(tops), vis))

from PIL import ImageGrab
img = ImageGrab.grab()
print("ImageGrab:", img.size)

print("gamemd.exe live:", L.list_gamemd())
print("PREFLIGHT_OK" if r.returncode == 0 and "PIPE_OK" in r.stdout and len(tops) > 0 else "PREFLIGHT_FAIL")
