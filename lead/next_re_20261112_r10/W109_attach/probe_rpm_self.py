import ctypes, ctypes.wintypes as wt, subprocess, sys, time
k = ctypes.WinDLL("kernel32", use_last_error=True)
k.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k.OpenProcess.restype = wt.HANDLE
k.VirtualQueryEx.argtypes = [wt.HANDLE, wt.LPCVOID, ctypes.c_void_p, ctypes.c_size_t]
k.VirtualQueryEx.restype = ctypes.c_size_t
k.ReadProcessMemory.argtypes = [wt.HANDLE, wt.LPCVOID, wt.LPVOID, ctypes.c_size_t,
                                ctypes.POINTER(ctypes.c_size_t)]
k.ReadProcessMemory.restype = wt.BOOL


class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocBase", ctypes.c_void_p),
                ("AllocProtect", wt.DWORD), ("PartitionId", wt.WORD),
                ("RegionSize", ctypes.c_size_t), ("State", wt.DWORD),
                ("Protect", wt.DWORD), ("Type", wt.DWORD)]


p = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(15)"],
                     creationflags=0x08000000)
time.sleep(0.5)
h = k.OpenProcess(wt.DWORD(0x1010), False, wt.DWORD(p.pid))
va = 0x10000
n = 0
priv = []
while va < 0x7FFF0000 and n < 5000:
    mbi = MBI()
    r = k.VirtualQueryEx(h, ctypes.c_void_p(va), ctypes.byref(mbi), ctypes.sizeof(mbi))
    if r != ctypes.sizeof(mbi):
        print("VQE stop at 0x%X ret=%d err=%d" % (va, r, ctypes.get_last_error()))
        break
    base = mbi.BaseAddress or 0
    size = mbi.RegionSize or 0x1000
    n += 1
    if mbi.State == 0x1000 and mbi.Type == 0x20000:
        priv.append((base, size, mbi.Protect))
    if n <= 5:
        print("%2d base=0x%08X size=0x%06X state=0x%X prot=0x%X type=0x%X"
              % (n, base, size, mbi.State, mbi.Protect, mbi.Type))
    nxt = base + size
    if nxt <= va:
        break
    va = nxt
print("total regions", n, "private committed", len(priv))
buf = ctypes.create_string_buffer(16)
got = ctypes.c_size_t(0)
okc = 0
for base, size, prot in priv[:400]:
    got.value = 0
    ok = k.ReadProcessMemory(h, ctypes.c_void_p(base), buf, 16, ctypes.byref(got))
    if ok and got.value == 16:
        okc += 1
        if okc <= 3:
            print("RPM OK 0x%08X prot=0x%X bytes=%s" % (base, prot, buf.raw[:8].hex()))
print("private regions RPM-readable:", okc, "/", min(400, len(priv)))
p.kill()
