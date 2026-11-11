#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§610 台账回填：append-only 追加 + 四项自检 + 条目标号分配。

写域：本脚本自身、stdout 落盘、备份副本 —— 均在 lead/re_ledger_apply_610_20261112/
被追加件：lead/GOAL_THREE_TARGETS_20261018.md（只允许文件末尾追加，既有字节零改动）

依据：
  - 草案：lead/re_chain_synth_v2_20261111/LEDGER_SECTION_DRAFT_v2.md（12,266 B /
          sha256 da79a234804247fd3477957b997e51202553e882d8654dd68e91c9274e5e0bab）
  - 三轮核验：lead/re_chain_v3_verify_20261112/V3_VERIFY.md（VERDICT = READY_TO_APPEND）
  - 调度方独立复核：C1-C6 逐条亲验（hexdump + capstone 字节级 + 文件存在性）
"""
import hashlib
import os
import re
import shutil
import sys
from collections import Counter

REPO = r"D:\Project\ra2-campaign-forge"
LEDGER = os.path.join(REPO, "lead", "GOAL_THREE_TARGETS_20261018.md")
DRAFT = os.path.join(REPO, "lead", "re_chain_synth_v2_20261111", "LEDGER_SECTION_DRAFT_v2.md")
WORK = os.path.join(REPO, "lead", "re_ledger_apply_610_20261112")

BASE_BYTES = 788030
BASE_SHA = "a2579798976f00b4dc09edc85c0b2efa0255289411819297047e2362ba3bffda"
BASE_LINES = 9845

TAIL = (
    "- **本节边界与未验**：(1) 全部结论为**磁盘静态读数**，运行期行为、跨图普适性、因果推断一律未验；"
    "(2) 【已证（CFG）】三项均**未做运行期确认**，零真机铁律下不可得——「未做运行期确认」≠「已被运行期证伪」；"
    "(3) 符号名（`Read_INI`/`Get_Bool`/`Write_INI`/`Put_Bool`/`this->Vector`/`IsAllocated`/`GrowthStep` 等）"
    "为探针标注与结构推断，**非二进制字面**，字节级条目只对指令字节与计数负责；"
    "(4) 台账历史指纹 `93c2974b` 算法仍未决（维持）；"
    "(5) 六探针读数本身**未经门禁化复核**（`lead/re_atlas_reassess_20261112/RE_ATLAS_REASSESS.md` 已如实登记）。\n"
    "- **本节零真机、零采样代码、未改既有件（除本节追加本体）、未 commit、未 push**。\n"
)

HEADER = """## §610 · ★★★ 并账入账：11-10/11-11 六探针静态链合流入账（18 条字节级【已证】+ 3 条【已证（CFG）】+ 8 条待证）；经「起草 → 异族核验（6 条改正项）→ 修正 → 三方复核 READY_TO_APPEND」四轮定稿（2026-11-12）

