#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# R17-AUDIT-R22 / audit.py  —— 独立实现（不 import、不调用执行方 work.py）
# 只读：gamemd.exe 的 .rdata/.data/.text（按节表），coverage.tsv（只读一次）。产物只写本目录。
import hashlib, json, pathlib, re, struct, sys

IMG = pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
COV = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
CORR = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R22_RING2_CORROB\corroborated.tsv")
OUT = pathlib.Path(__file__).resolve().parent
IMAGE_BASE = 0x400000
TD_VFPTR = 0x7F9594          # ??_7type_info@@6B@
EXPECT_SHA_PREFIX = "73201CC0"

RE_CLASS = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*Class(?![A-Za-z0-9_])")
MSVC_PREFIX = ("PAV", "AV", "PA", "P", "A")
RE_TPL_BASE = re.compile(r"^\?\$([A-Za-z_][A-Za-z0-9_]*)")
# A4：执行方判据（照抄其语义，仅用于复现/比对）
EXE_AUDIT = re.compile(r"VERDICT|verdict\.tsv|_audit|AUDIT|审计|独立|④|活表槽位见证|\bRTTI\b|rtti-vftable|\bvt\s*=|vtable|虚表槽|"
                       r"\bvt\b|slot\s*\d+|槽\s*\d+|PROOF|PROOF_SIX|VERIFY|CHAIN|链", re.I)
EXE_YRPP = re.compile(r"YRpp\s*(named|kb|地址名)|YRpp/kb|名字已证，语义据名", re.I)

def u32(b, o):
    if o is None or o < 0 or o + 4 > len(b):
        return None
    return struct.unpack_from("<I", b, o)[0]

def parse_pe(b):
    e = u32(b, 0x3C); nsec = struct.unpack_from("<H", b, e + 6)[0]
    optsz = struct.unpack_from("<H", b, e + 20)[0]; opt = e + 24
    assert u32(b, opt + 28) == IMAGE_BASE
    secs = {}
    for i in range(nsec):
        s = opt + optsz + i * 40
        name = b[s:s+8].rstrip(b"\0").decode("latin1")
        vs, va, rs, rp = struct.unpack_from("<IIII", b, s + 8)
        secs[name] = dict(vs=vs, va=va, rs=rs, rp=rp, lo=IMAGE_BASE + va)
    return secs

