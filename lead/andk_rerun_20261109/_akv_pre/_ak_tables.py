# -*- coding: utf-8 -*-
"""_ak_tables.py — 从 _ak_runs.jsonl / _ak_summary.json 生成逐输入判定表与矩阵交付件。
只读本任务写域内的 _ak_* 产物；不读、不改任何绝对只读原件。
用法：python -I -X utf8 "<绝对路径>/_ak_tables.py"
"""
import hashlib
import json
from pathlib import Path

W = Path(r"D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109")
S = json.loads((W / "_ak_summary.json").read_text(encoding="utf-8"))
RUNS = [json.loads(l) for l in (W / "_ak_runs.jsonl").read_text(encoding="utf-8").splitlines()]
ORDER = ("d27", "d28", "d29", "d30")


def w(name, text):
    (W / name).write_text(text, encoding="utf-8", newline="\n")


# ---------- 逐输入判定表（含命令全文 + stdout sha256 + 输入指纹） ----------
L = ["# _ak_PER_INPUT_TABLE.md — 逐输入独立跑判定表（2026-11-09 实跑）", "",
     "外壳：`_ak_shell.py --mode full`（108 次真实 subprocess 运行，记录于 `_ak_runs.jsonl`）。",
     "Python `" + S["python"] + "`；唯一写域 `" + S["write_domain"] + "`。",
     "每次运行均绑：被核脚本 SHA256+字节数、两份输入 SHA256+字节数、命令全文、EXIT、STDOUT 原文、stdout_sha256、原件未变复核。", "",
     "## 公式", "",
     "```",
     "P_WA(input)  = [逐词副本 WA 在该 input 上 EXIT=0 ∧ 输出含 PASS ∧ 无 FAIL]",
     "P_WB(input)  = [逐词副本 WB 在该 input 上 EXIT=0 ∧ 输出含 PASS ∧ 无 FAIL]",
     "AGGREGATE    = AND_k(P_WA, P_WB)   with k = 2   （甲' 第一律：两次真实独立运行，非推断）",
     "BAD_NEEDLE_CAUGHT = [SENT 副本在该 input 上 EXIT≠0 ∧ verdict=FAIL]",
     "DISTINGUISHABLE_PASS = AGGREGATE ∧ BAD_NEEDLE_CAUGHT",
     "```", "",
     "A = 原 RULING（两词都在） / B = 删第二根针 / C = 两词都删；输入变更一律落在写域副本上。", "",
     "## 1 逐输入判定总表（A/B/C）", "",
     "| gate | input | 原件 `any(present)` | P_WA | P_WB | `AGGREGATE = AND_k` | SENT EXIT | BAD_NEEDLE_CAUGHT | DISTINGUISHABLE_PASS |",
     "|---|---|---|---|---|---|---|---|---|"]
for r in S["abc"]:
    L.append("| %s | %s | %s (EXIT=%d) | %s | %s | **%s** | %d | %s | %s |" %
             (r["gate"], r["input"], r["original_verdict"], r["original_exit"],
              r["p_wa"], r["p_wb"], r["and_k"], r["sentinel_exit"],
              r["bad_needle_caught"], r["distinguishable_pass"]))
L += ["", "**实算值**：`AND_k` 在 A 输入四件均 True（= 0b1），在 B 输入四件均 False（因 P_WB=False），"
      "在 C 输入四件均 False（P_WA=P_WB=False）。`DISTINGUISHABLE_PASS` 只在 A 输入为 True。", "",
      "## 2 A/B/C 三次完整输出与退出码（命令全文 + stdout sha256）", ""]
for gate in ORDER:
    L += ["### " + gate, ""]
    for label in ("A", "B", "C"):
        recs = [r for r in RUNS if r["gate"] == gate and r["tag"].startswith("ABC_")
                and r["exp"] == ("abc_%s" % label if r["tag"] == "ABC_ORIGINAL"
                                 else "abc_%s_%s" % (label, r["variant"]))]
        # 按 tag 排序：ORIGINAL / WORDA / WORDB / SENTINEL
        recs.sort(key=lambda r: {"ABC_ORIGINAL": 0, "ABC_WORDA": 1,
                                 "ABC_WORDB": 2, "ABC_SENTINEL": 3}[r["tag"]])
        assert len(recs) == 4, (gate, label, len(recs))
        L += ["**输入 %s**：%s" % (label, recs[0]["doc_desc"]), "",
              "| 口径 | CMD (绝对路径) | 被核脚本 SHA256 / 字节 | 输入 SHA256 / 字节 | EXIT | STDOUT 原文 | stdout_sha256 | 判定 |",
              "|---|---|---|---|---|---|---|---|"]
        for r in recs:
            inp = "; ".join("%s=%s/%dB" % (n, v["sha256"][:16], v["bytes"])
                           for n, v in sorted(r["inputs"].items()))
            L.append("| %s | `%s` | `%s` / %d | %s | %d | `%r` | `%s` | %s |" %
                     (r["tag"], r["cmd"], r["script_sha256"], r["script_bytes"],
                      inp, r["exit"], r["stdout"], r["stdout_sha256"], r["verdict"]))
        L += ["", "  CWD = `%s`；布局 = %s" % (recs[0]["cwd"], recs[0]["layout"]), ""]

L += ["## 3 上游口径：12 份沙箱副本在原件输入上的 AND_k（k=2 真实逐词运行）", "",
      "| gate | WA EXIT/STDOUT | WB EXIT/STDOUT | p=[P_WA,P_WB] | AGGREGATE=AND_2 | SENT EXIT | BAD_NEEDLE_CAUGHT | DISTINGUISHABLE_PASS |",
      "|---|---|---|---|---|---|---|---|"]
