import ctypes, struct, subprocess, time
from ctypes import wintypes as wt
u32=ctypes.windll.user32; k32=ctypes.windll.kernel32
u32.GetWindowThreadProcessId.argtypes=[wt.HWND,ctypes.POINTER(wt.DWORD)]; u32.GetWindowThreadProcessId.restype=wt.DWORD
u32.GetClassNameA.argtypes=[wt.HWND,ctypes.c_char_p,ctypes.c_int]
u32.GetWindowRect.argtypes=[wt.HWND,ctypes.POINTER(wt.RECT)]
u32.GetClientRect.argtypes=[wt.HWND,ctypes.POINTER(wt.RECT)]
u32.ClientToScreen.argtypes=[wt.HWND,ctypes.POINTER(wt.POINT)]
u32.GetWindow.argtypes=[wt.HWND,wt.UINT]; u32.GetWindow.restype=wt.HWND
u32.IsWindowVisible.argtypes=[wt.HWND]
try:
    u32.GetDpiForWindow.argtypes=[wt.HWND]; u32.GetDpiForWindow.restype=wt.UINT
except Exception: pass
k32.OpenProcess.restype=wt.HANDLE
k32.ReadProcessMemory.argtypes=[wt.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
pid=int(subprocess.run(["powershell","-NoProfile","-Command","(Get-Process gamemd).Id"],capture_output=True,text=True).stdout.split()[0])
h=k32.OpenProcess(0x1000|0x10,False,pid)
def rd(va):
    b=ctypes.create_string_buffer(4); g=ctypes.c_size_t(0)
    ok=k32.ReadProcessMemory(h,ctypes.c_void_p(va),b,4,ctypes.byref(g))
    return struct.unpack("<I",b.raw)[0] if ok and g.value==4 else None
EP=ctypes.WINFUNCTYPE(wt.BOOL,wt.HWND,wt.LPARAM)
top=[]
def cb(hw,l):
    t=wt.DWORD(); u32.GetWindowThreadProcessId(hw,ctypes.byref(t))
    if t.value==pid:
        b=ctypes.create_string_buffer(128); u32.GetClassNameA(hw,b,128)
        if b.value==b"Yuri's Revenge": top.append(hw)
    return True
u32.EnumWindows(EP(cb),0)
hw=top[0]
wr=wt.RECT(); u32.GetWindowRect(hw,ctypes.byref(wr))
cr=wt.RECT(); u32.GetClientRect(hw,ctypes.byref(cr))
p=wt.POINT(0,0); u32.ClientToScreen(hw,ctypes.byref(p))
print("hwnd=0x%X  windowRect=(%d,%d)-(%d,%d) size=%dx%d"%(hw,wr.left,wr.top,wr.right,wr.bottom,wr.right-wr.left,wr.bottom-wr.top))
print("clientRect=%dx%d   clientOriginScreen=(%d,%d)"%(cr.right,cr.bottom,p.x,p.y))
print("dpi=%s"%u32.GetDpiForWindow(hw))
print("--- children ---")
def walk(hw,d=0):
    c=u32.GetWindow(hw,5)  # GW_CHILD
    while c:
        b=ctypes.create_string_buffer(128); u32.GetClassNameA(c,b,128)
        r=wt.RECT(); u32.GetWindowRect(c,ctypes.byref(r))
        print("  %s%-22s rect=(%d,%d) %dx%d vis=%s"%(("  "*d),b.value.decode("latin-1"),r.left,r.top,r.right-r.left,r.bottom-r.top,bool(u32.IsWindowVisible(c))))
        walk(c,d+1); c=u32.GetWindow(c,2)
walk(hw)
print("--- globals ---")
for name,va in [("mode(0xA8B238)",0xA8B238),("frame(0xA8ED84)",0xA8ED84),("bullets(0xA8ED50)",0xA8ED50),
                ("flag(0xA83D48)",0xA83D48),("world(0xA8B230)",0xA8B230),("unitCnt(0x8B4118)",0x8B4118),
                ("footCnt(0x8B3DD0)",0x8B3DD0),("bldgCnt(0xA8EB50)",0xA8EB50),("infCnt(0xA83DF8)",0xA83DF8),
                ("absCnt(0xB0F730)",0xB0F730),("attract(0xA8D5F8)",0xA8D5F8)]:
    print("  %-18s = %s"%(name,rd(va)))
