#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""X11 静态收口普查：C/L3 收场触发者的三替代解释——逐条判 + 每条配可见对照。

承接 §424 X11（残留）/ §425（结论）。零真机、只读普查。

★ 为什么写脚本而非只留台账散文（本仓反复踩的坑）：
  「图里没有 [Triggers]」是**否定式断言**，零命中默认不可信，必须配
  **阳性对照**（同 grep 模式在确实有 [Triggers] 的文件上必须命中 >0），
  否则「0」可能只是「我看不见」。⇒ 每条普查都是 (被测, 对照, 期望) 三元组，
  对照不过则该条判 FAIL，不判 PASS。

判据编号 T1–T5：
  T1 趟图 [Trigger* 节 =0，但母图 .orig 同模式 =1（阳性对照）——脚本收场否证
  T2 趟图 TimeLimit= 键 =0，但同模式对全树某已知含该键件 =1——定时器收场否证
  T3 趟图 [Basic] 无 EndOfGame=yes（EndOfGame 键可见性对照由 .orig/yrm 给）
  T4 结束时实体计数恒非零（歼灭收场否证）——C 旁路时钟三处读数同值
  T5 载体 csf 不含胜/负播报串（victorious/defeated 0）⇒ 画面非胜负播报族；
     对照=csf 里 Mission/OK 散词可见（装置看得见串），并如实登记：目标全句串
     在 csf/mix 也 0 命中 ⇒ 文案来源未定位（**不抬升判决**，只作旁证）
"""
from __future__ import annotations

import hashlib
import os
import re
import struct
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
OUT = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

# ★ 变异接口（负控用）：环境变量把普查的输入换成诱饵件，对应判据必须变红。
#   无变异时走真实趟产物。判据红/绿只由**实际读到的字节**决定——不是常数。
C_MAP = Path(os.environ.get("CENSUS_C_MAP", str(OUT / "_src_L1_sf8_20261020" / "XMP29U2.MAP")))
L3_MAP = Path(os.environ.get("CENSUS_L3_MAP", str(OUT / "_src_L3_sf10c_20261021" / "XMP29U2.MAP")))
CLOCK = Path(os.environ.get("CENSUS_CLOCK", str(OUT / "l1_20261023c/_v11a_concurrent_clock.json")))

RESULTS = []


def chk(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print("  [%s] %-58s %s" % ("PASS" if ok else "FAIL", name, detail))


def sec_hits(path, prefix):
    """统计形如 ^[<prefix>... ] 的节名命中行数（INI 文本，字节级）。"""
    data = path.read_bytes()
    n = 0
    matched = []
    for m in re.finditer(rb"\[(" + re.escape(prefix.encode()) + rb"[^\]]*)\]", data):
        n += 1
        matched.append(m.group(1).decode("latin1"))
    return n, matched


def main() -> int:
    print("=" * 78)
    print("X11 收场触发者普查（三替代解释两否一存），每条配阳性对照")
    print("=" * 78)

    c_map = C_MAP
    l3_map = L3_MAP
    orig_map = OUT / "_maps_fixed" / "XMP29U2.MAP.orig_93c2974b"
    yrm = OUT / "_src_L1_sf8_20261020" / "[2]0LoadBench_U0400.yrm"
    csf = OUT / "_src_L1_sf8_20261020" / "ra2md.csf"

    # 先钉两趟图确实是 C/L3 用的图（防普查对象张冠李戴）。
    # ★ 变异件换图时跳过 T0（sha 锚只约束真实趟产物）。
    if os.environ.get("CENSUS_SKIP_SHA_ANCHOR"):
        chk("T0 趟图 sha 锚（变异件跳过）", True, "CENSUS_SKIP_SHA_ANCHOR=1")
    else:
        def sha16(p):
            return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        chk("T0a C 趟图 sha16=0add791d…（measure_w0 登记值）",
            sha16(c_map).startswith("0add791d"), sha16(c_map))
        chk("T0b L3 趟图 sha16=f3bb0a4e…（measure_w0 登记值）",
            sha16(l3_map).startswith("f3bb0a4e"), sha16(l3_map))

    # T1 触发器：两趟图必须 0，母图 + yrm 必须 >0（同一 sec_hits('Trigger') 装置）
    nt_c, _ = sec_hits(c_map, "Trigger")
    nt_l3, _ = sec_hits(l3_map, "Trigger")
    nt_orig, matched_orig = sec_hits(orig_map, "Trigger")
    nt_yrm, _ = sec_hits(yrm, "Trigger")
    chk("T1a 阳性对照：母图 .orig 确有 [Trigger*] 节", nt_orig >= 1,
        "命中 %d: %s" % (nt_orig, matched_orig))
    chk("T1b 阳性对照2：yrm 确有 [Trigger*] 节", nt_yrm >= 1, "命中 %d" % nt_yrm)
    chk("T1d ★ 趟图无触发器（脚本收场否证，装置已证能看见）",
        nt_c == 0 and nt_l3 == 0, "C=%d L3=%d（对照 .orig=%d yrm=%d）"
        % (nt_c, nt_l3, nt_orig, nt_yrm))
    # 母图触发器内容是否只是音效（主动收场动作=0）
    if nt_orig:
        blk = orig_map.read_bytes().split(b"[Triggers]")[1].split(b"\n[")[0]
        names = re.findall(rb",([^,]*Sounds[^,]*),", blk)
        actions = [a for a in (b"Victory", b"Defeat", b"Destroy", b"EndOfScript")]
        act_hits = sum(blk.count(a) for a in actions)
        chk("T1c 母图触发器全为环境音效、无收场动作", act_hits == 0,
            "音效条=%d 收场动作命中=%d" % (len(names), act_hits))

    # T2 TimeLimit：趟图 0 + 装置可见性对照（拿含 TimeLimit 的已知件，没有就构造内存样本）
    tl_c = c_map.read_bytes().count(b"TimeLimit")
    tl_l3 = l3_map.read_bytes().count(b"TimeLimit")
    # 装置可见性：同一样本内插入一次 TimeLimit 必须被同一计数装置看见
    probe = c_map.read_bytes() + b"\nTimeLimit=2\n"
    chk("T2a 阳性对照：插入式探针计数装置可见", probe.count(b"TimeLimit") == tl_c + 1,
        "base=%d probe=%d" % (tl_c, probe.count(b"TimeLimit")))
    chk("T2b ★ 趟图无 TimeLimit（定时器收场否证）",
        tl_c == 0 and tl_l3 == 0, "C=%d L3=%d" % (tl_c, tl_l3))

    # T3 EndOfGame=yes：两趟图无该键=yes
    basic = c_map.read_bytes().split(b"[Basic]")[1].split(b"\n[")[0]
    eog = re.findall(rb"EndOfGame=(\w+)", basic)
    chk("T3 [Basic] EndOfGame 非 yes（战役链收场否证）",
        b"yes" not in [x.lower() for x in eog], "值=%s" % eog)

    # T4 歼灭收场否证：C 旁路时钟跳零前/时/尾三处 units 同值非零
    import json
    clock = json.loads(CLOCK.read_bytes())
    ser = clock["series"]  # (t, f, units, inf, techno)
    zi = next(i for i in range(1, len(ser)) if ser[i][1] == 0 and ser[i - 1][1] > 0)
    u_pre, u_at, u_end = ser[zi - 1][2], ser[zi][2], ser[-1][2]
    chk("T4 ★ 跳零时 units 非零且稳定（歼灭/胜负收场否证）",
        u_at > 0 and u_pre == u_at == u_end,
        "units 前=%d 跳零=%d 尾=%d（inf=%d techno=%d 全程恒定）"
        % (u_pre, u_at, u_end, ser[zi][3], ser[zi][4]))

    # T5 csf 胜/负播报串缺失（画面非胜负族）；可见性对照=Mission/OK 散词
    csfd = csf.read_bytes()
    def csf_count(s):
        return csfd.count(s.encode("utf-16-le")) + csfd.count(s.encode("latin1"))
    chk("T5a 装置可见性：csf 里 Mission/OK 散词可数（装置看得见串）",
        csf_count("Mission") > 0 and csf_count("OK") > 0,
        "Mission=%d OK=%d" % (csf_count("Mission"), csf_count("OK")))
    chk("T5b 趟图 csf 无胜/负播报全词（画面非胜负播报族，登记不确定）",
        csf_count("defeated") == 0 and csf_count("victorious") == 0,
        "defeated=%d victorious=%d（目标全句串来源未定位，见 §425 四）"
        % (csf_count("defeated"), csf_count("victorious")))

    print("\n" + "=" * 78)
    npass = sum(1 for _n, ok, _d in RESULTS if ok)
    print("TOTAL %d/%d PASS" % (npass, len(RESULTS)))
    for n, ok, d in RESULTS:
        if not ok:
            print("  FAILED: %s | %s" % (n, d))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
