# -*- coding: utf-8 -*-
"""XVERIFY H8 探针 P5：__pycache__ 字节码与当前源的一致性 + harness find_pids 可用性。

★ 关注点：发射器 A11 只 hash `.py`，而解释器执行的是 `__pycache__` 里的 .pyc
  （CPython 时间戳校验只看 (mtime, size)，且 PYTHONDONTWRITEBYTECODE 只禁写不禁读）。
  ⇒ 若候选目录里躺着与源不同步的 .pyc，真机跑的不是被审的那份代码。
★ 做法：读 .pyc 头部的 (magic, flags, mtime, size)，与当前源比对；再 unmarshal
  code object，与现场 compile 的 code object 比 co_consts/co_names 摘要。
★ 附带：执行 harness 自己的 find_pids 原件，证明 harness 侧枚举未坏（对照发射器副本）。
"""
import json
import marshal
import importlib.util
import sys
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"D:\Project\ra2-campaign-forge")

TARGETS = [
    (ROOT / "lead/goal1_harness8_20261031/qc151_trip.harness8.py",
     ROOT / "lead/goal1_harness8_20261031/__pycache__/qc151_trip.harness8.cpython-312.pyc"),
    (ROOT / "lead/goal1_harness8_20261031/_launch_h8_20261031.py",
     ROOT / "lead/goal1_harness8_20261031/__pycache__/_launch_h8_20261031.cpython-312.pyc"),
]


def pyc_header(raw):
    magic = raw[0:4]
    flags = int.from_bytes(raw[4:8], "little")
    mtime = int.from_bytes(raw[8:12], "little", signed=True)
    size = int.from_bytes(raw[12:16], "little", signed=True)
    return magic, flags, mtime, size


def digest(co):
    """稳定摘要：递归取 co_names / co_consts 中的字符串与嵌套 code。"""
    parts = [co.co_name, tuple(co.co_names), co.co_argcount,
             co.co_varnames]
    consts = []
    for c in co.co_consts:
        if hasattr(c, "co_name"):
            consts.append(("CODE", digest(c)))
        else:
            consts.append(repr(c))
    parts.append(tuple(consts))
    return repr(parts)


def main():
    res = {}
    for src, pyc in TARGETS:
        st = src.stat()
        item = {"src_exists": src.is_file(), "pyc_exists": pyc.is_file()}
        if pyc.is_file():
            raw = pyc.read_bytes()
            magic, flags, m, s = pyc_header(raw)
            item.update({
                "pyc_recorded_mtime": m, "pyc_recorded_size": s,
                "src_actual_mtime": int(st.st_mtime), "src_actual_size": st.st_size,
                "mtime_match": m == int(st.st_mtime), "size_match": s == st.st_size,
                "invalidation_flags": flags,
            })
            code_in_pyc = marshal.loads(raw[16:])
            fresh = compile(src.read_text(encoding="utf-8"), str(src), "exec")
            item["code_digest_equal"] = (digest(code_in_pyc) == digest(fresh))
        res[pyc.name] = item

    # harness find_pids 原件
    sp = importlib.util.spec_from_file_location(
        "p5_h8", str(ROOT / "lead/goal1_harness8_20261031/qc151_trip.harness8.py"))
    m = importlib.util.module_from_spec(sp)
    sys.modules["p5_h8"] = m
    sp.loader.exec_module(m)
    fp = m.find_pids(Path(sys.executable).name)
    res["harness_find_pids"] = {"self_name": Path(sys.executable).name,
                                "self_pid": os.getpid(),
                                "found_count": len(fp),
                                "self_in_found": os.getpid() in fp}
    print(json.dumps(res, ensure_ascii=False, indent=1))
    (HERE / "probe_pyc_and_findpids.stdout.txt").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