- **性质与依据**：本节是 `lead/re_chain_synthesis_20261111/` 那条因果链报告的**台账入账版**。草案四版流转：① 初稿 `lead/re_chain_synthesis_20261111/CHAIN_SYNTHESIS.md`（20,971 B / sha256 `c88717d71c4b59d88ecd04f234843f561a829e63f5b967659e10acfdcf8254b3`）+ `LEDGER_SECTION_DRAFT.md`（3,415 B / `b40ac2a7b6fade6854fc0960aa9b01252ccff3dc292c780b979a8e56b664a800`）；② 异族跨模型核验 `lead/re_chain_v2_xverify_20261112/XVERIFY.md`（24,363 B / `9ef8b4a1fbe51278e190d30b48807a504bb191d396238c2507ce26ee1da9856f`）判 **PASS_WITH_CORRECTIONS**，列 **C1–C6** 六条必改；③ 修正版 `lead/re_chain_synth_v2_20261111/RE_GRADING.md`（26,217 B / `c17a3c63a3c8858761b206622f60f96ff5fc579ffd1cd2fe838869c2fcc967e5`）+ `LEDGER_SECTION_DRAFT_v2.md`（12,266 B / `da79a234804247fd3477957b997e51202553e882d8654dd68e91c9274e5e0bab`），改正记录 `lead/re_chain_v2_fix_20261112/FIX_RECORD.md`（23,869 B / `6276243bf0b0f2ef3b99dfb7849bd56ace58431e4cc6d9049e47c7e3db8c5efe`）；④ 三方复核 `lead/re_chain_v3_verify_20261112/V3_VERIFY.md`（22,685 B）判 **V-C1…V-C6 + V-ALL 全 PASS / VERDICT = READY_TO_APPEND**。
- **靶件**：`ra2bench/gamemd.exe` = **4,825,360 B** / sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（草案与三轮核验各自实算 MATCH）。**本节零真机**：未启动 gamemd.exe / ra2loader / YURI.exe，未 attach、未读活进程内存、未写 hook / 采样 / MiniDump / SuspendThread 代码；对 exe 仅静态读字节。
- **证据目录缩写**：`sf`=`lead/slot2_fullscan_20261111/_sf_scan_out.txt`（1,834 行）；`cw`=`lead/re_crashwriter_static_20261110/_cw_disasm_out.txt`（177 行）；`ps`=`lead/playerctrl_semantics_20261111/_ps_disasm_out.txt`（1,283 行）；`oo`=`lead/re_orphan_owners_20261110/_oo_map_out.txt`（151 行）；`md`=`lead/re_map_preset_decode_20261110/_md_parse_out.txt`（167 行）；`ld`=`lead/re_loadbench_diff_20261110/_ld_diff_out.txt`（103 行）。
- **定级口径（本章统一）**：**字节级读数**=直接从 exe 字节/反汇编指令流读出的确定事实（含穷举扫描计数）；**【已证（CFG）】**=从指令序列推出的控制流/数据流逻辑结论、**未做运行期确认**；**【未证】**=依赖未验前提或运行期机制断言。混合条目按「读数部分 / 推断部分」拆分定级。**凡「逃逸 / 无别名 / 无任何运行时读取点」这类全称否定结论，只依赖静态扫描且探针自标为前提者，一律不留在【已证】/【已证（CFG）】，同降【未证】**；其底层计数/指令字节仍按字节级读数维持【已证】。
- **条目标号**：A 节 18 条 = `§610-A01`…`§610-A18`；B 节 3 条 = `§610-B01`…`§610-B03`；C 节待证 8 项 = 编号列表逐项。引用本节时请用条目号。

