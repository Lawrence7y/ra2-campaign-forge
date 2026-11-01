# -*- coding: utf-8 -*-
"""_r064rev_probe3.py — 复核点 2/4 核心：独立 esp-D 归一化模拟器（全新实现）

域：与门禁同款逐条线性解码（解码失败 cur+=1；1.39M 指令）。
闭包：E8 头前向闭包（fall 不入他头 / jcc 双臂 / jmp 目标；ret 截断；
      闭包内跳可回边；他 E8 头不入）。头归属=闭包成员且唯一。
ret-imm：闭包内全部 ret 的 imm 交集（不一致或无 ret ⇒ None）。
状态 (D,p)：D=esp 沉降量（相对头入口，call 已压 4），p=待清算 push 计数。
  push +4/p+4；pop −4；sub esp +imm/p+imm；add esp −imm/p=0；
  call 已知 r：D−=r,p=max(0,p−r)；call 未知 ret-imm：p==0 放行（零推⇒两种约定效应 0，
  R-063b 规则 1）否则剪枝；写 esp（非 add/sub 形）/leave：剪枝；ret：截断收集。
帧 D 两处间接 call（0x5CEF6B/0x5CEF78）按 vtable 直读落实 r=4（本脚本自行重验，
不引 R-064 输出）；帧 D 其余间接 call（0x5CF038/0x5CF350/0x5CF556）默认剪枝，
并跑 HYPV 依赖性实验（仅采信两处落实、其余全剪枝 ⇒ 行仍闭合？）
"""
import struct, hashlib, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
raw = open(EXE, "rb").read()
assert hashlib.sha256(raw).hexdigest() == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
e_lfanew = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e_lfanew + 6)[0]
optsz = struct.unpack_from("<H", raw, e_lfanew + 20)[0]
opt = e_lfanew + 24
ib = struct.unpack_from("<I", raw, opt + 28)[0]
tab = opt + optsz
secs = []
for i in range(nsec):
    name = raw[tab+i*40:tab+i*40+8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab+i*40+8)
    secs.append((name, ib+va, vsz, rp, rsz))
def rb(va, n):
    rva = va - ib
    for name, sva, vsz, rp, rsz in secs:
        if sva - ib <= rva < sva - ib + vsz:
            fo = rp + (rva - (sva - ib))
            return raw[fo:fo+n] if fo < rp+rsz else bytes(n)
    return b""
def rd(va):
    b = rb(va, 4); return int.from_bytes(b, "little") if len(b)==4 else None

tname, tva, tvsz, trp, trsz = next(s for s in secs if s[0]==".text")
TLO, THI = tva, tva + trsz
code = raw[trp:trp+trsz]
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
insns = []; cur = TLO; end = TLO + trsz
while cur < end:
    got = None
    for ins in md.disasm(code[cur-TLO:min(cur-TLO+15, end-TLO)], cur):
        got = (ins.address, ins.size, ins.bytes.hex(), ins.mnemonic, ins.op_str); break
    if got is None: cur += 1; continue
    insns.append(got); cur += got[1]
IDX = {a: i for i, (a, s, b, m, o) in enumerate(insns)}
def insn(a):
    k = IDX.get(a); return insns[k] if k is not None else None
print("decoded=%d" % len(insns))

e8set = set()
for a, s, b, m, o in insns:
    if m == "call" and b.startswith("e8") and len(b) == 10:
        try: t = int(o, 16)
        except ValueError: continue
        if TLO <= t < THI and a in IDX and insns[IDX[a]][0] == a:
            e8set.add(t)
print("E8 targets=%d" % len(e8set))

def parse_imm(s):
    s = s.strip()
    if s.startswith("0x"):
        try: return int(s, 16)
        except ValueError: return None
    if re.fullmatch(r"\d+", s): return int(s)
    return None

def closure(head):
    body = {}
    stack = [head]; seen = {head}
    while stack:
        a = stack.pop()
        k = IDX.get(a)
        if k is None:
            body[a] = []; continue
        _, s, b, m, o = insns[k]
        succ = []
        if m == "ret":
            pass
        elif m == "jmp":
            t = parse_imm(o)
            if t is not None and TLO <= t < THI and (t not in e8set or t == head):
                succ.append(t)
        elif m[0] == "j":
            t = parse_imm(o)
            if t is not None and TLO <= t < THI and t not in e8set:
                succ.append(t)
            nxt = a + s
            if nxt < THI and (nxt not in e8set or nxt == head):
                succ.append(nxt)
        else:
            nxt = a + s
            if nxt < THI and (nxt not in e8set or nxt == head):
                succ.append(nxt)
        body[a] = succ
        for x in succ:
            if x not in seen:
                seen.add(x); stack.append(x)
    return body, seen

