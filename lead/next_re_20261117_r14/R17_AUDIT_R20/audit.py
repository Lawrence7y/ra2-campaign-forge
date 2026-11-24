#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# R17_AUDIT_R20 / audit.py  —— 独立复核实现（不复用、不 import 执行方 work.py）
# 只读输入：gamemd.exe（只取 PE 节表 + .rdata/.data 原始字节）、COVERAGE/coverage.tsv
# 只写本目录 audit_out.json
import hashlib, json, pathlib, re, struct

IMG = pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
COVERAGE = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
OUT = pathlib.Path(__file__).resolve().parent

def u16(buf, o):
    return struct.unpack_from("<H", buf, o)[0]


def u32(buf, o):
    return struct.unpack_from("<I", buf, o)[0]
CLASS_RE = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*Class(?![A-Za-z0-9_])")

def main():
    b = IMG.read_bytes()
    sha = hashlib.sha256(b).hexdigest().upper()
    pe = u32(b, 0x3C); nsec = u16(b, pe + 6); optsz = u16(b, pe + 20); opt = pe + 24
    image_base = u32(b, opt + 28)
    secs = {}
    for i in range(nsec):
        s = opt + optsz + i * 40
        nm = b[s:s+8].rstrip(b"\0").decode("latin1")
        vs, va, rs, rp = struct.unpack_from("<IIII", b, s + 8)
        secs[nm] = {"va": va, "rs": rs, "rp": rp, "vaLo": image_base + va}
    TD_VF = 0x7F9594   # TypeDescriptor vftable，取自 _stage1_rtti.json 首条 TD 的 vfptr，非执行方脚本
    rtti = []
    for nm in (".rdata", ".data"):
        sc = secs[nm]; end = sc["rp"] + sc["rs"]; o = sc["rp"]
        while o + 12 <= end:
            if u32(b, o) == TD_VF and u32(b, o + 4) == 0 and b[o+8:o+10] == b".?":
                p = o + 8
                while p < end and b[p] != 0:
                    p += 1
                dec = b[o+8:p].decode("latin1")
                if 4 <= len(dec) <= 512 and re.fullmatch(r"\.\?A[VUW][\x20-\x7e]*", dec):
                    rtti.append({"dec": dec, "va": sc["vaLo"] + (o - sc["rp"])})
                o = p + 1
                while o % 4:
                    o += 1
                continue
            o += 4
    bares = [e["dec"][4:-2] if e["dec"].endswith("@@") else e["dec"][4:] for e in rtti]
    for e, x in zip(rtti, bares):
        e["bare"] = x
    exact = {}
    for x in bares:
        exact.setdefault(x.lower(), x)
    tmpl = {}
    for x in bares:
        if x.startswith("?$") and "@" in x:
            tmpl.setdefault(x[2:].split("@")[0].lower(), []).append(x)

    cb = COVERAGE.read_bytes()
    cov_sha = hashlib.sha256(cb).hexdigest().upper()
    lines = cb.decode("utf-8").splitlines()
    counts = {}
    for line in lines[1:]:
        if not line:
            continue
        col = line.split("\t")
        for t in dict.fromkeys(CLASS_RE.findall(col[3] if len(col) > 3 else "")):
            counts[t] = counts.get(t, 0) + 1
    toks = list(counts)

    def strip_prefix(s):
        return [s[n:] for n in range(1, min(4, len(s) - 1) + 1) if all(c in "PAV" for c in s[:n])]

    def resolve(t):
        if t.lower() in exact:
            return t, "exact"
        cands = [(x, "prefix") for x in strip_prefix(t)]
        segs = [s for s in t.split("_") if s]
        cands += [(s, "underscore") for s in segs]
        for s in segs:
            cands += [(x, "underscore") for x in strip_prefix(s)]
        for x, mech in cands:
            if x.lower() in exact:
                return x, mech
        if t.lower() in tmpl:
            return t, "template_base"
        return None, None

    res = {}
    for t in toks:
        k, mech = resolve(t)
        if k:
            res[t] = (k, mech)
    unresolved = [t for t in toks if t not in res]

    # RTTI 侧：每个 in-binary 裸名由哪条机制覆盖
    def rtti_cover(bare):
        bl = bare.lower()
        if bl.startswith("?$") and "@" in bl:
            base = bl[2:].split("@")[0]
            if base in {t.lower() for t in toks}:
                return "template_base"
            return None
        if bl in exact and any(t.lower() == bl for t in toks):
            return "direct"
        return None
    covered = [e for e in rtti if rtti_cover(e["bare"])]
    tmpl_covered = [e for e in covered if rtti_cover(e["bare"]) == "template_base"]
    # note: template_base 396 = VectorClass 200 + DynamicVectorClass 196，二者都是 coverage token 本身
    rtti_only = [e for e in rtti if not rtti_cover(e["bare"])]

    # 全镜像 ASCII 出现次数（用来看"名字是否在镜像里出现过"）
    blob = b.decode("latin1")
    appear = {t: blob.count(t) for t in unresolved}

    out = {
        "image": str(IMG), "sha256": sha, "size": len(b),
        "sections": secs,
        "rttiEntries": len(rtti), "rttiUniqueBare": len(exact), "templateInstances": len(tmpl),
        "coverageRows": len(lines) - 1, "distinctTokens": len(toks),
        "tokenOccurrences": sum(counts.values()),
        "coverageSha256": cov_sha,
        "both": len(res), "coverageOnly": len(unresolved),
        "mechanism": {m: sum(1 for v in res.values() if v[1] == m) for m in ("exact", "prefix", "underscore", "template_base")},
        "underscoreDetail": sorted(t for t, v in res.items() if v[1] == "underscore"),
        "unresolved": sorted(unresolved),
        "unresolvedOccurrences": sum(counts[t] for t in unresolved),
        "rttiCovered": len(covered), "rttiTemplateBaseCovered": len(tmpl_covered),
        "rttiOnly": len(rtti_only),
        "rawAppearancesInImage": appear,
    }
    (OUT / "audit_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("sha256", "rttiEntries", "distinctTokens", "both", "coverageOnly", "mechanism", "rttiCovered", "rttiTemplateBaseCovered", "rttiOnly", "unresolvedOccurrences")}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
