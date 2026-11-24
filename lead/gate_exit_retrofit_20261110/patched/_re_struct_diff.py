# -*- coding: utf-8 -*-
"""_re_struct_diff.py — 并入版结构核验：difflib 比对只读原件与并入版，断言全部差异
hunk 落在白名单（模块 docstring、link() docstring、link_triple() docstring、
DECL_RE 插入、J4 块插入、tier 三元、merged elif 插入、usage 行）。
输出落本写域 _re_struct_diff_out.json。只读 + 本写域一件输出；-B 防 __pycache__。"""
import difflib
import hashlib
import json
from pathlib import Path

SL_PY = Path(r"D:\Project\ra2-campaign-forge\lead\samedoc_link_20261109\_sl_link.py")
RE_PY = Path(r"D:\Project\ra2-campaign-forge\lead\r33e_merge_20261109\_re_linked.py")
OUT = Path(r"D:\Project\ra2-campaign-forge\lead\r33e_merge_20261109\_re_struct_diff_out.json")

b_sl = SL_PY.read_bytes()
b_re = RE_PY.read_bytes()
guard = {
    "sl_link": {"sha256": hashlib.sha256(b_sl).hexdigest(), "bytes": len(b_sl),
                "expect_sha": "a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5",
                "expect_bytes": 12475},
    "re_linked": {"sha256": hashlib.sha256(b_re).hexdigest(), "bytes": len(b_re)},
}
assert guard["sl_link"]["sha256"] == guard["sl_link"]["expect_sha"], "GUARD FAIL: original drifted"
assert guard["sl_link"]["bytes"] == guard["sl_link"]["expect_bytes"], "GUARD FAIL: original drifted"

orig_lines = b_sl.decode("utf-8").splitlines()
new_lines = b_re.decode("utf-8").splitlines()
sm = difflib.SequenceMatcher(None, orig_lines, new_lines, autojunk=False)
ops = sm.get_opcodes()
# 白名单（1-based 原件行号）：
#   replace 允许跨 (2,24)=模块 docstring；(139,141)=link() docstring；
#           (225,226)=link_triple() docstring；229=tier 三元；243=usage 行
#   insert  允许锚 48=DECL_RE 之后；210=multi 分支 warning 之后（J4 块）；236=unique rec 块之后
ALLOWED_REPLACE_SPANS = [(2, 24), (139, 141), (225, 226), (229, 229), (243, 243)]
ALLOWED_INSERT_AFTER = [48, 210, 236]
diff_hunks, struct_ok = [], True
for tag, i1, i2, j1, j2 in ops:
    if tag == "equal":
        continue
    if tag == "insert":
        ok = i1 in ALLOWED_INSERT_AFTER
        where = "after line %d" % i1
    else:
        span = (i1 + 1, i2)
        ok = any(span[0] >= a and span[1] <= b for a, b in ALLOWED_REPLACE_SPANS)
        where = "lines %d-%d" % span
    diff_hunks.append({"op": tag, "orig": where, "new": "new lines %d-%d" % (j1 + 1, j2)})
    struct_ok = struct_ok and ok
unified = "".join(difflib.unified_diff(
    [ln + "\n" for ln in orig_lines], [ln + "\n" for ln in new_lines],
    fromfile="_sl_link.py", tofile="_re_linked.py", n=1))

out = {"guard": guard, "struct_ok": struct_ok, "hunks": diff_hunks, "unified_diff": unified}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("STRUCT_OK:", struct_ok)
print("HUNKS:", json.dumps(diff_hunks, ensure_ascii=False))
print("GUARD:", guard["sl_link"]["sha256"][:12], "/", guard["sl_link"]["bytes"],
      "| RE:", guard["re_linked"]["sha256"][:12], "/", guard["re_linked"]["bytes"])
print("OUT:", OUT)
# ---------- 出口改造（纯追加：以上原件 59 行与原件逐字节一致，未改一字） ----------
# 原型：lead/dtrigger_compare_20261107/_check_dtrigger.py:31-35 + :226-228（模板形态）
# A. 原件「对自身的检查」及其结果通道（本会话实读原件全文）：
#    :23-24 两条 assert 守卫：只读原件 _sl_link.py 的 sha256 / bytes 与登记常量
#           相等（"GUARD FAIL: original drifted"）；失败即 AssertionError，stdout 无输出。
#    :36-48 结构核验：:37 逐个 diff opcode，:41 insert 锚点白名单、:45 replace
#           跨度白名单，:48 struct_ok = struct_ok and ok 合取。这是本脚本主判定
#           （EXIT_CRITERION.md:516 明写「主判定 struct_ok 写 :54」）。
#    结果通道：:23-24 assert（异常通道）、:54 OUT.write_text 写盘 JSON 的
#           guard/struct_ok/hunks、:55 print("STRUCT_OK:", struct_ok)、
#           :56-59 HUNKS / GUARD / OUT 观测打印；原件无 sys.exit/SystemExit，
#           正常跑完退出码恒 0（本会话基线实跑 EXIT=0）。
#    :47 diff_hunks 与 :49-51 unified_diff 是被核对象的领域数据，不是本脚本
#           对自身的 PASS/FAIL 裁决；不纳入聚合，不另造判定。
# B. 聚合口径：本脚本判定 ≡ 两条 guard 均真 且 struct_ok 为真。下方逐字复用
#    原件 :23 / :24 / :48 的同一布尔式合取，不改写、不取反、不重跑任何检查；
#    原有 4 条 print、1 次写盘、2 条 assert 全部保留，执行顺序与取值不变。
#    guard 不满足时原件在 :23 / :24 已抛 AssertionError（EXIT=1，同为 FAIL），
#    不会到达出口；满足时 3 项全真 ⇒ ok 真 ⇒ EXIT=0。判定与打印均不变。
# C1 纯追加：无任何既有行被改动，故不存在「必须改的行」需逐行说明。
# C2 原件无 if __name__ == "__main__" 块；全库 *.py 实 grep 无 import 本件的语句
#    （_ecv_compare.py:43 只把它当路径字符串、台账只当被读文件），故不存在
#    被别的脚本 import 的库本体；追加段位于全部原件行之后。
# C3 复用原件 :41 / :45 已有的全局名 ok 作聚合变量；不新增任何全局名字、
#    不新增 import、不新增函数/类；无调用方，不存在覆盖同名符号风险。
ok = True
ok = ok and bool(guard["sl_link"]["sha256"] == guard["sl_link"]["expect_sha"])   # 同原件 :23 assert
ok = ok and bool(guard["sl_link"]["bytes"] == guard["sl_link"]["expect_bytes"])   # 同原件 :24 assert
ok = ok and bool(struct_ok)                                                       # 同原件 :36/:48/:55
print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
raise SystemExit(0 if ok else 1)
