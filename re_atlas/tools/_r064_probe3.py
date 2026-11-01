# _r064_probe3.py -- R-064 仲裁探针3：函数边界 + ret-imm 普查 + 路径敏感 esp-D 归一化 + 17 行 witness 槽逐行配对
# 独立实现（自写 PE 装载复用 _r064_probe1；自写前向函数体/前驱图/回溯定头；自写 D-sim）。
# 两种模式：STRICT（未知 ret-imm 的 call 剪枝，仅零推规则）/ HYP4（间接 call 且 0<p<=4 时假设清 4p，R-063b 规则2 的独立化）。
import struct, sys
from collections import deque
import capstone
from _r064_probe1 import rd, rd32, data, secs, EXE

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
TEXT_LO, TEXT_HI = 0x401000, 0x7E1000

def decode_one(va):
    b = rd(va, 16)
    if b is None: return None
    for ins in md.disasm(b, va):
        return ins
    return None

# ---- 1. E8 call 目标集 + 前向函数体 + 前驱图 ----
print("== 1. 线性扫描 .text 提取 E8 call 目标 ==")
call_targets = set()
va = TEXT_LO
raw = data[0x1000:0x3E1000]
i = 0
while i < len(raw) - 5:
    if raw[i] == 0xE8:
        rel = struct.unpack_from("<i", raw, i+1)[0]
        tgt = TEXT_LO + i + 5 + rel
        if TEXT_LO <= tgt < TEXT_HI:
            call_targets.add(tgt)
    i += 1
print("   E8 目标数 =", len(call_targets))

body = {}      # addr -> (mnemonic, op_str, size)
preds = {}     # addr -> set(prev addr)
def walk_from(entry):
    seen = set()
    stack = [entry]
    while stack:
        va = stack.pop()
        while True:
            if va in seen or not (TEXT_LO <= va < TEXT_HI):
                break
            ins = body.get(va) or None
            if ins is None:
                d = decode_one(va)
                if d is None: break
                ins = (d.mnemonic, d.op_str or "", d.size)
                body[va] = ins
            seen.add(va)
            m, ops, sz = ins
            nxt = va + sz
            if m == "ret":
                break
            if m == "jmp":
                try: t = int(ops, 16)
                except ValueError: break
                preds.setdefault(t, set()).add(va)
                va = t
                continue
            if m.startswith("j"):
                try: t = int(ops, 16)
                except ValueError: pass
                else:
                    preds.setdefault(t, set()).add(va)
                    stack.append(t)
                preds.setdefault(nxt, set()).add(va)
                va = nxt
                continue
            preds.setdefault(nxt, set()).add(va)
            va = nxt

for t in sorted(call_targets):
    walk_from(t)
print("   函数体指令数 =", len(body))

def find_head(site):
    """回溯 BFS，收集路径上 E8 目标（函数头候选）"""
    seen = {site}; q = deque([site]); cands = []
    while q:
        a = q.popleft()
        if a in call_targets:
            cands.append(a)
        for p in preds.get(a, ()):  # 仅已有前驱
            if p not in seen:
                seen.add(p); q.append(p)
        if len(seen) > 200000: break
    return sorted(set(cands))

# ---- 2. ret-imm 解析（callee 闭包内全部 ret；一致才给出，否则 None；缓存） ----
from collections import deque as _dq
def _closure_rets(head):
    seen = set(); q = _dq([head]); out = []
    while q:
        a = q.popleft()
        while True:
            if a in seen or a not in body: break
            seen.add(a)
            m, ops, sz = body[a]
            if m == "ret":
                out.append((a, int(ops, 16) if ops else 0)); break
            if m == "jmp":
                try: a = int(ops, 16); continue
                except ValueError: break
            if m.startswith("j"):
                try: q.append(int(ops, 16))
                except ValueError: pass
            a = a + sz
    return out

_imm_cache = {}
def ret_imm(callee):
    if callee in _imm_cache: return _imm_cache[callee]
    rets = _closure_rets(callee)
    if not rets:
        res = None
    else:
        imms = {i for _, i in rets}
        res = imms.pop() if len(imms) == 1 else None
    _imm_cache[callee] = res
    return res

