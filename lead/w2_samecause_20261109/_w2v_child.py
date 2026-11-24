import os, sys, time, ctypes
GENERIC_READ  = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
h = ctypes.windll.kernel32.CreateFileW(sys.argv[1],
      GENERIC_READ | GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None)
assert h not in (-1, 0xFFFFFFFFFFFFFFFF), ctypes.GetLastError()
open(sys.argv[2], 'w').write('held')
for _ in range(300):
    if os.path.exists(sys.argv[3]):
        break
    time.sleep(0.1)
ctypes.windll.kernel32.CloseHandle(h)
open(sys.argv[2] + '.done', 'w').write('closed')