"""


def sha(b):
    return hashlib.sha256(b).hexdigest()


def chk(tag, ok, detail=""):
    print("[%s] %-30s %s" % ("PASS" if ok else "FAIL", tag, detail))
    return ok


def sect(lines, start_pat, stop_pat=None):
    out, on = [], False
    for ln in lines:
        if ln.startswith(start_pat):
            on = True
            out.append(ln)
            continue
        if on and stop_pat and ln.startswith(stop_pat):
            break
        if on:
            out.append(ln)
    return out


def renumber(sec_lines, prefix):
    n = 0
    out = []
    for ln in sec_lines:
        if ln.startswith("| §6xx 待编号"):
            n += 1
            ln = ln.replace("| §6xx 待编号", "| §610-%s%02d" % (prefix, n), 1)
        out.append(ln)
    return out, n


def main():
    os.makedirs(WORK, exist_ok=True)
    all_ok = True

    raw = open(LEDGER, "rb").read()
    before_len = len(raw)
    before_sha = sha(raw)
    print("== STEP 0 · before 指纹 ==")
    print("before_bytes  = %d" % before_len)
    print("before_sha256 = %s" % before_sha)
    all_ok &= chk("0a before bytes == 788030", before_len == BASE_BYTES, str(before_len))
    all_ok &= chk("0b before sha == baseline", before_sha == BASE_SHA, before_sha[:16] + "...")

    bak = os.path.join(WORK, "GOAL_before.md")
    if not os.path.exists(bak):
        shutil.copyfile(LEDGER, bak)
    print("backup        = %s (%d B)" % (bak, os.path.getsize(bak)))

    dv = open(DRAFT, encoding="utf-8").read()
    dlines = dv.splitlines()

    a_lines, na = renumber(sect(dlines, "## A ·", "## B ·"), "A")
    b_lines, nb = renumber(sect(dlines, "## B ·", "## C ·"), "B")
    c_lines, nc = renumber(sect(dlines, "## C ·", "## 备注"), "C")
    n_lines = sect(dlines, "## 备注", None)

    print("\n== STEP 0b · 条目编号分配 ==")
    print("A 节 %d 条（§610-A01…§610-A%02d）" % (na, na))
    print("B 节 %d 条（§610-B01…§610-B%02d）" % (nb, nb))
    print("C 节占位符 %d 处" % nc)
    all_ok &= chk("0c A 节条数 == 18", na == 18, str(na))
    all_ok &= chk("0d B 节条数 == 3", nb == 3, str(nb))

    sec_a = "\n".join(a_lines).rstrip()
    sec_b = "\n".join(b_lines).rstrip()
    sec_c = "\n".join(c_lines).rstrip()
    sec_n = "\n".join(n_lines).rstrip()

    joined = "\n".join([sec_a, sec_b, sec_c, sec_n])
    all_ok &= chk("0e 残余 §6xx 占位符 == 0", joined.count("§6xx 待编号") == 0,
                  str(joined.count("§6xx 待编号")))
    all_ok &= chk("0f A 节含 §610-A18", "§610-A18" in sec_a, "")
    all_ok &= chk("0g B 节含 §610-B03", "§610-B03" in sec_b, "")

    body = HEADER + sec_a + "\n\n" + sec_b + "\n\n" + sec_c + "\n\n" + sec_n + "\n\n" + TAIL
    payload = "\n\n" + body
    pb = payload.encode("utf-8")

    print("\n== STEP 1 · 追加 ==")
    print("payload_bytes  = %d" % len(pb))
    print("payload_sha256 = %s" % sha(pb))

    with open(LEDGER, "ab") as f:
        f.write(pb)

    after = open(LEDGER, "rb").read()
    after_len = len(after)
    after_sha = sha(after)
    print("\n== STEP 2 · after 指纹 ==")
    print("after_bytes  = %d" % after_len)
    print("after_sha256 = %s" % after_sha)

    print("\n== STEP 3 · 四项自检 ==")
    pre = sha(after[:before_len])
    all_ok &= chk("a 前缀 sha == before sha", pre == before_sha, pre[:16] + "...")

    txt = after.decode("utf-8")
    heads = re.findall(r"(?m)^##+ *§(\d+)\b", txt)
    hc = Counter(heads)
    for n in ("605", "606", "607", "608", "609", "610"):
        c = hc.get(n, 0)
        all_ok &= chk("b §%s 节标题数 == 1" % n, c == 1, str(c))

    appended = after[before_len:]
    all_ok &= chk("c 追加字节数 == payload", len(appended) == len(pb), str(len(appended)))
    all_ok &= chk("c' 追加段 sha == payload sha", sha(appended) == sha(pb), "")

    before_lines = len(open(bak, encoding="utf-8").read().splitlines())
    after_lines = len(txt.splitlines())
    print("before_lines = %d" % before_lines)
    print("after_lines  = %d  (+%d)" % (after_lines, after_lines - before_lines))
    all_ok &= chk("d before_lines == 9845", before_lines == BASE_LINES, str(before_lines))
    all_ok &= chk("d' 行数增量 == 追加行数",
                  (after_lines - before_lines) == len(payload.splitlines()),
                  str(len(payload.splitlines())))
    all_ok &= chk("d'' UTF-8 可解码无 U+FFFD", txt.count("\ufffd") == 0,
                  "fffd=%d" % txt.count("\ufffd"))

    print("\n== STEP 4 · 定位 ==")
    lines = txt.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("## §610"):
            print("§610 标题行 = L%d" % (i + 1))
            break
    print("追加段起始行 = L%d" % (before_lines + 1))
    print("总行数 = %d" % len(lines))
    print("\n==== RESULT: %s ====" % ("ALL PASS" if all_ok else "HAS FAILURE"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
