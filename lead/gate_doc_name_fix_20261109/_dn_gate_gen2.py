# -*- coding: utf-8 -*-
"""Gen-2 缺陷门禁复刻（对照用）：DOC=max(cands,key=st_size) 猜被核对象。
检查项与方案 A 完全一致，唯一差别 = 被核对象怎么选。
用法: python -I -X utf8 _dn_gate_gen2.py <写域绝对路径>"""
import json, re, sys, hashlib
from pathlib import Path

SECTIONS = ["## 1", "## 2", "## 3"]
ELEMENTS = ["未验"]
BANNED = ["已改台账"]
BINDING_RE = re.compile(r"被核对象 SHA256 = [0-9a-fA-F]{64}")

def main():
    wd = Path(sys.argv[1])
    P = []
    NB = 0
    SHA = "MISSING"
    B = 0
    doc = None
    cands = sorted(wd.glob("*.md")) if wd.is_dir() else []
    if not cands:
        P.append("写域内无 md 交付件")
    else:
        doc = max(cands, key=lambda p: p.stat().st_size)  # ← 缺陷行
        raw = doc.read_bytes()
        NB = len(raw)
        SHA = hashlib.sha256(raw).hexdigest()
        t = raw.decode("utf-8", errors="replace")
        for s in SECTIONS:
            if s not in t:
                P.append("缺小节 " + s)
        for k in ELEMENTS:
            if k not in t:
                P.append("缺要素 " + k)
        for bad in BANNED:
            if bad in t:
                P.append("含越界断言 " + bad)
        B = len(BINDING_RE.findall(t))
        if B < 1:
            P.append("缺规范格式绑定行")
    print(json.dumps({
        "ok": not P, "problems": P,
        "doc": (doc.name if doc else "(none)"),
        "docBytes": NB, "docSha256": SHA, "bindings": B,
    }, ensure_ascii=False))

main()
