import ctypes, ctypes.wintypes as w
u = ctypes.WinDLL("user32")
k = ctypes.WinDLL("kernel32")
u.GetProcessWindowStation.restype = w.HANDLE
u.GetThreadDesktop.restype = w.HANDLE
u.GetThreadDesktop.argtypes = [w.DWORD]
u.GetUserObjectInformationW.restype = w.BOOL
u.GetUserObjectInformationW.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.POINTER(w.DWORD)]
k.GetCurrentThreadId.restype = w.DWORD

def nm(h):
    b = ctypes.create_unicode_buffer(512)
    n = w.DWORD(0)
    ok = u.GetUserObjectInformationW(h, 2, b, ctypes.sizeof(b), ctypes.byref(n))
    return b.value if ok else "ERR"

print("winsta=", nm(u.GetProcessWindowStation()))
print("thread_desktop=", nm(u.GetThreadDesktop(k.GetCurrentThreadId())))
tops = []
ENUM = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
u.EnumWindows.argtypes = [ctypes.c_void_p, w.LPARAM]
def cb(h, l):
    tops.append(h); return True
u.EnumWindows(ENUM(cb), 0)
print("enum_windows_total=", len(tops))
try:
    from PIL import ImageGrab
    im = ImageGrab.grab()
    print("imagegrab=", im.size, "mode=", im.mode)
except Exception as e:
    print("imagegrab FAILED", repr(e))
