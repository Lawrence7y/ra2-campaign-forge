# _efv_fence_unit.py — 复核员对修版件 code_fence_lines() 的独立单测（8 例，自造文本）
import importlib.util
import json
import pathlib

spec = importlib.util.spec_from_file_location(
    "efd_unit", r"D:\Project\ra2-campaign-forge\lead\eqdecl_fix_20261110\_ef_detector.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

cases = []


def case(cid, name, lines, expect_inside, note=""):
    inside, ranges = m.code_fence_lines(lines)
    ok = inside == set(expect_inside)
    cases.append({"id": cid, "name": name, "passed": ok,
                  "inside": sorted(inside), "expect": sorted(expect_inside),
                  "ranges": [list(r) for r in ranges], "note": note})


# U1 开行带信息串
case("U1", "开行 ```python 带信息串", ["```python", "x = 集合恒等? True", "```"], [2])
# U2 闭行长度须 >= 开行
case("U2", "闭行 `` 短于开行 ``` 不闭合", ["```", "a", "``", "b"], [2, 3, 4])
# U3 同字符才闭合（~ 开 ` 不闭）
case("U3", "~ 开 ` 不闭合→兜底文件尾", ["~~~", "a", "```", "b"], [2, 3, 4])
# U4 未闭合兜底到文件尾
case("U4", "未闭合兜底", ["```", "a", "b"], [2, 3])
# U5 波浪栏
case("U5", "~~~ 闭合", ["~~~", "a", "~~~"], [2])
# U6 标记行自身不在内部
case("U6", "标记行不在内部", ["```", "a", "```", "prose"], [2])
# U7 多段
case("U7", "两段围栏", ["```", "a", "```", "p", "~~~", "b", "~~~"], [2, 6])
# U8 复刻 CA:157-165 结构：段内 seg(158,164)
lines8 = ["prose", "```", "chain_changed=18 | 集合恒等? True", "x=1", "```"]
case("U8", "CA 形态", lines8, [3, 4])

n_pass = sum(1 for c in cases if c["passed"])
out = {"n_cases": len(cases), "n_passed": n_pass,
       "all_pass": n_pass == len(cases), "cases": cases}
print(json.dumps(out, ensure_ascii=False, indent=1))
