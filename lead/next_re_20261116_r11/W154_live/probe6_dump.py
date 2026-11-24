import ctypes, struct, subprocess
from ctypes import wintypes as wt
k32=ctypes.windll.kernel32
k32.OpenProcess.restype=wt.HANDLE
k32.ReadProcessMemory.argtypes=[wt.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
pid=int(subprocess.run(["powershell","-NoProfile","-Command","(Get-Process gamemd).Id"],capture_output=True,text=True).stdout.split()[0])
h=k32.OpenProcess(0x1000|0x10,False,pid)
def raw(va,n):
    b=ctypes.create_string_buffer(n); g=ctypes.c_size_t(0)
    ok=k32.ReadProcessMemory(h,ctypes.c_void_p(va),b,n,ctypes.byref(g))
    return b.raw[:g.value] if ok else b""
for tag,base in [("0x8B4100",0x8B4100),("0x8B4110",0x8B4110),("0xA8ED3C",0xA8ED3C),("0xB0F720",0xB0F720)]:
    d=raw(base,0x20)
    print("%s: "%tag + " ".join("%08X"%v for v in struct.unpack("<%dI"%(len(d)//4), d)))
