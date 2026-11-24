# PROBE-UNNAMED-R2 · 无名候选行的 ② 能否用虚表 / RTTI 钉住（只读探针）
#
# 只读 gamemd.exe；只写本目录（probe.tsv / EVIDENCE/）。
# 用法：
#   python probe.py sample           # 第 1 步：抽样，打印抽样命令与 12 个 entry
#   python probe.py vt               # 建全镜像虚表清单（缓存 vt_inventory.tsv）
#   python probe.py row <entry>      # 第 2 步：判一行 ②
#   python probe.py rings <entry>    # 第 3 步：判 ③④
#
# 技术条（R14_COMMON §13，必须遵守）：
#   - RTTI 的 pTD / pCHD 是绝对 VA，不是 RVA；按 IB+rva 解会越界并 fail-closed 误判
#   - 装饰名在 TD+8 是内联串，不是指针
#   - COL 在 vt-4，且 vt-4 存的是 COL 的**指针**（不是结构体本身）
#   - ㉓ 判 ④ 须枚举该虚表全部写点，排除 atexit 注册的全局析构器与删除析构器

import sys, os, csv, struct, hashlib, json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pefile

ROOT = r"D:\Project\ra2-campaign-forge"
IMG = os.path.join(ROOT, r"ra2youli\gamemd.exe")
R14 = os.path.join(ROOT, r"lead\next_re_20261117_r14")
OUT = os.path.join(R14, "PROBE_UNNAMED_R2")
EV = os.path.join(OUT, "EVIDENCE")
HITS = os.path.join(R14, r"SURVEY_3B2\hits_detail.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
COVER = os.path.join(R14, r"COVERAGE\coverage.tsv")

EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

data = open(IMG, "rb").read()
SHA = hashlib.sha256(data).hexdigest().upper()

pe = pefile.PE(IMG, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase          # 0x400000
SOI = pe.OPTIONAL_HEADER.SizeOfImage       # 0x796000
SECS = [(s.Name.rstrip(b"\x00").decode(), s.VirtualAddress + IB, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
SEC = {n: (va, vs, raw, rs) for n, va, vs, raw, rs in SECS}
TEXT_VA, TEXT_VS, TEXT_RAW, TEXT_RS = SEC[".text"]
TEXT_LO, TEXT_HI = TEXT_VA, TEXT_VA + TEXT_VS
RDATA_VA, RDATA_VS, _, _ = SEC[".rdata"]


def va2off(va):
    for n, sva, vs, raw, rs in SECS:
        if sva <= va < sva + max(vs, rs):
            off = raw + (va - sva)
            if 0 <= off < len(data):
                return off
    return None


def rd(va, n):
    o = va2off(va)
    return None if o is None else data[o:o + n]


def u32(va):
    b = rd(va, 4)
    return None if b is None or len(b) < 4 else struct.unpack("<I", b)[0]


def mapped(va):
    return va is not None and va2off(va) is not None


def ptr_at(va):
    """读一个指针字段。本镜像 RTTI 用绝对 VA；若值 < ImageBase 才按 RVA 再试一次。
    返回 (目标VA 或 None, 说明)。"""
    v = u32(va)
    if v is None:
        return None, "unmapped"
    if v == 0:
        return None, "null"
    if v >= IB and mapped(v):
        return v, "absVA"
    if v < IB and mapped(IB + v):
        return IB + v, "RVA->IB+rva"
    return None, "unresolved:0x%08X" % v


def in_text(va):
    return va is not None and TEXT_LO <= va < TEXT_HI


# ---------------------------------------------------------------- 装饰名
def demangle(raw):
    """TD+8 内联装饰名的**原样保留**（只做显示用去前缀，绝不猜类名）。"""
    s = raw.decode("latin1")
    return s


# ---------------------------------------------------------------- RTTI 链
def col_of_vt(vt):
    """vt[-1] → COL 指针；COL 20B = sig/offset/cdOffset/pTD/pCHD。带诊断。"""
    diag = {}
    col, how = ptr_at(vt - 4)
    diag["col_ptr"] = "%s(%s)" % ("0x%08X" % u32(vt - 4) if u32(vt - 4) is not None else "?", how)
    if col is None:
        diag["fail"] = "vt-4 不是可解指针"
        return None, diag
    b = rd(col, 20)
    if b is None or len(b) < 20:
        diag["fail"] = "COL 20B 不可读"
        return None, diag
    sig, off, cd, ptd, pchd = struct.unpack("<IIIII", b)
    diag.update(col=col, sig=sig, off=off, cd=cd, ptd=ptd, pchd=pchd)
    if sig != 0:
        diag["fail"] = "COL.sig=%d != 0" % sig
        return None, diag
    td, howtd = ptr_at(col + 12)
    diag["td_how"] = howtd
    if td is None:
        diag["fail"] = "COL+0xC pTD 不可解 (%s)" % howtd
        return None, diag
    diag["td"] = td
    nb = rd(td + 8, 256)
    if nb is None:
        diag["fail"] = "TD+8 不可读"
        return None, diag
    # TD+0 应指向 TD 的 vftable（.rdata），TD+4 应为 0 —— 形状自检
    diag["td_vft"] = "0x%08X" % u32(td)
    diag["td_pad"] = u32(td + 4)
    if not (nb[:4] in (b".?AV", b".?AU")):
        diag["fail"] = "TD+8 非内联装饰名（首4字节 %s）" % nb[:4].hex()
        return None, diag
    end = nb.find(b"\x00")
    if end < 0:
        diag["fail"] = "TD+8 名串无 NUL 终止"
        return None, diag
    diag["name"] = demangle(nb[:end])
    diag["td_bytes"] = nb[:end].hex()
    return diag, diag


# ---------------------------------------------------------------- 虚表清单
# 判定一张表：vt 处的槽值全部落在 .text；vt-4 是 COL 指针且 COL.sig==0 且 TD+8 是装饰名。
def vt_of_slot(sa):
    """给定一个槽地址，尝试所有可能的 vt（sa-4k），返回命中的 (vt, slot_no) 列表。"""
    out = []
    for k in range(0, MAX_SLOT):
        vt = sa - 4 * k
        c = VT_CACHE.get(vt)
        if c is not None:
            if k < c["nslots"]:
                out.append((vt, k))
            continue
    return out


MAX_SLOT = 400
VT_CACHE = {}


def build_vt_inventory(verbose=True):
    """枚举 .rdata/.data 中所有「vt-4 是 COL 指针且 sig==0」的表起点。"""
    cand = []
    for secname in (".rdata", ".data"):
        if secname not in SEC:
            continue
        sva, svs, sraw, srs = SEC[secname]
        lo = max(sva, IB)
        hi = min(sva + max(svs, srs), IB + SOI)
        a = lo if lo % 4 == 0 else lo + (4 - lo % 4)
        while a + 4 <= hi:
            colv = u32(a - 4)
            if colv:
                col = None
                if colv >= IB and mapped(colv):
                    col = colv
                elif colv < IB and mapped(IB + colv):
                    col = IB + colv
                if col is not None:
                    b = rd(col, 20)
                    if b is not None and len(b) == 20:
                        sig = struct.unpack("<I", b[:4])[0]
                        if sig == 0:
                            cand.append(a)
            a += 4
    if verbose:
        print("候选表起点（COL.sig==0）: %d" % len(cand))

    vt = {}
    for a in cand:
        # 表长：连续 .text 指针
        n = 0
        while n < MAX_SLOT:
            v = u32(a + 4 * n)
            if v is None or not in_text(v):
                break
            n += 1
        if n == 0:
            continue
        diag, _ = col_of_vt(a)
        if diag is None:
            continue
        vt[a] = {"vt": a, "nslots": n, "col": diag["col"], "off": diag["off"],
                 "sig": diag["sig"], "td": diag["td"], "name": diag["name"],
                 "slots": [u32(a + 4 * i) for i in range(n)]}
    VT_CACHE.clear()
    VT_CACHE.update(vt)
    if verbose:
        print("可用虚表（含 RTTI 且表长>0）: %d" % len(vt))
    # 落盘缓存
    p = os.path.join(OUT, "vt_inventory.tsv")
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["vt_addr", "nslots", "col", "col_offset", "td", "class_name",
                    "slots_head", "slot_text_entries"])
        for a in sorted(vt):
            t = vt[a]
            w.writerow(["%08X" % a, t["nslots"], "%08X" % t["col"], t["off"],
                        "%08X" % t["td"], t["name"],
                        ",".join("%08X" % x for x in t["slots"][:8]),
                        ",".join("%08X" % x for x in t["slots"])])
    return vt


# ---------------------------------------------------------------- 抽样
def load_unnamed():
    rows = list(csv.DictReader(open(HITS, encoding="utf-8"), delimiter="\t"))
    un = [r for r in rows if r["p3b2_named"] == "False" and r["name"].startswith("sub_")]
    un.sort(key=lambda r: int(r["entry"], 16))
    return un


def sample12():
    un = load_unnamed()
    n = len(un)
    picks = [0, n - 1]
    span = (n - 2) - 1        # 内部索引 1..n-2
    for k in range(1, 11):
        idx = 1 + (k * span) // 11
        picks.append(idx)
    picks = sorted(set(picks))
    return un, [(i, un[i]) for i in picks]


# ---------------------------------------------------------------- 报告辅助
def hexs(v):
    return "0x%08X" % v if v is not None else "-"


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sample"
    print("IMAGE  =", IMG)
    print("SHA256 =", SHA, "OK" if SHA == EXPECT_SHA else "*** MISMATCH ***")
    print("IB=0x%08X SOI=0x%08X .text=[0x%08X,0x%08X)" % (IB, SOI, TEXT_LO, TEXT_HI))

    if cmd == "sample":
        un, picks = sample12()
        print("无名池 = %d" % len(un))
        print("规则: 位置1(最小) + 最后1个(最大) + 内部 10 等分点 floor(k*(n-3)/11)")
        for i, r in picks:
            print("  pos %4d/%d  %s  %s  grade=%s  size=%s  n_call=%s"
                  % (i + 1, len(un), r["entry"], r["subsystem"], r["grade"], r["size"], r["n_call"]))
    elif cmd == "vt":
        build_vt_inventory()
    elif cmd == "row":
        e = int(sys.argv[2], 16)
        build_vt_inventory(verbose=False)
        row(e)
    elif cmd == "rings":
        e = int(sys.argv[2], 16)
        build_vt_inventory(verbose=False)
        v = row(e)
        if v["verdict"].startswith("成立"):
            rr = rings(e, v)
            print("\n".join(rr["lines"]))
            print("③=%s (%s)" % (rr["ring3b"], rr["ring3b_reason"]))
            print("④=%s (%s)" % (rr["ring4"], rr["ring4_reason"]))
    elif cmd == "sweep":
        sweep()
    elif cmd == "poolstats":
        poolstats()
    else:
        print("unknown cmd")


def stub_forward(e):
    """「转发行桩」变体：entry 本身不在槽里，但某个**占据虚表槽**的函数体是
    `call/jmp <entry>; ret`（纯转发，不改参数）⇒ 类身份同样可钉。
    这是同一条方法（槽 + RTTI）的变体，须与「严格槽值==entry」分开报。"""
    out = []
    ci = build_call_index()
    inv_tables = VT_CACHE if VT_CACHE else build_vt_inventory(verbose=False)
    for site, mn in ci["idx"].get(e, []):
        occ = raw_slot_occurrences(site)
        good = [o for o in occ if o["name"]]
        if not good:
            continue
        ins, sz = body(site)
        if not ins:
            # 桩常常不是 atlas 独立条目（比 atlas 粒度更细），直接反汇编小窗口
            raw = rd(site, 24)
            if raw is None:
                continue
            ins = list(md.disasm(raw, site))[:6]
            sz = sum(i.size for i in ins) if ins else None
        if not ins or sz is None or sz > 40:
            continue
        txt = [(i.mnemonic, i.op_str) for i in ins]
        pure = (txt and txt[0][0] in ("call", "jmp")
                and txt[0][1] == "0x%x" % e
                and len(txt) <= 8
                and all(t[0] in ("ret", "nop") for t in txt[1:]))
        adapter = (txt and txt[0][0] == "call" and txt[0][1] == "0x%x" % e)
        if not (pure or adapter):
            continue
        o = good[0]
        out.append({"stub": site, "kind": "纯转发" if pure else "带后处理(弱)",
                    "vt": o["vt"], "slot": o["slot_no"], "off": o["off"],
                    "cls": o["name"], "body": " / ".join("%s %s" % t for t in txt[:4])})
    return out


def row(e):
    """第 2 步：判一行 ②。
    两条独立路径：
      (A) 原始扫描 .rdata/.data 里所有 dd <e> 的出现点（不依赖虚表清单，故能区分
          「不在任何虚表槽」与「在槽里但 RTTI 链断」）；
      (B) 与已建虚表清单交叉核对槽号。
    """
    print("\n=== ROW 0x%08X ===" % e)
    occ = raw_slot_occurrences(e)
    print("原始 dd<entry> 出现点: %d" % len(occ))
    if not occ:
        st = stub_forward(e)
        if st:
            s = st[0]
            print("  ⇒ 严格判据（槽值==entry）：不在任何虚表槽")
            print("  ⇒ 变体判据（转发行桩）：%d 处 —— stub 0x%08X [%s] %s → vt=0x%08X slot=%d %s"
                  % (len(st), s["stub"], s["kind"], s["body"], s["vt"], s["slot"], s["cls"]))
            return {"entry": e, "occ": [], "verdict": "成立(经stub)",
                    "reason": "严格：不在任何虚表槽；经转发行桩成立：stub 0x%08X [%s] `%s` 驻 0x%08X slot%d(off=%d)"
                              % (s["stub"], s["kind"], s["body"], s["vt"], s["slot"], s["off"]),
                    "class_name": s["cls"], "vt": s["vt"], "slot": s["slot"], "off": s["off"],
                    "vt_count": 1, "stub": st,
                    "names": [x["cls"] for x in st]}
        print("  ⇒ 该 entry 在 .rdata/.data 中没有任何 dd 出现点 ⇒ ② 不成立：不在任何虚表槽里")
        return {"entry": e, "occ": [], "verdict": "不成立",
                "reason": "不在任何虚表槽里（.rdata/.data 全扫 0 个 dd<entry>；亦无转发行桩）",
                "class_name": "未取得", "vt": None, "slot": None, "off": None,
                "vt_count": 0}

    good, bad = [], []
    for o in occ:
        print("  slot 0x%08X  @%s  table_start=%s  slot_no=%s  rtti=%s"
              % (o["slot"], o["sec"], hexs(o["vt"]) if o["vt"] else "-",
                 o["slot_no"] if o["slot_no"] is not None else "-",
                 o["name"] if o["name"] else ("FAIL: " + o["fail"])))
        if o["name"]:
            print("        COL=0x%08X sig=%d off=%d td=0x%08X name=%s%s"
                  % (o["col"], o["sig"], o["off"], o["td"], o["name"],
                     "   [主表]" if o["off"] == 0 else "   [子对象接口表 off=%d]" % o["off"]))
            good.append(o)
        else:
            print("        COL=%s sig=%s 断因=%s" % (
                hexs(o["col"]) if o.get("col") else "-",
                o.get("sig") if o.get("sig") is not None else "-", o["fail"]))
            bad.append(o)

    if not good:
        reasons = sorted(set(o["fail"] for o in bad))
        return {"entry": e, "occ": occ, "verdict": "不成立",
                "reason": "在虚表槽里但 RTTI 链断：" + " / ".join(reasons),
                "class_name": "未取得", "vt": None, "slot": None, "off": None,
                "vt_count": len(occ)}

    # 优先主表（COL.offset==0）；否则取第一张子对象接口表
    main = [o for o in good if o["off"] == 0]
    pick = main[0] if main else good[0]
    # 主表与子表名不同则如并列
    names = []
    for o in good:
        if o["name"] not in names:
            names.append(o["name"])
    return {"entry": e, "occ": occ, "verdict": "成立",
            "reason": "vt[%d]@0x%08X COL.sig=0 off=%d TD+8 内联名" % (
                pick["slot_no"], pick["vt"], pick["off"]),
            "class_name": pick["name"], "vt": pick["vt"], "slot": pick["slot_no"],
            "off": pick["off"], "vt_count": len(set(o["vt"] for o in occ if o["vt"])),
            "names": names, "good": good, "bad": bad}


def raw_slot_occurrences(e):
    """在 .rdata/.data 里找所有 dd <e>，并尝试定表头 + 走 RTTI 链（带断因）。"""
    pat = struct.pack("<I", e)
    out = []
    for secname in (".rdata", ".data"):
        if secname not in SEC:
            continue
        sva, svs, sraw, srs = SEC[secname]
        lo = max(sva, IB)
        hi = min(sva + max(svs, srs), IB + SOI)
        off0 = va2off(lo)
        off1 = va2off(hi - 4)
        if off0 is None or off1 is None:
            continue
        a = lo if lo % 4 == 0 else lo + (4 - lo % 4)
        blob = data
        while a + 4 <= hi:
            o = va2off(a)
            if o is None:
                a += 4
                continue
            if blob[o:o + 4] == pat:
                out.append(classify_slot(a, secname))
            a += 4
    return out


def classify_slot(sa, secname):
    """从一个槽地址回退定出表起点，然后走 COL→TD→名字链。"""
    r = {"slot": sa, "sec": secname, "vt": None, "slot_no": None,
         "col": None, "sig": None, "off": None, "td": None, "name": None, "fail": None}
    # 回退：连续 .text 指针段
    start = sa
    while start - 4 >= IB:
        v = u32(start - 4)
        if v is None or not in_text(v):
            break
        start -= 4
    r["vt"] = start
    r["slot_no"] = (sa - start) // 4
    d, _ = col_of_vt(start)
    if d is None:
        r["fail"] = "表头 %s 处 RTTI 不可解" % hexs(start)
        if _:
            r["col"] = _.get("col")
            r["sig"] = _.get("sig")
            if _.get("fail"):
                r["fail"] = _.get("fail")
        return r
    r.update(col=d["col"], sig=d["sig"], off=d["off"], td=d["td"], name=d["name"])
    return r


# ---------------------------------------------------------------- ③④
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True          # 必须：否则遇到数据字节会中止反汇编（错源 ㉖）

ATLAS_PATH = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
_ATLAS = {}


def load_atlas():
    if _ATLAS:
        return _ATLAS
    for r in csv.DictReader(open(ATLAS_PATH, encoding="utf-8"), delimiter="\t"):
        try:
            _ATLAS[int(r["entry"], 16)] = int(r["size"])
        except Exception:
            pass
    return _ATLAS



def body(e):
    sz = load_atlas().get(e)
    if sz is None:
        return None, None
    raw = rd(e, sz)
    if raw is None:
        return None, sz
    return list(md.disasm(raw, e)), sz


CALL_INDEX = None


def build_call_index():
    """全 .text 扫 E8/E9，建 target → [site...] 索引（错源 ㉖：报覆盖规模）。"""
    global CALL_INDEX
    if CALL_INDEX is not None:
        return CALL_INDEX
    raw = rd(TEXT_LO, TEXT_HI - TEXT_LO)
    idx = {}
    n = 0
    for i in md.disasm(raw, TEXT_LO):
        n += 1
        if i.mnemonic in ("call", "jmp") and i.op_str.startswith("0x"):
            t = int(i.op_str, 16)
            idx.setdefault(t, []).append((i.address, i.mnemonic))
    CALL_INDEX = {"idx": idx, "n_insn": n}
    return CALL_INDEX


def insn_sites_of_table(vt):
    """枚举 .text 中所有把 imm32==vt 写进去的指令站点（㉓：必须全部枚举）。"""
    pat = struct.pack("<I", vt)
    out = []
    o = TEXT_RAW
    end = TEXT_RAW + TEXT_RS
    while True:
        k = data.find(pat, o, end)
        if k < 0:
            break
        fva = TEXT_LO + (k - TEXT_RAW)
        # 反汇编定位承载该立即数的指令
        for start in range(max(TEXT_LO, fva - 10), fva + 1):
            b = rd(start, 24)
            if b is None:
                continue
            done = False
            for ins in md.disasm(b, start):
                if ins.address + ins.size == fva + 4:
                    out.append((ins.address, ins.mnemonic + " " + ins.op_str, ins.bytes.hex()))
                    done = True
                    break
                if ins.address + ins.size > fva + 4:
                    break
            if done:
                break
        o = k + 1
    return sorted(set(out))


def containing_fn(site):
    ent = None
    for a in load_atlas():
        if a <= site and (ent is None or a > ent):
            ent = a
    return ent


def is_deleting_dtor(fn):
    """删除析构器特征：test byte ptr [esp+X],1 + call 0x7C8B3D + ret 4。"""
    if fn is None:
        return False, ""
    ins, sz = body(fn)
    if not ins:
        return False, ""
    has_test = False
    has_free = False
    has_ret4 = False
    for i in ins:
        t = i.mnemonic + " " + i.op_str
        if i.mnemonic == "test" and "byte ptr [esp" in i.op_str and ", 1" in i.op_str:
            has_test = True
        if i.mnemonic == "call" and i.op_str == "0x7c8b3d":
            has_free = True
        if i.mnemonic == "ret" and "4" in i.op_str:
            has_ret4 = True
    ok = has_test and has_free and has_ret4
    return ok, "test字节:%s free:%s ret4:%s" % (has_test, has_free, has_ret4)


def atexit_registered(fn):
    """是否被 push <fn>; call 0x7C978A 注册（atexit 全局析构器）。"""
    if fn is None:
        return False, ""
    for site, mn in build_call_index()["idx"].get(fn, []):
        pass
    # 直接找 push imm32==fn 后紧跟 call 0x7c978a
    pat = struct.pack("<I", fn)
    o = TEXT_RAW
    end = TEXT_RAW + TEXT_RS
    while True:
        k = data.find(pat, o, end)
        if k < 0:
            break
        fva = TEXT_LO + (k - TEXT_RAW)
        nxt = rd(fva + 4, 5)
        if nxt and nxt[0] == 0xE8:
            rel = struct.unpack("<i", nxt[1:5])[0]
            if (fva + 9 + rel) == 0x7C978A:
                return True, "push 0x%08X @0x%08X; call 0x7C978A" % (fn, fva - 1)
        o = k + 1
    return False, ""


def rings(e, pick=None):
    """第 3 步：③（③b② 语义合同）与 ④（活虚表派发 / 真实调用者，㉓）。"""
    ins, sz = body(e)
    res = {"e": e, "size": sz, "ring3b": "未判", "ring3b_reason": "",
           "ring4": "未判", "ring4_reason": "", "lines": []}
    L = res["lines"]
    if ins is None:
        res["ring3b_reason"] = "atlas 无 size，未反汇编"
        res["ring4_reason"] = "atlas 无 size，未反汇编"
        return res
    L.append("body [0x%08X, +0x%X) insn=%d" % (e, sz, len(ins)))

    imms, jccs = [], []
    for i in ins:
        t = i.mnemonic + " " + i.op_str
        if i.mnemonic in ("mov", "or", "and", "xor", "add", "sub") and i.op_str.startswith("eax, "):
            imms.append((i.address, t))
        if i.mnemonic.startswith("j") and i.mnemonic != "jmp" and i.op_str.startswith("0x"):
            jccs.append((i.address, t))
    neg1 = [x for x in imms if x[1].split(", ")[-1] in ("0xffffffff", "-1")]
    signed_range = [x for x in jccs if x[1].split()[0] in ("jl", "jle", "jg", "jge", "js", "jns")]
    L.append("eax 常量写 %d 处；其中 -1: %d 处 %s"
             % (len(imms), len(neg1), [hex(a) for a, _ in neg1][:6]))
    L.append("有符号范围跳转(jl/jg/js/...): %d 处 %s"
             % (len(signed_range), [x[1] for x in signed_range][:8]))
    L.append("ret 数: %d" % len([i for i in ins if i.mnemonic == "ret"]))

    if neg1 or signed_range:
        res["ring3b"] = "候选"
        res["ring3b_reason"] = "多值状态码候选：%d 处 -1 返回 / %d 处有符号范围跳转" % (
            len(neg1), len(signed_range))
    else:
        res["ring3b"] = "候选弱"
        res["ring3b_reason"] = "未见 -1 返回，也未见有符号范围跳转（疑 {0,1} 布尔形态）"

    ci = build_call_index()
    sites = ci["idx"].get(e, [])
    calls = [s for s in sites if s[1] == "call"]
    jmps = [s for s in sites if s[1] == "jmp"]
    L.append("全 .text 扫描 %d 条指令；call→本 entry %d 处，jmp→ %d 处"
             % (ci["n_insn"], len(calls), len(jmps)))
    for a, mn in calls[:8]:
        L.append("   caller %08X %s" % (a, mn))

    if pick and pick.get("vt"):
        vt = pick["vt"]
        writes = insn_sites_of_table(vt)
        L.append("表 0x%08X 的 .text 写点: %d 处" % (vt, len(writes)))
        live = []
        for a, txt, bx in writes:
            fn = containing_fn(a)
            dtor, dwhy = is_deleting_dtor(fn)
            ax, awhy = atexit_registered(fn)
            kind = "删除析构器" if dtor else ("atexit 全局析构" if ax else "其它(构造器侧)")
            L.append("   write %08X in fn %s [%s] %-34s %s"
                     % (a, hexs(fn), kind, txt, (dwhy if dtor else awhy)))
            if not dtor and not ax:
                live.append((a, fn))
        res["live_writes"] = live
        L.append("排除 ㉓ 两类后剩活写点: %d %s" % (len(live), [hex(a) for a, _ in live]))

    if calls:
        # ④ 独立性：调用者若本身就是 ② 所用的那张表的槽值（即转发行桩），
        # 则该 call 与 ② 出自同一条「槽 → 实现」事实 ⇒ 按 §12.3 不算独立。
        same = []
        indep = []
        for a, mn in calls:
            occ = raw_slot_occurrences(a)
            hit = [o for o in occ if pick and o["vt"] == pick.get("vt") and o["slot_no"] == pick.get("slot")]
            (same if hit else indep).append(a)
        if indep:
            res["ring4"] = "成立"
            res["ring4_reason"] = "真实调用者 %d 处（非槽值站点，与 ② 不同源）：%s" % (
                len(indep), ", ".join("%08X" % a for a in indep[:5]))
        else:
            res["ring4"] = "仅同源虚表槽"
            res["ring4_reason"] = ("唯一调用者 %s 本身就是 ② 那张表 slot%d 的槽值（转发桩）⇒ 与 ② 同源，"
                                   "按 §12.3 不独立成立" % (", ".join("%08X" % a for a in same[:3]),
                                                        pick["slot"] if pick else -1))
    elif res.get("live_writes"):
        res["ring4"] = "仅同源虚表槽"
        res["ring4_reason"] = ("无直 call；表 0x%08X 有活写点 %s，但该槽即 ② 的槽 ⇒ ④② 同源，"
                               "按 §12.3 不独立" % (pick["vt"], [hex(a) for a, _ in res["live_writes"][:3]]))
    else:
        res["ring4"] = "无"
        res["ring4_reason"] = "无直 call，且该表无活写点（或写点全落在 ㉓ 排除类）"
    return res


def sweep():
    """12 行逐行判 ②（② 成立者顺手判 ③④），每判完一行立刻落盘 probe.tsv + EVIDENCE。"""
    un, picks = sample12()
    build_vt_inventory(verbose=False)
    hdr = ["entry", "vt_count", "vt_addr", "slot_no", "col_offset", "class_name",
           "is_main_table", "ring2", "ring3b", "ring4", "verdict", "reason"]
    ok = bad = 0
    with open(os.path.join(OUT, "probe.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(hdr)
        f.flush()
        for pos, r in picks:
            e = int(r["entry"], 16)
            v = row(e)
            lines, ring3b, ring4 = [], "—", "—"
            r3r = r4r = ""
            if v["verdict"].startswith("成立"):
                ok += 1
                rr = rings(e, v)
                print("\n".join(rr["lines"]))
                ring3b, ring4 = rr["ring3b"], rr["ring4"]
                r3r, r4r = rr["ring3b_reason"], rr["ring4_reason"]
                lines = rr["lines"]
            else:
                bad += 1
            w.writerow(["%08X" % e, v["vt_count"],
                        "%08X" % v["vt"] if v["vt"] else "",
                        v["slot"] if v["slot"] is not None else "",
                        v["off"] if v["off"] is not None else "",
                        v["class_name"],
                        "1" if v.get("off") == 0 else ("0" if v.get("off") is not None else ""),
                        v["verdict"], ring3b, ring4, v["verdict"],
                        v["reason"] + (" | ③:%s" % r3r if r3r else "") + (" | ④:%s" % r4r if r4r else "")])
            f.flush()
            ep = os.path.join(EV, "ROW_%08X.txt" % e)
            with open(ep, "w", encoding="utf-8") as g:
                g.write("entry 0x%08X  pos %d/%d  subsystem %s  grade %s  size %s\n"
                        % (e, pos + 1, len(un), r["subsystem"], r["grade"], r["size"]))
                g.write("池=%d  抽样规则: pos1 + posN + 内部 10 等分点 floor(k*(n-3)/11)\n\n" % len(un))
                g.write("--- ② 原始 dd<entry> 出现点 ---\n")
                if not v["occ"]:
                    g.write("0 个（不在任何虚表槽）\n")
                for o in v["occ"]:
                    g.write("slot 0x%08X @%s table_start=%s slot_no=%s rtti=%s\n"
                            % (o["slot"], o["sec"], hexs(o["vt"]), o["slot_no"],
                               o["name"] or ("FAIL:" + str(o["fail"]))))
                    if o["name"]:
                        g.write("    COL=0x%08X sig=%d off=%d td=0x%08X name=%s\n"
                                % (o["col"], o["sig"], o["off"], o["td"], o["name"]))
                if lines:
                    g.write("\n--- ③④ ---\n" + "\n".join(lines) + "\n")
            print("  >> 落盘 %s : ②=%s ③=%s ④=%s\n" % (
                os.path.basename(ep), v["verdict"], ring3b, ring4))
    print("\n汇总: ② 成立 %d / 不成立 %d" % (ok, bad))
    return ok, bad


def build_dd_index():
    """把 .rdata/.data 里所有「值落在 .text 的 dd」建成 value → [addr] 索引。
    这是**不依赖 RTTI** 的原始层：即使某张表 RTTI 链断了，它的槽也不会漏。"""
    idx = {}
    for secname in (".rdata", ".data"):
        if secname not in SEC:
            continue
        sva, svs, sraw, srs = SEC[secname]
        lo = max(sva, IB)
        hi = min(sva + max(svs, srs), IB + SOI)
        a = lo if lo % 4 == 0 else lo + (4 - lo % 4)
        while a + 4 <= hi:
            v = u32(a)
            if v is not None and in_text(v):
                idx.setdefault(v, []).append(a)
            a += 4
    return idx


def classify_occurrence(sa):
    """把一个 dd 出现点归到四桶之一。"""
    start = sa
    while start - 4 >= IB:
        v = u32(start - 4)
        if v is None or not in_text(v):
            break
        start -= 4
    slot_no = (sa - start) // 4
    colv = u32(start - 4)
    if not colv:
        return {"bucket": "非虚表dd", "vt": start, "slot_no": slot_no,
                "step": "表头 -4 处为零/不可读，整段不是 RTTI 虚表", "name": None}
    d, diag = col_of_vt(start)
    if d is None:
        step = diag.get("fail", "?")
        if "sig" in step or "不是可解指针" in step or "COL 20B" in step:
            return {"bucket": "非虚表dd", "vt": start, "slot_no": slot_no,
                    "step": step, "name": None}
        return {"bucket": "虚表槽但RTTI断", "vt": start, "slot_no": slot_no,
                "step": step, "name": None,
                "col": diag.get("col"), "sig": diag.get("sig")}
    return {"bucket": "成立", "vt": start, "slot_no": slot_no, "step": "",
            "name": d["name"], "col": d["col"], "sig": d["sig"], "off": d["off"],
            "td": d["td"]}


def poolstats():
    """全池（无名 1,181 / 具名 552）四桶分类 —— 用于回答第 3 问的基础率。"""
    dd = build_dd_index()
    print("原始 dd 索引: 不同值 %d" % len(dd))
    rows = list(csv.DictReader(open(HITS, encoding="utf-8"), delimiter="\t"))
    groups = {
        "unnamed": [r for r in rows if r["p3b2_named"] == "False" and r["name"].startswith("sub_")],
        "named": [r for r in rows if r["p3b2_named"] == "True"],
    }
    out = []
    for gname, g in groups.items():
        st = {"成立": 0, "成立(经stub)": 0, "虚表槽但RTTI断": 0, "非虚表dd": 0, "无dd出现": 0}
        steps = {}
        detail = []
        for r in g:
            e = int(r["entry"], 16)
            occs = dd.get(e, [])
            if not occs:
                sf = stub_forward(e)
                if sf:
                    st["成立(经stub)"] += 1
                    s = sf[0]
                    detail.append(("%08X" % e, gname, "成立(经stub)", "%08X" % s["vt"],
                                   s["slot"], "%s [%s via stub %08X]" % (s["cls"], s["kind"], s["stub"])))
                    continue
                st["无dd出现"] += 1
                detail.append(("%08X" % e, gname, "无dd出现", "", "", ""))
                continue
            cls = [classify_occurrence(a) for a in occs]
            best = None
            for c in cls:
                if c["bucket"] == "成立":
                    best = c
                    break
            if best:
                b = "成立"
            elif any(c["bucket"] == "虚表槽但RTTI断" for c in cls):
                b = "虚表槽但RTTI断"
            else:
                b = "非虚表dd"
            st[b] += 1
            if b == "虚表槽但RTTI断":
                s = [c["step"] for c in cls if c["bucket"] == "虚表槽但RTTI断"][0]
                steps[s] = steps.get(s, 0) + 1
            detail.append(("%08X" % e, gname, b,
                           "%08X" % (best or cls[0])["vt"],
                           (best or cls[0])["slot_no"],
                           (best or {}).get("name") or (cls[0].get("step") or "")))
        out.append((gname, len(g), st, steps, detail))
        print("\n[%s] n=%d" % (gname, len(g)))
        for k, v in st.items():
            print("   %-14s %5d  (%.2f%%)" % (k, v, 100.0 * v / len(g)))
        if steps:
            for k, v in sorted(steps.items(), key=lambda x: -x[1]):
                print("   断因: %-40s %d" % (k, v))
    # 落盘
    p = os.path.join(OUT, "pool_stats.tsv")
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["entry", "group", "bucket", "vt_addr", "slot_no", "class_name_or_break_step"])
        for gname, n, st, steps, detail in out:
            for row in detail:
                w.writerow(row)
    # 无名池里 8 行"成立"的明细单列
    p2 = os.path.join(OUT, "unnamed_ring2_hits.tsv")
    with open(p2, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["entry", "subsystem", "grade", "size", "vt_addr", "slot_no", "col_offset", "class_name"])
        un = {r["entry"]: r for r in groups["unnamed"]}
        for gname, n, st, steps, detail in out:
            if gname != "unnamed":
                continue
            for e, gg, b, vt, slot, name in detail:
                if b == "成立":
                    r = un[e]
                    c = classify_occurrence(dd[int(e, 16)][0])
                    w.writerow([e, r["subsystem"], r["grade"], r["size"], vt, slot,
                                c.get("off", ""), name])
    print("\n落盘 pool_stats.tsv / unnamed_ring2_hits.tsv")
    return out


if __name__ == "__main__":
    main()
