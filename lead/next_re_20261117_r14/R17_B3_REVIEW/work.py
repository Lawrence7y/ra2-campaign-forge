
#!/usr/bin/env python3
# R17_B3_REVIEW / work.py -- independent re-decode of the 12 B3 sites.
# Pure static, read-only. Opened with 'rb'. No process, no debugger.
# Anchored disassembly only: PE header -> section table -> host anchors.
import sys, os, json, hashlib
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_B3_REVIEW"

HOSTS = [0x43B680, 0x43B740, 0x43BCF0]
SLOTS = [0x7E3E90, 0x7E3E98, 0x7E3EA0, 0x7E3EBC]
EXPECTED = {0x7E3E90: 0x410590, 0x7E3E98: 0x410580, 0x7E3EA0: 0x4105E0, 0x7E3EBC: 0x410260}

def u16(b,o): return int.from_bytes(b[o:o+2],'little')
def u32(b,o): return int.from_bytes(b[o:o+4],'little')

def load():
    data = open(EXE,'rb').read()
    assert u16(data,0)==0x5A4D, 'not MZ'
    pe = u32(data,0x3C); assert data[pe:pe+4]==b'PE\0\0','not PE'
    nsec = u16(data, pe+6); optsz = u16(data, pe+20)
    opt = pe+24
    magic = u16(data,opt); assert magic==0x10B, 'not PE32'
    imagebase = u32(data,opt+28)
    sizeopt = u32(data,opt+56)
    secs=[]
    secoff = opt+optsz
    for i in range(nsec):
        o = secoff+i*40
        name = data[o:o+8].rstrip(b'\0').decode('latin1')
        vsz = u32(data,o+8); va = u32(data,o+12); rsz = u32(data,o+16); raw = u32(data,o+20)
        chars = u32(data,o+36)
        secs.append(dict(name=name, va=imagebase+va, vsize=vsz, rsize=rsz, raw=raw, chars=chars))
    return data, imagebase, secs

data, IMGB, SECS = load()

def sec_of(va):
    for s in SECS:
        lo = s['va']; hi = s['va'] + max(s['rsize'], s['vsize'])
        if s['raw'] and lo <= va < s['va']+s['rsize']:
            return s
    return None

def rd(va, n):
    s = sec_of(va)
    if s is None: return None
    off = s['raw'] + (va - s['va'])
    return data[off:off+n]

def dword(va):
    b = rd(va,4)
    return None if b is None or len(b)<4 else int.from_bytes(b,'little')

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

def disas_range(start, end):
    blk = rd(start, end-start)
    res=[]
    for ins in md.disasm(blk, start):
        res.append(ins)
    return res

# ---------- C2: byte-measured fn_end ----------
# Anchor-aligned: every candidate host anchor must sit at an instruction boundary
# derived from the previous function's measured end or from a call target.
def measure_fn_end(host, window=0x900):
    ins = disas_range(host, host+window)
    last = host
    for i in ins:
        last = i.address + i.size
        if i.mnemonic == 'ret' or i.mnemonic=='retn':
            # check padding after ret
            nxt = rd(last, 16)
            j = 0
            while j < len(nxt) and nxt[j] in (0x90,0xCC,0x00):
                j += 1
            return dict(host=hex(host), fn_end=hex(last+ (j if j>=1 else 0)), end_kind='ret', ret_addr=hex(last),
                        pad_after=j, pad_bytes=nxt[:j].hex(), next_bytes=nxt[j:j+8].hex())
    return dict(host=hex(host), fn_end=None, end_kind='no-ret-in-window')

# ---------- helper: find next anchor after host that is a known entry ----------
def entry_like(va):
    # prologue heuristic: push ebp; mov ebp,esp  OR sub esp,imm  OR push -1 ; mov eax,fs:[0]
    b = rd(va,8)
    if not b: return False
    if b[0]==0x55 and b[1]==0x8B and b[2]==0xEC: return True
    if b[0:3]==b'\x83\xEC': return True
    if b[0:3]==b'\x81\xEC': return True
    if b[0:2]==b'\x6A\xFF' and len(b)>=5 and b[3]==0x64 and b[4]==0xA1: return True
    return False

report = {}
report['sha256'] = hashlib.sha256(data).hexdigest().upper()
report['size'] = len(data)
report['imagebase'] = hex(IMGB)
report['sections'] = [dict(name=s['name'], va=hex(s['va']), vsize=s['vsize'], rsize=s['rsize'], raw=s['raw']) for s in SECS]

# ---------- C3: slot contents ----------
c3=[]
for s in SLOTS:
    v = dword(s)
    sec = sec_of(v) if v else None
    c3.append(dict(slot=hex(s), value=hex(v) if v is not None else None,
                   expected=hex(EXPECTED[s]), match=(v==EXPECTED[s]),
                   value_section=(sec['name'] if sec else None)))
report['C3']=c3

# also dump the 16 slots around each target for context
ctx=[]
for s in SLOTS:
    ctx.append(dict(base=hex(s-8), vals=[hex(dword(s-8+4*k) or 0) for k in range(8)]))
report['C3_context']=ctx

# ---------- C2/C1 ----------
fns=[]
for h in HOSTS:
    e = measure_fn_end(h)
    fns.append(e)
report['fn_end']=fns

# verify end alignment against a plausible next entry
for e in fns:
    if e['fn_end']:
        fe=int(e['fn_end'],16)
        e['next_entry_like']=entry_like(fe)
        e['next_bytes']= (rd(fe,12) or b'').hex()

json.dump(report, open(os.path.join(OUT,'stage1.json'),'w',encoding='utf8'), indent=1, ensure_ascii=False)
print(json.dumps(report, indent=1)[:6000])
