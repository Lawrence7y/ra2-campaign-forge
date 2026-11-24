import ctypes, ctypes.wintypes as wt, sys, struct
k32=ctypes.WinDLL("kernel32",use_last_error=True)
k32.OpenProcess.restype=wt.HANDLE
k32.OpenProcess.argtypes=[wt.DWORD,wt.BOOL,wt.DWORD]
k32.ReadProcessMemory.argtypes=[wt.HANDLE,wt.LPCVOID,wt.LPVOID,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
pid=int(sys.argv[1])
h=k32.OpenProcess(0x1010,False,pid)
def rd(va,n):
    b=ctypes.create_string_buffer(n); g=ctypes.c_size_t(0)
    ok=k32.ReadProcessMemory(h,ctypes.c_void_p(va),b,n,ctypes.byref(g))
    return b.raw[:n] if ok and g.value==n else None
def u32(va):
    b=rd(va,4); return None if b is None else int.from_bytes(b,"little")
tbl=u32(0x87F924); print("table=0x%08X"%tbl)
# 一次读整张 512*512*4 = 1 MB
blob=rd(tbl, 512*512*4)
print("bulk read 1MB:", "OK" if blob else "FAIL")
if not blob: sys.exit(0)
entries=struct.unpack_from("<%dI"%(512*512), blob, 0)
nn=[(i,v) for i,v in enumerate(entries) if v]
print("全表非空条目 = %d / %d" % (len(nn), 512*512))
# 取前若干非空条目，看它们的 +0xE4/+0xE8 有没有合法 vptr
good=[]
for i,v in nn[:4000]:
    for off in (0xE4,0xE8):
        head=u32(v+off)
        if head and head>0x10000:
            vt=u32(head)
            if vt and 0x7E1000<=vt<0x812000:
                good.append((i,v,off,head,vt))
print("前 4000 个非空 cell 中，链头 vptr 落在 .rdata 的 = %d" % len(good))
for i,v,off,head,vt in good[:8]:
    print("   idx=%-7d (r=%d,c=%d) cell=0x%08X off=+0x%02X head=0x%08X vptr=0x%08X"
          % (i, i//512, i%512, v, off, head, vt))
# 也扫一遍 static CellClass 候选：找 .data 里首 dword == CellClass vtable 的对象
for cand in (0x0089C2E0,0x00ABDC50):
    v0=u32(cand); print("静态候选 0x%08X 首dword=0x%08X  %s" % (cand, v0 or 0,
        "=CellClass vtable" if v0 in (0x7E4EC0,0x7E4EC8,0x7E4ED0,0x7E4EEC) else ""))
k32.CloseHandle(h)