# ---- 3. D-sim ----
def dsim(head, pois, mode):
    """前向 DFS；state=(addr,D,p)。返回 {poi_va: set of D}。mode: STRICT/HYP4"""
    res = {p: set() for p in pois}
    visited = set()
    causes = {}
    stack = [(head, 0, 0)]
    steps = 0
    while stack:
        va, D, p = stack.pop()
        steps += 1
        if steps > 3_000_000: break
        while True:
            if va not in body: break
            if va in res: res[va].add(D)
            key = (va, D, p)
            if key in visited: break
            visited.add(key)
            m, ops, sz = body[va]
            nxt = va + sz
            if m == "push":
                D += 4; p += 1; va = nxt; continue
            if m == "pop":
                D -= 4; p = 0; va = nxt; continue
            if m == "sub" and ops.startswith("esp,"):
                D += int(ops.split(",")[1], 16); va = nxt; continue
            if m == "add" and ops.startswith("esp,"):
                D -= int(ops.split(",")[1], 16); p = 0; va = nxt; continue
            if m == "call":
                ops0 = ops.strip()
                if ops0.startswith("0x"):
                    tgt = int(ops0, 16)
                else:
                    tgt = None  # 间接 call
                imm = ret_imm(tgt) if tgt is not None else None
                VERIFIED = {0x5CEF6B: 4, 0x5CEF78: 4}  # CCFileClass vtable 直读落实（probe4 B）
                if imm is None:
                    if va in VERIFIED and mode in ("HYP4", "HYPV"):
                        D -= VERIFIED[va]; p = 0
                        causes.setdefault("verified-vtable@%#x(imm=%d)" % (va, VERIFIED[va]), None)
                        va = nxt; continue
                    if p == 0:
                        causes.setdefault("rule1-zero-push@%#x" % va, tgt)
                        va = nxt; continue
                    if mode == "HYP4" and tgt is None and p <= 4:
                        imm_h = 4 * p
                        D -= imm_h; p = 0
                        causes.setdefault("hyp4@%#x(imm=%d)" % (va, imm_h), tgt)
                        va = nxt; continue
                    causes.setdefault("ret-unknown-prune@%#x" % va, tgt)
                    break
                D -= imm; p = 0
                va = nxt; continue
            if m == "ret":
                break
            if m == "jmp":
                try: va = int(ops, 16)
                except ValueError:
                    causes.setdefault("jmp-indirect-prune@%#x" % va, None); break
                continue
            if m.startswith("j"):
                try: t = int(ops, 16)
                except ValueError: t = None
                if t is not None: stack.append((t, D, p))
                va = nxt; continue
            if m in ("mov", "xchg") and (" esp" in ops.split(",")[0] or ops.split(",")[0] == "esp"):
                causes.setdefault("esp-write-prune@%#x" % va, None); break
            if m == "leave":
                causes.setdefault("leave-prune@%#x" % va, None); break
            va = nxt; continue
    return res, causes, steps

