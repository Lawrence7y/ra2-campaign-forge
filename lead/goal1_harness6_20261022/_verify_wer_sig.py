#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WER `Sig[]` 解析门禁：三种真实布局都必须正确，含交错布局（原缺陷）。

背景：异族核验（B 组）发现 harness6 的**单游标**写法在交错布局下静默丢值
（`Sig[0].Name / Sig[1].Name / Sig[0].Value / Sig[1].Value` ⇒ 得 {B:1}，
丢掉了 Sig[1] 的值）。本项目 25 份 AppCrash 实证 `Sig[7]/Sig[6]` 与
`Sig[6]/Sig[7]` 两种排列并存；交错布局虽未在实证中出现，但一旦出现会
**静默丢失异常代码**，方向是"少报而非误读"。

本门禁把四种布局都断言一遍，并对旧单游标写法做负控（必须转红）。

★ 用 importlib 正常导入被测模块，不用 exec/eval（避免代码注入面）。
"""
import importlib.util
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "qc151_trip.harness6.py"

RESULTS = []


def check(tag, cond, ev=""):
    RESULTS.append((tag, bool(cond), ev))
    print("  %-48s %s  %s" % (tag, "PASS" if cond else "FAIL", ev))


def load_module():
    spec = importlib.util.spec_from_file_location("h6_under_test", SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # 模块顶层只定义函数/常量，无副作用
    return mod


CASES = {
    "顺序布局（Name/Value 成对）":
        "Sig[0].Name=Exception Code\nSig[0].Value=c0000005\n"
        "Sig[1].Name=Exception Offset\nSig[1].Value=00012345\n",
    "交错布局（全部 Name 后全部 Value）":
        "Sig[0].Name=Exception Code\nSig[1].Name=Exception Offset\n"
        "Sig[0].Value=c0000005\nSig[1].Value=00012345\n",
    "乱序索引（Sig[7] 在 Sig[6] 前）":
        "Sig[7].Name=Exception Offset\nSig[7].Value=00012345\n"
        "Sig[6].Name=Exception Code\nSig[6].Value=c0000005\n",
    "Value 先于 Name（逆序）":
        "Sig[0].Value=c0000005\nSig[0].Name=Exception Code\n",
}


def old_parser(text):
    """旧单游标写法（原缺陷实现），仅用于负控。"""
    top, pairs, sig, cur = {}, [], {}, None
    for line in text.splitlines():
        s = line.strip()
        if not s or "=" not in s:
            continue
        key, _, val = s.partition("=")
        key, val = key.strip(), val.strip()
        if key.startswith("Sig[") and key.endswith(".Name"):
            cur = val
            continue
        if key.startswith("Sig[") and key.endswith(".Value"):
            pairs.append((cur, val))
            if cur is not None and cur not in sig:
                sig[cur] = val
            cur = None
            continue
        if key.startswith("Sig[") or key.startswith("DynamicSig["):
            continue
        if key not in top:
            top[key] = val
    return {"top": top, "sig_pairs": pairs, "sig": sig}


def main():
    print("=" * 92)
    print("WER Sig[] 解析门禁（含交错布局）")
    print("=" * 92)

    mod = load_module()
    parse = mod._h6_wer_parse

    for name, txt in CASES.items():
        sig = parse(txt)["sig"]
        if name.startswith("Value 先于 Name"):
            good = sig.get("Exception Code") == "c0000005"
        else:
            good = (sig.get("Exception Code") == "c0000005"
                    and sig.get("Exception Offset") == "00012345")
        check("正控 " + name, good, "sig=%s" % sig if not good else "")

    # 辅助函数本身
    check("_sig_index('Sig[7].Value','.Value') == 7",
          mod._sig_index("Sig[7].Value", ".Value") == 7, "")
    check("_sig_index 对非 Sig 键返回 None",
          mod._sig_index("AppName", ".Value") is None, "")
    check("_sig_index 对非数字返回 None",
          mod._sig_index("Sig[x].Value", ".Value") is None, "")

    print()
    print("--- 负控：旧单游标写法 ---")
    r = old_parser(CASES["交错布局（全部 Name 后全部 Value）"])
    # ★ 旧写法不只是丢值，而是**错配**：把异常代码塞进偏移字段。
    #   这比丢值更危险 —— 读数看似有效但是错的。
    check("负控 旧写法在交错布局下错配（Offset 拿到 Code 的值）",
          r["sig"].get("Exception Offset") == "c0000005",
          "sig=%s（把 c0000005 配给了 Exception Offset）" % r["sig"])
    check("负控 旧写法在交错布局下确实丢了 Exception Code",
          r["sig"].get("Exception Code") is None,
          "sig=%s" % r["sig"])
    # 旧写法在顺序布局下是对的 —— 证明缺陷只对交错布局可见
    r2 = old_parser(CASES["顺序布局（Name/Value 成对）"])
    check("负控 旧写法在顺序布局下正常（说明缺陷是布局敏感的）",
          r2["sig"].get("Exception Offset") == "00012345",
          "sig=%s" % r2["sig"])

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    if npass != len(RESULTS):
        for t, c, e in RESULTS:
            if not c:
                print("  - %s  %s" % (t, e))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
