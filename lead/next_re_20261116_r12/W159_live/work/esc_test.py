import ctypes, time, sys
from ctypes import wintypes as wt
import w159_probe as W
u32=ctypes.windll.user32
u32.SetForegroundWindow.argtypes=[wt.HWND]
u32.keybd_event.argtypes=[wt.BYTE,wt.BYTE,wt.DWORD,ctypes.c_size_t]

pid=W.pid_of(); m=W.Mem(pid)
def hwnd_of(pid):
    found=[]
    def cb(h,l):
        t=wt.DWORD(); u32.GetWindowThreadProcessId(h,ctypes.byref(t))
        if t.value==pid and u32.IsWindowVisible(h): found.append(h)
        return True
    EP=ctypes.WINFUNCTYPE(wt.BOOL,wt.HWND,wt.LPARAM); u32.EnumWindows(EP(cb),0)
    return found[0] if found else None
h=hwnd_of(pid)
u32.ShowWindow(h,9); u32.SetForegroundWindow(h); time.sleep(1.0)
print("fg match:", u32.GetForegroundWindow()==h)
print("before ESC: mode=%s frame=%s" % (m.rd(W.G['mode']), m.rd(W.G['frame'])))
VK_ESCAPE=0x1B
u32.keybd_event(VK_ESCAPE,0,0,0); time.sleep(0.05); u32.keybd_event(VK_ESCAPE,0,2,0)
for i in range(8):
    time.sleep(1.0)
    print("  t=%ds mode=%s frame=%s bullets=%s" % (i+1, m.rd(W.G['mode']), m.rd(W.G['frame']), m.rd(W.G['bullets'])))
