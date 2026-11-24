# -*- coding: utf-8 -*-
"""_civ_structural.py — 独立检验 §1(c)「match is True ⟺ path 真值 是控制流结构性后果」。

做法：在临时目录里放一个真实小文件，用合成绑定行（声明 hash 故意错）调用现盘
r11_scan_plus（纯函数，零真机、零采样代码、只读），观察 (path, match) 组合。
"""
import hashlib
import importlib.util
import json
import pathlib
import tempfile

REPO = pathlib.Path(r"D:\Project\ra2-campaign-forge")
PLUS = REPO / "lead" / "r11_f2_fix_20261109" / "_f2_r11plus.py"
spec = importlib.util.spec_from_file_location("_civ_plus", PLUS)
f2p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f2p)

tmp = pathlib.Path(tempfile.mkdtemp(prefix="_civ_struct_"))
(tmp / "probe.txt").write_bytes(b"hello")
real_sha = hashlib.sha256(b"hello").hexdigest()
wrong = "0" * 64
print("TEMP:", tmp, " real sha:", real_sha, " declared:", wrong)

# 绑定行格式：BIND_RE 要求「被核对象…SHA256 = 64hex」；分隔段内反引号路径 => T1 path
line = "被核对象 `probe.txt` SHA256 = %s，字节数 = 5" % wrong
print("LINE:", line)
problems, warnings, bindings = f2p.r11_scan_plus(line, tmp, root=tmp)
print("problems =", problems)
print("warnings =", warnings)
b = bindings[0]
print("binding =", json.dumps({k: v for k, v in b.items() if k != "tried"},
                             ensure_ascii=False, default=str))
print()
print("path truthy      =", bool(b.get("path")))
print("match is True    =", b.get("match") is True)
print("match value      =", b.get("match"))
print("tier             =", b.get("tier"))
print()
print("==> (path 真值, match=False) 在【现版本 r11_scan_plus】里可达 =",
      bool(b.get("path")) and b.get("match") is False)
print("==> 若把这条塞进 results[]：plus_path=1, plus_match=0 ⇒ plus_path > plus_match")
print("==> §1(c)『match is True ⟺ path 真值是控制流结构性后果』是否成立 =",
      (b.get("match") is True) == bool(b.get("path")))