_RC = {}
def ret_imm(head):
    if head in _RC: return _RC[head]
    body, seen = closure(head)
    imms = []
    for a in body:
        it = insn(a)
        if it and it[3] == "ret":
            imms.append(parse_imm(it[4]) if it[4] else 0)
    v = None
    if imms and len(set(imms)) == 1:
        v = imms[0]
    _RC[head] = (v, body, seen, imms)
    return _RC[head]

def callee_retimm(t):
    v, _, _, _ = ret_imm(t)
    return v

# ---- 间接 call 落实自验（不引 R-064 输出）----
print("\n== 帧 D 间接 call vtable 落实自验 ==")
print("  rb(0x473A9B,6)=%s（期望 c706b0167e00：CCFileClass stamp [esi]=0x7E16B0）" % rb(0x473A9B, 6).hex())
s1 = rd(0x7E16B0 + 8); s2 = rd(0x7E16B0 + 0x1C)
print("  vtable[+8]=%06X rets=%s ; vtable[+0x1C]=%06X rets=%s" % (s1, ret_imm(s1)[3], s2, ret_imm(s2)[3]))
print("  call-site bytes: 0x5CEF6B=%s 0x5CEF78=%s" % (rb(0x5CEF6B,3).hex(), rb(0x5CEF78,3).hex()))
RES = {0x5CEF6B: 4, 0x5CEF78: 4}
UNRES = {0x5CF038, 0x5CF350, 0x5CF556}

def dsim(head, resmap):
    v, body, seen, _ = ret_imm(head)
    collect = {}; causes = {}
    stack = [(head, 0, 0)]; seenst = set(); guard = 0
    while stack:
        guard += 1
        if guard > 3_000_000: causes["guard-budget"] = None; break
        a, D, p = stack.pop()
        if (a, D, p) in seenst: continue
        seenst.add((a, D, p))
        it = insn(a)
        if it is None:
            if a in targetset: collect.setdefault(a, set()).add(None)
            causes.setdefault("undecoded@%06X" % a, set()).add("undecoded")
            continue
        _, s, b, m, o = it
        if a in targetset0: collect.setdefault(a, set()).add(D)
        if m == "ret": continue
        nD, np = D, p; pruned = False
        if m == "push":
            nD, np = D + 4, p + 4
        elif m == "pop":
            nD = D - 4
        elif m == "sub" and o.startswith("esp, "):
            x = parse_imm(o.split(", ", 1)[1]); nD, np = D + x, p + x
        elif m == "add" and o.startswith("esp, "):
            x = parse_imm(o.split(", ", 1)[1]); nD, np = D - x, 0
        elif m == "call":
            if a in resmap:
                r = resmap[a]; nD, np = D - r, max(0, p - r)
            else:
                t = parse_imm(o) if (o and not o.startswith("dword")) else None
                if t is None or not (TLO <= t < THI) or t not in e8set:
                    # 间接/外部/非 E8 call：零推放行（规则 1），否则剪枝
                    if p != 0:
                        causes.setdefault(a, set()).add("call-unresolved p=%d%s" % (p, " (E8-unknown)" if (t and t in e8set) else "")); pruned = True
                    else:
                        nD, np = D, 0
                else:
                    r = callee_retimm(t)
                    if r is None:
                        if p != 0:
                            causes.setdefault(a, set()).add("callee-%06X retambig%s p=%d" % (t, ("" if imms_uni(t) else ""), p)); pruned = True
                        else:
                            nD, np = D, 0
                    else:
                        nD, np = D - r, max(0, p - r)
        elif m == "lea" and o.startswith("esp, "):
            causes.setdefault(a, set()).add("esp-rewrite-lea"); pruned = True
        elif m == "mov" and o.startswith("esp, "):
            causes.setdefault(a, set()).add("esp-rewrite-mov"); pruned = True
        elif m in ("leave", "pushad", "popad", "x87-boundary"):
            causes.setdefault(a, set()).add("esp-shape"); pruned = True
        if pruned: continue
        for x in body.get(a, ()):
            stack.append((x, nD, np))
    return collect, causes

def imms_uni(t):
    return ret_imm(t)[3] and len(set(ret_imm(t)[3])) == 1

FRAMES = {0x778710:"A", 0x779B50:"B", 0x779DD0:"C", 0x5CEEF0:"D", 0x76C290:"E", 0x778A20:"F", 0x5D7590:"T16"}
ROWS = [0x77884F,0x77890C,0x778956,0x779C3D,0x779EBD,
        0x5CEFC9,0x5CF10E,0x5CF162,0x5CF284,0x5CF2E0,0x5CF42C,0x5CF4C7,
        0x5D76A9,0x76C555,0x778BCF,0x778DD1,0x778E24]
print("\n== 行→唯一 E8 头（闭包成员）==")
rowhead = {}
for r in ROWS:
    hs = [h for h in FRAMES if r in ret_imm(h)[2]]
    allh = sorted([h for h in e8set if r in ret_imm(h)[2]]) if False else hs
    rowhead[r] = hs
    print("  %06X -> %s" % (r, [FRAMES[h] for h in hs] or "不在七帧"))