for r in S["per_word"]:
    L.append("| %s | %d / `%r` | %d / `%r` | %s | **%s** | %d | %s | %s |" %
             (r["gate"], r["wa"]["exit"], r["wa"]["stdout"],
              r["wb"]["exit"], r["wb"]["stdout"], r["p"], r["aggregate"],
              r["sentinel"]["exit"], r["bad_needle_caught"], r["distinguishable_pass"]))
L += ["", "**重要限定**：这一行的 `DISTINGUISHABLE_PASS=True` 只证明「把 OR 元组换成单元素后的两份"
      "**改写脚本副本**」各能独立过，不证明「**原件**的 exit=0」有逐输入内容。原件仍是 `any(present)` 一次聚合。", ""]

# ---------- 坏针哨兵矩阵 ----------
M = ["# _ak_BAD_NEEDLE_MATRIX.md — 坏针哨兵全矩阵（件 × 项）", "",
     "注射只在写域副本的输入文档上做；被核脚本一律用**原件逐字节副本**（BASE，SHA256 见 §4）。",
     "「注入前判定」= 该件 BASE 基线实跑；「是否被抓」= 注入后 `EXIT≠0 ∧ verdict=FAIL`。", "",
     "| gate | 项 | 检查内容 | 注射动作 | 注入前 | 注入后 | 注入后 STDOUT | 是否被抓 |",
     "|---|---|---|---|---|---|---|---|"]
for m in S["matrix"]:
    M.append("| %s | %s | %s | %s | %s (EXIT=%d) | %s (EXIT=%d) | `%r` | **%s** |" %
             (m["gate"], m["item"], m["label"], m["doc_desc"],
              m["before"], m["before_exit"], m["after"], m["after_exit"],
              m["after_stdout"], m["caught"]))
M += ["", "## 汇总", "",
      "| gate | 8 项 AND_8 | 9 行 AND_9（含「只杀一根针」） | 抓到数 | 漏抓项 |",
      "|---|---|---|---|---|"]
for g, v in S["and_matrix"].items():
    M.append("| %s | %s | **%s** | %d/%d | %s |" %
             (g, v["and_8"], v["and_9"], v["caught_count"], v["rows"],
              ", ".join(v["missed"]) if v["missed"] else "无"))
M += ["", "**7 项单一字面量的结论**：本实跑把 8 个编号项各自注射一根坏针，"
      "四件全部 8/8 被抓（`AND_8=True`）：`[1]` 缺文件、`[2]` 声明行、`[3]` 小节标题、"
      "`[4]`/`[5]`/`[6]` 字面量、`[7]` 引用计数、`[8]` selfBias。"
      "即单元素 `all([word in body])` 在本口径下**都在工作**，删掉字面量即非零退出。",
      "**唯一漏抓**是每件额外加的第 9 行「OR 项只杀一根针」：四件全部 `注入后仍 PASS / EXIT=0`。"
      "这不是「单项检查没工作」，而是 OR 语义本身允许另一根针单独满足 ⇒ `AND_9=False`。", ""]

# ---------- 上游注射复现 ----------
R = ["# _ak_REPRO.md — 与 STALE_PASS_INVENTORY.md:94-101 上游注射实证对齐", "",
     "上游口径复刻（`_sp_gen_injected.py:4-12` / `_sp_gen_d28.py:4-10` / `_sp_gen_d29d30.py:6-19`）："
     "只把**脚本副本**里的第二根针字面量换成 `TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ`，"
     "OR 结构不变；输入文档为原件逐字节副本。命令全文、EXIT、STDOUT、stdout_sha256 见 `_ak_runs.jsonl` 的 "
     "`REPRO_BASE` / `REPRO_INJECTED` 行。", "",
     "| gate | BASE CMD | INJ CMD | BASE EXIT / STDOUT | INJ EXIT / STDOUT | 逐字一致 | stdout_sha256 一致 | 均 PASS | 能否复现 |",
     "|---|---|---|---|---|---|---|---|---|"]
for g in ORDER:
    r = S["repro"][g]
    R.append("| %s | `%s` | `%s` | %d / `%r` | %d / `%r` | %s | %s | %s | **能** |" %
             (g, r["base_cmd"], r["inj_cmd"], r["base_exit"], r["base_stdout"],
              r["inj_exit"], r["inj_stdout"], r["stdout_identical"],
              r["stdout_sha_identical"], r["both_pass"]))
R += ["", "注射副本 SHA256 / 字节数（与 `STALE_PASS_INVENTORY.md:98-101` 登记的 INJ 前缀逐字符相符）：", ""]
for g in ORDER:
    r = S["repro"][g]
    R.append("- %s: `%s`，%d B" % (g, r["inj_script_sha256"], r["inj_script_bytes"]))
R += ["", "**差异原因**：本外壳把「k 个输入」拆到两份**单元素词表副本**上真实各跑一次，"
      "则 B 输入（第二根针被删）在 WB 副本上必 FAIL（`AND_k=False`）；"
      "而上游注射只改脚本词表里的一个词、仍保留 OR 另一词，原件的 `any(present)` "
      "在输入不变时必然仍 PASS 且输出逐字一致。两者并不矛盾，是同一 OR 塌缩的两种观测面。", ""]

w("_ak_PER_INPUT_TABLE.md", "\n".join(L) + "\n")
w("_ak_BAD_NEEDLE_MATRIX.md", "\n".join(M) + "\n")
w("_ak_REPRO.md", "\n".join(R) + "\n")
print("WROTE 3 tables")
for n in ("_ak_PER_INPUT_TABLE.md", "_ak_BAD_NEEDLE_MATRIX.md", "_ak_REPRO.md"):
    b = (W / n).read_bytes()
    print(n, hashlib.sha256(b).hexdigest(), len(b))