def main():
    b = IMG.read_bytes()
    sha = hashlib.sha256(b).hexdigest().upper()
    assert sha.startswith(EXPECT_SHA_PREFIX), ("image sha mismatch", sha)
    secs = parse_pe(b)
    def off(va):
        for s in secs.values():
            r = va - IMAGE_BASE - s["va"]
            if 0 <= r < s["rs"]:
                return s["rp"] + r
        return None
    rd = lambda va: u32(b, off(va))
    tx = secs[".text"]
    in_text = lambda va: tx["lo"] <= va < tx["lo"] + tx["vs"]

    # ---- 1) TypeDescriptor 扫描（.rdata/.data）----
    tds, scan_bytes = {}, 0
    for sn in (".rdata", ".data"):
        s = secs[sn]; scan_bytes += s["rs"]
        o, end = s["rp"], s["rp"] + s["rs"]
        while o + 12 <= end:
            if u32(b, o) == TD_VFPTR and u32(b, o + 4) == 0 and b[o+8:o+10] == b".?":
                p = o + 8
                while p < end and b[p]: p += 1
                raw = b[o+8:p].decode("latin1", "replace")
                if 4 <= len(raw) <= 512 and all(0x20 <= ord(c) <= 0x7E for c in raw):
                    bare = raw
                    for pf in (".?AV", ".?AU", ".?AW"):
                        if bare.startswith(pf): bare = bare[len(pf):]; break
                    if bare.endswith("@@"): bare = bare[:-2]
                    tds[IMAGE_BASE + s["va"] + (o - s["rp"])] = bare
                    o = p + 1
                    while o % 4: o += 1
                    continue
            o += 4

    # ---- 2) COL（RTTI Complete Object Locator），只在 .rdata ----
    cols, rs = {}, secs[".rdata"]
    for o in range(rs["rp"], rs["rp"] + rs["rs"] - 19, 4):
        if u32(b, o) == 0 and u32(b, o + 4) in (0, 4, 8, 12) and u32(b, o + 8) == 0 and u32(b, o + 12) in tds:
            cols[IMAGE_BASE + rs["va"] + (o - rs["rp"])] = tds[u32(b, o + 12)]

    # ---- 3) vtable = COL 指针 + 4，持续到下一处 COL 引用或 .rdata 末尾 ----
    refs = []
    for sn in (".rdata", ".data"):
        s = secs[sn]
        for o in range(s["rp"], s["rp"] + s["rs"] - 3, 4):
            if u32(b, o) in cols: refs.append(IMAGE_BASE + s["va"] + (o - s["rp"]))
    refs.sort()
    vts = []
    for i, r in enumerate(refs):
        base = r + 4
        end = refs[i + 1] if i + 1 < len(refs) else rs["lo"] + rs["rs"]
        slots, va = [], base
        while va + 3 < end:
            v = rd(va)
            if v is None or not in_text(v): break
            slots.append(v); va += 4
        vts.append(dict(base=base, bare=cols[paddr(refs[i])] if False else None, slots=slots, colref=r))
    byref = {v["colref"]: v for v in vts}
    for r in refs:
        # COL va = 指针所指；用 u32 读回
        pass
    for v in vts:
        cva = u32(b, off(v["colref"]))
        v["bare"] = cols[cva]

    # ---- 4) 类键索引（裸名 + 模板基名别名）----
    def keys_of(bare, alias):
        k = [bare]
        if alias:
            m = RE_TPL_BASE.match(bare)
            if m: k.append(m.group(1))
        return k
    def build(alias):
        cls, ent = {}, {}
        for v in vts:
            for k in keys_of(v["bare"], alias):
                cls.setdefault(k, set()).add(v["base"])
                ent.setdefault(k, set())
            for i, s in enumerate(v["slots"]):
                for k in keys_of(v["bare"], alias):
                    ent.setdefault(s, []).append(dict(cls=k, owner=v["bare"], vtable=v["base"], slot=i))
        return cls, ent
    EX, AL = build(False), build(True)

    # ---- 5) coverage 读取（只读一次，前后各取哈希）----
    cb = COV.read_bytes(); cov_before = hashlib.sha256(cb).hexdigest().upper()
    lines = cb.decode("utf-8").splitlines()
    rows = [ln.split("\t") for ln in lines[1:] if ln]
    proved = [r for r in rows if len(r) == 8 and r[4] == "[已证]"]

    def variants(raw):
        o, s, ch = [raw], raw, True
        while ch:
            ch = False
            for p in MSVC_PREFIX:
                if s.startswith(p) and len(s) > len(p):
                    s = s[len(p):]; o.append(s); ch = True; break
        return o

    def measure(idx):
        cls, ent = idx
        loc = closed = contra = contra_only = 0
        for r in proved:
            keys = []
            for raw in set(RE_CLASS.findall(r[3])):
                for cand in variants(raw):
                    if cand in cls: keys.append(cand); break
            keys = sorted(set(keys))
            if not keys: continue
            loc += 1
            own = set()
            for k in keys: own |= cls[k]
            hits = ent.get(int(r[0], 16), [])
            ownhit = any(h["vtable"] in own for h in hits)
            other = any(h["vtable"] not in own for h in hits)
            closed += ownhit; contra += other; contra_only += (other and not ownhit)
        return dict(located=loc, closed=closed, contradiction=contra, contradiction_not_closed=contra_only)
    m_alias, m_exact = measure(AL), measure(EX)

    # ---- 6) A2：继承 vs 错配 ----
    # 判据（本审计新增，执行方未实现）：若 D 的 vtable 中与 P 的 vtable 同值的那些槽，在 P 中的位置 j 都不早于在 D 中的位置 i
    # （j >= i，且 ≥3 个共同槽可判、违背 ≤1 个），则 P 是 D 的基类表（MSVC 单继承下派生类 override 只会把基类槽位的实现下移/替换，
    # 绝不会把基类方法挪到更靠前的槽位）。关系可传递（沿派生链上溯），允许双向（基类/派生类任一方向均算继承）。
    bybase = {v["base"]: v for v in vts}
    pcache = {}
    def parents(D):
        if D in pcache: return pcache[D]
        c = bybase[D]; res = []
        for p in vts:
            if p["base"] == D or len(p["slots"]) < 3 or len(p["slots"]) > len(c["slots"]) + 2: continue
            pos, both, sup, conf = {}, 0, 0, 0
            for j, s in enumerate(p["slots"]): pos.setdefault(s, []).append(j)
            for i, s in enumerate(c["slots"]):
                if s not in pos: continue
                both += 1
                if any(j >= i for j in pos[s]): sup += 1
                else: conf += 1
            if both >= 3 and sup >= 3 and conf <= 1 and sup / both >= 0.9:
                res.append(dict(p=p["base"], support=sup, both=both))
        res.sort(key=lambda x: (-x["support"], abs(len(bybase[x["p"]]["slots"]) - len(c["slots"]))))
        pcache[D] = res; return res
    def chain_to(X, Y, limit=6):
        if X == Y: return True
        frontier, seen = [X], {X}
        for _ in range(limit):
            nxt = []
            for cur in frontier:
                for p in parents(cur):
                    if p["p"] == Y: return True
                    if p["p"] not in seen: seen.add(p["p"]); nxt.append(p["p"])
            frontier = nxt
        return False
    related = lambda A, B: A == B or chain_to(A, B) or chain_to(B, A)

    out_rows, tally = [], {}
    for r in proved:
        keys = []
        for raw in set(RE_CLASS.findall(r[3])):
            for cand in variants(raw):
                if cand in AL[0]: keys.append(cand); break
        keys = sorted(set(keys))
        if not keys: continue
        own = set()
        for k in keys: own |= AL[0][k]
        entry = int(r[0], 16)
        hits = [dict(base=v["base"], bare=v["bare"], slot=i) for v in vts for i, s in enumerate(v["slots"]) if s == entry]
        ownhit = any(h["base"] in own for h in hits)
        other = [h for h in hits if h["base"] not in own]
        if not other: continue
        rel = [h for h in other if any(related(o, h["base"]) for o in own)]
        allstl = all(h["bare"].startswith("?$TClassFactory@") for h in other)
        if len(rel) == len(other): verdict = "继承可解释"
        elif allstl: verdict = "同址复用(非继承，非错配)"
        elif rel: verdict = "真正可疑"
        else: verdict = "真正可疑"
        tally[verdict] = tally.get(verdict, 0) + 1
        out_rows.append(dict(entry=r[0], row_classes=[bybase[b]["bare"] for b in sorted(own)],
                             other_classes=[h["bare"] for h in other], verdict=verdict,
                             own_closure=ownhit, n_vtable_hits=len({h["base"] for h in hits})))

    # ---- 7) A4：复现执行方的证据分类 ----
    covrow = {r[0]: r for r in rows if len(r) == 8}
    corr = [l.split("\t") for l in CORR.read_text(encoding="utf-8").splitlines() if l][1:]
    a4 = []
    for c in corr:
        sem = covrow.get(c[0], ["", "", "", "", "", "", "", ""])[3]
        aud, yr = bool(EXE_AUDIT.search(sem)), bool(EXE_YRPP.search(sem))
        mine = "有独立审计链" if aud else ("仅 YRpp 代理" if yr else "未命中→兜底")
        a4.append(dict(entry=c[0], cls=c[1], exec_label=c[4], sem=sem, audit_hit=aud, yrpp_hit=yr, mine=mine))
    a4_src = {}
    for x in a4:
        kk = "%s/%s" % (x["audit_hit"], x["yrpp_hit"])
        a4_src[kk] = a4_src.get(kk, 0) + 1
    a4_both = sum(1 for x in a4 if x["audit_hit"] and x["yrpp_hit"])

    cov_after = hashlib.sha256(COV.read_bytes()).hexdigest().upper()
    res = dict(image=str(IMG), sha256=sha, image_size=len(b), scan_bytes=scan_bytes,
               tds=len(tds), cols=len(cols), vtables=len(vts),
               slots=sum(len(v["slots"]) for v in vts),
               alias_keys=len(AL[0]), exact_keys=len(EX[0]),
               proved=len(proved), alias=m_alias, exact=m_exact,
               a2_tally=tally, a4_src=a4_src, a4_both_hit=a4_both, a4_rows=len(a4),
               cov_before=cov_before, cov_after=cov_after, cov_unmodified=cov_before == cov_after)
    (OUT / "_audit_result.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "_a4_evidence.json").write_text(json.dumps(a4, ensure_ascii=False, indent=1), encoding="utf-8")
    with (OUT / "inherit_vs_mismatch.tsv").open("w", encoding="utf-8") as f:
        f.write("entry\trow_class\tother_class\tinherited\tverdict\town_closure\tn_vtable_hits\n")
        for x in out_rows:
            f.write("%s\t%s\t%s\t%s\t%s\t%s\t%d\n" % (x["entry"], "|".join(x["row_classes"]), "|".join(x["other_classes"]),
                    "yes" if x["verdict"] == "继承可解释" else "no", x["verdict"],
                    "closed" if x["own_closure"] else "not-closed", x["n_vtable_hits"]))
    print(json.dumps({k: res[k] for k in ("sha256", "proved", "alias", "exact", "a2_tally", "a4_src", "a4_both_hit",
                                          "cov_unmodified")}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
