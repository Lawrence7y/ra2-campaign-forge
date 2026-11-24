# -*- coding: utf-8 -*-
"""F2V-05: ⑥ 盘符剥后缀 ⑦ 引文降级反例 + 对抗性探针（尾括注偶然反引号路径）。
全部端到端走 r11_scan_plus，对象为真实在盘 fixture；错 hash 用另一 fixture 的真 hash。"""
import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "r11_f2_fix_20261109"
FX = W / "_f2v_fixtures"

spec = importlib.util.spec_from_file_location("_f2p", W / "_f2_r11plus.py")
plus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plus)

obj = FX / "_f2v_obj.txt"
oth = FX / "_f2v_other.txt"
sha_obj = hashlib.sha256(obj.read_bytes()).hexdigest()
sha_oth = hashlib.sha256(oth.read_bytes()).hexdigest()
nb_obj = len(obj.read_bytes())
print("obj sha=%s bytes=%d" % (sha_obj, nb_obj))
print("other sha=%s" % sha_oth)

print("\n===== ⑥ strip_line_suffixes 盘符/行号后缀 =====")
cases = [
    r"C:\path:18", r"C:\x", r"C:", "C:\\", r"C:\Users\a\f.md:18-19",
    r"f.md:L18", "f.md#L18", "f.md:L18-L19", "f.md:962/:963/:965",
    "f.md", "plain.md", "f.md:18:19", "http://h/x.md:5", "12:30",
]
for c in cases:
    print("%-28r -> %r" % (c, plus.strip_line_suffixes(c)))

print("\n===== ⑥b 端到端：真对象+行号后缀（原版会 R3-3c 误报的形态）=====")
doc = ("绑定测试：被核对象 SHA256 = %s，字节数 = %d（`_f2v_obj.txt:10-20`）\n" % (sha_obj, nb_obj))
p, w, b = plus.r11_scan_plus(doc, FX, root=REPO)
print("problems=%r warnings=%r" % (p, w))
print("rec: tier=%r match=%r suffix_stripped=%r used=%r" % (
    b[0].get("tier"), b[0].get("match"), b[0].get("suffix_stripped"), b[0].get("used_variant")))

print("\n===== ⑥c 端到端：不存在盘符路径 :5-6 —— 报错消息应含完整路径而非 'C' =====")
doc2 = "被核对象 SHA256 = %s，字节数 = 3（`C:\\no\\such_dir\\missing.md:5-6`）\n" % sha_oth
p2, w2, b2 = plus.r11_scan_plus(doc2, FX, root=REPO)
print("problems=%r" % p2)

print("\n===== ⑦ 引文语境反例（对象在盘、声明 hash 为错值 → 基线必须 FAIL）=====")
def case(name, doc):
    p, w, b = plus.r11_scan_plus(doc, FX, root=REPO)
    verdict = "FAIL" if p else "PASS"
    print("[%-34s] verdict=%s problems=%d warnings=%d first_problem=%r" % (
        name, verdict, len(p), len(w), (p or w or [""])[0][:90]))
    return p, w

BAD = sha_oth  # 真 hash 但属于另一文件 → 对 _f2v_obj.txt 而言是失配
# a. 对照组：无标记（T1 路径在分隔段）
case("a 无标记(T1)", "被核对象 `_f2v_obj.txt` SHA256 = %s，字节数 = 26\n" % BAD)
# b/c/d. 伪标记
case("b 引：", "引：被核对象 `_f2v_obj.txt` SHA256 = %s，字节数 = 26\n" % BAD)
case("c 引用锚已修复：", "引用锚已修复：被核对象 `_f2v_obj.txt` SHA256 = %s\n" % BAD)
case("d 引述待核：", "引述待核：被核对象 `_f2v_obj.txt` SHA256 = %s\n" % BAD)
# e. 标记距命中点 >24 字符
case("e 标记>24字符", "本段为引文，前导说明共超过二十四个字符的冗长铺垫之后才出现被核对象 `_f2v_obj.txt` SHA256 = %s\n" % BAD)
# f. 标记仅在前一行
case("f 标记仅前一行", "（引文）\n被核对象 `_f2v_obj.txt` SHA256 = %s\n" % BAD)
# g. ★本件自身断言+窗内标记（被核反例）
case("g 自身断言+窗内「引文」", "本件自证引文对照：被核对象 `_f2v_obj.txt` SHA256 = %s\n" % BAD)
case("g2 自身断言+「本轮实读」", "本轮实读后本件郑重断言：被核对象 `_f2v_obj.txt` SHA256 = %s\n" % BAD)
# h. 真引文（规范标记）
case("h 真引文「原文照录」", "原文照录：被核对象 `_f2v_obj.txt` SHA256 = %s\n" % BAD)

print("\n===== ⑦b 对照：自身断言+窗内标记 但 hash 正确 → 两版都应 PASS（无误报）=====")
case("g3 正确hash+窗内「引文」", "本件自证引文对照：被核对象 `_f2v_obj.txt` SHA256 = %s，字节数 = %d\n" % (sha_obj, nb_obj))

print("\n===== ⑧ 探针：无 T1 + 尾括注偶然反引号路径（他文件在盘）→ 潜在新误报形态 =====")
# 绑定对象 hash 正确（真对象 _f2v_other.txt），但对象路径不出现；尾括注偶然反引号引用 _f2v_obj.txt
doc3 = "被核对象 SHA256 = %s，字节数 = 26（详见同域另一物 `_f2v_obj.txt`）\n" % sha_oth
p3, w3, b3 = plus.r11_scan_plus(doc3, FX, root=REPO)
print("plus problems=%r warnings=%r" % (p3, w3))
print("orig(r11_scan) 同文本对照：")
import importlib.util as iu
s2 = iu.spec_from_file_location("_g7x", REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py")
g7 = iu.module_from_spec(s2); s2.loader.exec_module(g7)
op, ow, ob = g7.r11_scan(doc3, FX, root=REPO)
print("orig problems=%r warnings=%r" % (op, ow))
