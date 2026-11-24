import ctypes, struct, time, subprocess
from ctypes import wintypes as wt
u32=ctypes.windll.user32; k32=ctypes.windll.kernel32
u32.GetWindowThreadProcessId.argtypes=[wt.HWND,ctypes.POINTER(wt.DWORD)]
u32.GetWindowThreadProcessId.restype=wt.DWORD
u32.GetClassNameA.argtypes=[wt.HWND,ctypes.c_char_p,ctypes.c_int]
u32.GetWindowTextA.argtypes=[wt.HWND,ctypes.c_char_p,ctypes.c_int]
u32.GetWindowRect.argtypes=[wt.HWND,ctypes.POINTER(wt.RECT)]
u32.IsWindowVisible.argtypes=[wt.HWND]
u32.GetParent.argtypes=[wt.HWND]; u32.GetParent.restype=wt.HWND
u32.GetWindow.argtypes=[wt.HWND,wt.UINT]; u32.GetWindow.restype=wt.HWND
k32.OpenProcess.restype=wt.HANDLE
k32.ReadProcessMemory.argtypes=[wt.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
pid=int(subprocess.run(["powershell","-NoProfile","-Command","(Get-Process gamemd).Id"],capture_output=True,text=True).stdout.split()[0])
h=k32.OpenProcess(0x1000|0x10,False,pid)
def rd(va):
    b=ctypes.create_string_buffer(4); g=ctypes.c_size_t(0)
    ok=k32.ReadProcessMemory(h,ctypes.c_void_p(va),b,4,ctypes.byref(g))
    return struct.unpack("<I",b.raw)[0] if ok and g.value==4 else None
EP=ctypes.WINFUNCTYPE(wt.BOOL,wt.HWND,wt.LPARAM)
rows=[]
def cls(hw):
    b=ctypes.create_string_buffer(128); u32.GetClassNameA(hw,b,128); return b.value.decode("latin-1","replace")
def txt(hw):
    b=ctypes.create_string_buffer(256); u32.GetWindowTextA(hw,b,256); return b.value.decode("latin-1","replace")
def cb(hw,l):
    t=wt.DWORD(); u32.GetWindowThreadProcessId(hw,ctypes.byref(t))
    if t.value==pid:
        r=wt.RECT(); u32.GetWindowRect(hw,ctypes.byref(r))
        rows.append((cls(hw),txt(hw),(r.left,r.top,r.right-r.left,r.bottom-r.top),bool(u32.IsWindowVisible(hw)),hw))
    return True
u32.EnumWindows(EP(cb),0)
print("== top-level windows of pid",pid,"==")
for c,t,r,v,hw in rows: print("  %-24s %-28r rect=%s visible=%s hwnd=0x%X"%(c,t[:26],r,v,hw))
print("== frame/mode over 6s ==")
for i in range(7):
    print("  t=%4.1fs mode=%s frame=%s bullets=%s"%(i,rd(0xA8B238),rd(0xA8ED84),rd(0xA8ED50)))
    time.sleep(1)
