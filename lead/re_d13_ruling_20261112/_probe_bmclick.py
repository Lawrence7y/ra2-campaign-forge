import ctypes, ctypes.wintypes as wt, time, sys
PID=int(sys.argv[1])
u=ctypes.WinDLL("user32", use_last_error=True)
u.SendMessageW.restype=ctypes.c_void_p; u.SendMessageW.argtypes=[wt.HWND,wt.UINT,wt.WPARAM,wt.LPARAM]
u.PostMessageW.restype=wt.BOOL; u.PostMessageW.argtypes=[wt.HWND,wt.UINT,wt.WPARAM,wt.LPARAM]
u.GetWindowThreadProcessId.restype=wt.DWORD; u.GetWindowThreadProcessId.argtypes=[wt.HWND,ctypes.POINTER(wt.DWORD)]
u.GetWindowTextLengthW.restype=ctypes.c_int; u.GetWindowTextLengthW.argtypes=[wt.HWND]
u.GetWindowTextW.restype=ctypes.c_int; u.GetWindowTextW.argtypes=[wt.HWND,wt.LPWSTR,ctypes.c_int]
u.GetClassNameW.restype=ctypes.c_int; u.GetClassNameW.argtypes=[wt.HWND,wt.LPWSTR,ctypes.c_int]
u.EnumWindows.restype=wt.BOOL; u.EnumWindows.argtypes=[ctypes.c_void_p,wt.LPARAM]
u.EnumChildWindows.restype=wt.BOOL; u.EnumChildWindows.argtypes=[wt.HWND,ctypes.c_void_p,wt.LPARAM]
ENUM=ctypes.WINFUNCTYPE(wt.BOOL,wt.HWND,wt.LPARAM)
def wtxt(h):
    n=u.GetWindowTextLengthW(h); b=ctypes.create_unicode_buffer(max(n+1,2)); u.GetWindowTextW(h,b,n+1); return b.value
def wcls(h):
    b=ctypes.create_unicode_buffer(256); u.GetClassNameW(h,b,256); return b.value
def buttons(pid):
    tops=[]
    def cb(h,l):
        q=wt.DWORD(0); u.GetWindowThreadProcessId(h,ctypes.byref(q))
        if q.value==pid: tops.append(h)
        return True
    u.EnumWindows(ENUM(cb),0)
    out=[]
    def walk(h):
        kids=[]
        def ccb(k,l): kids.append(k); return True
        u.EnumChildWindows(h,ENUM(ccb),0)
        for k in kids:
            if wcls(k)=='Button': out.append((k,wtxt(k)))
            walk(k)
    for t in tops: walk(t)
    return out
bs=buttons(PID)
print("=== 找到 %d 个 Button 控件 ==="%len(bs))
for h,t in bs: print("  hwnd=%-10d %r"%(h,t))
print()
target=None
for h,t in bs:
    if 'SinglePlayer' in t: target=h; break
print("目标（單人遊戲）hwnd =", target)
if target:
    print()
    print("=== 发 BM_CLICK (0x00F5) ===")
    r=u.SendMessageW(target, 0x00F5, 0, 0)
    print("  SendMessage(BM_CLICK) 返回 =", r)
    time.sleep(2.5)
    print()
    print("=== 之后重新枚举按钮（菜单应已切换）===")
    bs2=buttons(PID)
    print("  现在 %d 个 Button："%len(bs2))
    for h,t in bs2: print("    hwnd=%-10d %r"%(h,t))
