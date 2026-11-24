# -*- coding: utf-8 -*-
"""方案 A 门禁标准形态（可执行版）。payload 内嵌时把 argv 两参换成字面量：
   DOC=wd/'<主件名>.md'
用法: python -I -X utf8 _dn_gate_planA.py <写域绝对路径> <主件文件名>
输出: 单行 JSON {ok, problems, doc, docBytes, docSha256, bindings}
要点: 显式命名 / 缺失即 FAIL / 门禁瞬间指纹发射（防 TOCTOU）/ 严格绑定行正则。"""
import json, re, sys, hashlib
from pathlib import Path

SECTIONS = ["## 1", "## 2", "## 3"]
ELEMENTS = ["未验"]
BANNED = ["已改台账"]
BINDING_RE = re.compile(r"被核对象 SHA256 = [0-9a-fA-F]{64}")

def main():
    wd = Path(sys.argv[1])
    name = sys.argv[2]
    DOC = wd / name
    P = []
    NB = 0
    SHA = "MISSING"
    B = 0
    if not DOC.is_file():
        P.append("主件缺失 " + name + "（写域=" + wd.name + "）")
    else:
        raw = DOC.read_bytes()
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
        "doc": name, "docBytes": NB, "docSha256": SHA, "bindings": B,
    }, ensure_ascii=False))

main()