# 全镜像 stamp（两种 imm）
pat = re.compile(r"^dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\], (0x[0-9a-f]+)$")
stamps = {0x7EA5F4: [], 0x7E1B04: []}
for a, s, b, m, o in insns:
    if m == "mov":
        mm = pat.match(o)
        if mm:
            imm = int(mm.group(2), 16)
            if imm in stamps:
                d = mm.group(1); d = int(d, 16) if d.startswith("0x") else int(d)
                stamps[imm].append((a, d))
for k in stamps:
    print("\n== 全镜像 mov [esp+d],%06X：%d 处 ==" % (k, len(stamps[k])))
    for a, d in stamps[k]:
        hs = [FRAMES[h] for h in FRAMES if a in ret_imm(h)[2]]
        print("   %06X disp=%s 帧=%s" % (a, hex(d), hs))

# 逐帧 D-sim
LEA = {}
for r in ROWS:
    k = IDX.get(r)
    if k:
        prev = insns[k-1]
        mm = None
        if prev[3] == "lea":
            mm = re.match(r"^ecx, (?:dword ptr )?\[esp \+ (0x[0-9a-f]+|\d+)\]$", prev[4])
        if mm:
            d = mm.group(1); d = int(d,16) if d.startswith("0x") else int(d)
            LEA[r] = (prev[0], d)
print("\nwitness lea:", {hex(r): (hex(v[0]), hex(v[1])) for r, v in LEA.items()})

targetset0 = set()
for h, name in FRAMES.items():
    v, body, seen, _ = ret_imm(h)
    for r in ROWS:
        if r in seen: targetset0.add(r)
        lea = LEA.get(r, (None,None))[0]
        if lea in seen: targetset0.add(lea)
    for imm in stamps:
        for a, d in stamps[imm]:
            if a in seen: targetset0.add(a)
targetset = targetset0  # used inside dsim

def run_frame(h, resmap, label):
    collect, causes = dsim(h, resmap)
    print("\n===== 帧 %s head=%06X [%s] =====" % (FRAMES[h], h, label))
    rows_here = [r for r in ROWS if r in ret_imm(h)[2]]
    for r in rows_here:
        Dr = collect.get(r); lea, ld = LEA[r]; Dl = collect.get(lea)
        W = None
        if Dl and len(Dl) == 1 and next(iter(Dl)) is not None:
            W = ld - next(iter(Dl))
        print("  row %06X D=%s | lea@%06X D=%s disp=%s → W=%s" % (
            r,
            sorted(hex(x) for x in Dr) if Dr else "剪枝",
            lea, sorted(hex(x) for x in Dl) if Dl else "剪枝", hex(ld),
            hex(W) if W is not None else "-"))
        if W is not None:
            for imm in stamps:
                for a, d in stamps[imm]:
                    Da = collect.get(a)
                    if Da and len(Da) == 1:
                        P = d - next(iter(Da))
                        mark = "  <<<== W 命中" if P == W else ("  (错位 %s)" % hex(P - W) if P - W in (12, -12, 0xC, -0xC) else "")
                        if a in ret_imm(h)[2]:
                            print("      stamp %06X imm=%06X disp=%s D=%s P=%s%s" % (
                                a, imm, hex(d), hex(next(iter(Da))), hex(P), mark))
    print("  剪枝因:", {("%06X"%k if isinstance(k,int) else k): sorted(v) if isinstance(v,set) else v for k,v in causes.items()})
    return collect

for h, name in FRAMES.items():
    run_frame(h, RES if h == 0x5CEEF0 else {}, "STRICT+帧D两indirect落实")
# HYPV：仅保留两落实，其余 indirect 剪枝 —— 与上面帧 D 相同（UNRES 本就剪枝），
# 换 HYP8：未落实间接 call 假设清 8 放行，看 7 行是否仍 D 单例
def run_D(mode):
    resmap = {}
    if mode in ("HYP8",):
        resmap = {0x5CF038: 8, 0x5CF350: 8, 0x5CF556: 8}
    if mode != "PURE":
        resmap.update(RES)
    print("\n##### 帧 D mode=%s #####" % mode)
    run_frame(0x5CEEF0, resmap, mode)
run_D("PURE")   # 全 indirect 剪枝（含两处可落实）——检验是否仍能闭合
run_D("HYP8")   # 三未落实假设清 8
print("\n== 关键 callee ret-imm 亲查 ==")
for t in (0x528C00, 0x525A10, 0x5256F0, 0x527F20, 0x526D90, 0x5295F0, 0x40E340, 0x7B6290, 0x473FC0, 0x473D10, 0x7B5B30, 0x52B4F0):
    v, body, seen, imms = ret_imm(t)
    print("  %06X: ret交集=%s 全部ret=%s 闭包大小=%d" % (t, v, sorted(set(imms)), len(body)))