if __name__ == '__main__':
    MODE = sys.argv[1] if len(sys.argv) > 1 else 'STRICT'
    # ---- 4. 逐帧装配 POI 并跑 ----
    ROWS = [  # (行 VA, lea VA, lea disp)
        (0x5cefc9, 0x5cefc5, 0x38), (0x5cf10e, 0x5cf10a, 0x38), (0x5cf162, 0x5cf15e, 0x38),
        (0x5cf284, 0x5cf280, 0x38), (0x5cf2e0, 0x5cf2dc, 0x38), (0x5cf42c, 0x5cf428, 0x38),
        (0x5cf4c7, 0x5cf4c3, 0x38), (0x5d76a9, 0x5d76a2, 0x88), (0x76c555, 0x76c551, 0x38),
        (0x77884f, 0x77884b, 0x38), (0x77890c, 0x778908, 0x38), (0x778956, 0x778952, 0x38),
        (0x778bcf, 0x778bcb, 0x38), (0x778dd1, 0x778dcd, 0x38), (0x778e24, 0x778e20, 0x38),
        (0x779c3d, 0x779c39, 0x24), (0x779ebd, 0x779eb9, 0x24),
    ]
    STAMPS = [  # (VA, disp, imm, 标签)
        (0x7787c0, 0x38, 0x7E1B04, "G-A(R-062窗1)"), (0x7787d1, 0x34, 0x7E1AFC, "List-A"),
        (0x7787f7, 0x30, 0x7EA5F4, "I-A(补stampA)"),
        (0x779bb3, 0x24, 0x7E1B04, "G-B(R-062窗2)"), (0x779bc4, 0x20, 0x7E1AFC, "List-B"),
        (0x779bea, 0x1c, 0x7EA5F4, "I-B(补stampB)"),
        (0x779e33, 0x24, 0x7E1B04, "G-C(R-062窗3)"), (0x779e44, 0x20, 0x7E1AFC, "List-C"),
        (0x779e6a, 0x1c, 0x7EA5F4, "I-C(补stampC)"),
        (0x5cef20, 0x34, 0x7E1AFC, "List-D"), (0x5cef41, 0x28, 0x7EA5F4, "I-D(R-063b stamp1)"),
        (0x76c484, 0x3c, 0x7E1AFC, "List-E"), (0x76c4a4, 0x30, 0x7EA5F4, "I-E(R-063b stamp2)"),
        (0x778b20, 0x2c, 0x7EA5F4, "I-F(R-063b stamp3)"), (0x778b83, 0x84, 0x7E1668, "CDF-F"),
        (0x5d761d, 0x78, 0x7EA5F4, "I-16"),
    ]

    # 帧分组：由反汇编结构人工+回溯定头；先对每行找头候选
    frame_pois = {}
    for row_va, lea_va, disp in ROWS:
        cands = find_head(lea_va)
        frame_pois.setdefault(tuple(cands[:2]), []).append((row_va, lea_va, disp))

    print("\n== 2. 各 witness 行的函数头候选 ==")
    for cands, rows in sorted(frame_pois.items()):
        print("   头候选 %s -> 行 %d 个: %s" % (["%#x" % c for c in cands], len(rows),
              ",".join("%#x" % r[0] for r in rows[:4])))

    # stamp 的头候选
    print("\n== 3. 各 stamp 的函数头候选 ==")
    stamp_head = {}
    for va, disp, imm, lab in STAMPS:
        cands = find_head(va)
        stamp_head[va] = cands
        print("   %-22s @%#x 头候选 %s" % (lab, va, ["%#x" % c for c in cands[:3]]))

    def run_frame(head, poi_leas, poi_stamps, mode):
        pois = [lv for _, lv, _ in poi_leas] + [p for p, _, _, _ in poi_stamps]
        res, causes, steps = dsim(head, pois, mode)
        print("\n   ---- 帧 head=%#x 模式=%s steps=%d ----" % (head, mode, steps))
        for (row_va, lea_va, disp) in poi_leas:
            Ds = res.get(lea_va, set())
            Ws = sorted(disp - d for d in Ds)
            print("   行 %#x lea[%#x]+0x%02x D=%s W=%s" % (
                row_va, lea_va, disp,
                ",".join(hex(d) for d in sorted(Ds)) if Ds else "UNREACHED",
                ",".join(hex(w) for w in Ws) if Ws else "-"))
        for (va, disp, imm, lab) in poi_stamps:
            Ds = res.get(va, set())
            Ps = sorted(disp - d for d in Ds)
            print("   stamp %-16s @%#x [esp+0x%02x]=%#x D=%s P=%s" % (
                lab, va, disp, imm,
                ",".join(hex(d) for d in sorted(Ds)) if Ds else "UNREACHED",
                ",".join(hex(p) for p in Ps) if Ps else "-"))
        if causes:
            csum = {}
            for c in causes:
                k = c.split("@")[0]; csum[k] = csum.get(k, 0) + 1
            print("   剪枝/规则因: " + ", ".join("%s×%d" % kv for kv in sorted(csum.items())))
            for c in sorted(causes):
                print("      " + c)
        return res

    # (MODE 由上方设置)

    # 对每个唯一帧（按行头候选分组）跑两种头选择
    frames = {}
    for row_va, lea_va, disp in ROWS:
        cands = find_head(lea_va)
        key = cands[0] if cands else None
        frames.setdefault(key, {"leas": [], "stamps": []})
        frames[key]["leas"].append((row_va, lea_va, disp))
    for va, disp, imm, lab in STAMPS:
        cands = stamp_head[va]
        key = cands[0] if cands else None
        if key in frames:
            frames[key]["stamps"].append((va, disp, imm, lab))
        else:
            # stamp 在另一个函数（如 List/的帧与行帧不同）：单独成帧
            frames.setdefault(key, {"leas": [], "stamps": []})[ "stamps"].append((va, disp, imm, lab))

    print("\n== 4. 模式 %s 下逐帧 D-sim ==" % MODE)
    for head in sorted(frames, key=lambda x: (x is None, x)):
        fr = frames[head]
        if not fr["leas"] and not fr["stamps"]: continue
        if head is None:
            print("   [帧无头候选，跳过]"); continue
        run_frame(head, fr["leas"], fr["stamps"], MODE)

    print("\n== 5. 关键 callee ret-imm 表 ==")
    callees = [0x40e320, 0x40e340, 0x525a10, 0x526810, 0x7b4630, 0x7b4620, 0x7b46f0, 0x4325c0,
               0x7b5440, 0x7b5b30, 0x7b6290, 0x7b66c0, 0x7b5340, 0x5256f0, 0x526d90, 0x526a30,
               0x473a80, 0x52ace0, 0x5cf5f0, 0x528c00, 0x778f30, 0x778710, 0x431b80, 0x76c970,
               0x76ca60, 0x76bfb0, 0x7b6280, 0x7b4690, 0x527f20, 0x778a20]
    for c in callees:
        print("   %#x ret-imm = %s" % (c, ret_imm(c)))