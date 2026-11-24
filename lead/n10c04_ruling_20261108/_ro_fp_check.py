# -*- coding: utf-8 -*-
# _ro_fp_check.py — N10-C04/Q3 顺序裁决 · 被核对象指纹实算（纯 hashlib 只读，零写盘，零进程接触）
# 命令：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/n10c04_ruling_20261108/_ro_fp_check.py
import hashlib

BASE = r"D:\Project\ra2-campaign-forge"
# (相对路径, 预期 sha256 或 None, 预期字节数或 None)；预期来源见行尾注
FILES = [
    ("lead/d13d14_cards_20261108/DECISION_QUESTIONS.md",
     "0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f", 27172),  # 编排方指纹
    ("lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md",
     "7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0", 29619),  # 编排方指纹
    ("lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md",
     "5b933fe2fcb3cc35c5026cb57b45f29da29c90b67a618346af248744ed3ccdb9", 32281),  # 编排方指纹
    ("lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md",
     "e0c00683fb23b0b3777d71639f3d7d265208057969073e53fd2b7195d0c3e1f7", 28648),  # 编排方指纹
    ("lead/p11_stations_20261108/P11_STATION_NAMING.md",
     "d328e4f99d428daf86047ca420d0c84668d4827865ec62296904f467f9ee4b9e", 24636),  # 编排方指纹
    ("lead/n9_erratum_20261108/N9_SPEC_ERRATUM.md",
     "61446db581a273725010e9b09cf3ebeba0d1412fc8666c0c6b8c660e4f7d22b4", 20630),  # 编排方指纹
    ("lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md",
     "c0dfb0d17edab4d0d89c43dc48bce4b84354fd13bd89cae7277aa15e82cf65f2", 54351),  # 编排方指纹
    ("lead/direction_ruling_20261108/RULING_DIRECTION.md",
     "0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653", 16514),  # 编排方指纹
    ("lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
     "c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225),  # 编排方指纹
    ("lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),  # 编排方指纹
    ("lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),  # 编排方指纹
    ("lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md",
     "20e4eeac49254b274a8382e94505525a614ec5bf24ccb89316fcd8f914406262", 26485),  # 上游 N-9:49 / SGC:136 / P11:89
    ("lead/re_line_20261105/W8_STATIC_LOCATE/F8_VISIBILITY.md",
     "ebacbfca", 19335),  # 上游仅记 8 位前缀+字节数（ERRATUM §4.2 行7：ebacbfca/19335）——按前缀比较，不补造全串
    ("lead/re_line_20261105/W8_STATIC_LOCATE/F7_TARGETING.md",
     None, None),                                                                  # 无上游指纹，登记实算值
    ("ra2youli/gamemd.exe",
     "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476", 4825360),  # SGC:9/:143 / ERRATUM:57
]

results = []
for rel, exp_sha, exp_bytes in FILES:
    p = BASE + "\\" + rel.replace("/", "\\")
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            n += len(chunk)
    sha = h.hexdigest()
    if exp_sha is None:
        verdict = "NO_EXPECT(登记实算值)"
    elif len(exp_sha) < 64:
        # 前缀比较（上游仅记短前缀时使用；另比字节数）
        ok = sha.startswith(exp_sha) and (exp_bytes is None or n == exp_bytes)
        verdict = ("MATCH(前缀%s)" % exp_sha) if ok else "MISMATCH"
    else:
        ok = (sha == exp_sha) and (exp_bytes is None or n == exp_bytes)
        verdict = "MATCH" if ok else "MISMATCH"
    results.append((rel, sha, n, verdict))
    print("[file] " + rel)
    print("  sha256 = " + sha)
    print("  bytes  = %d" % n)
    print("  vs预期 : " + verdict)

checked = [r for r in results if r[3] != "NO_EXPECT(登记实算值)"]
all_match = all(r[3].startswith("MATCH") for r in checked)
print("")
print("CHECKED_WITH_EXPECT = %d / %d" % (len(checked), len(results)))
print("ALL_MATCH = " + str(all_match))
print("WRITES_MADE = 0 (本脚本纯只读，无任何写盘语句；本会话零真机、零采样、零活进程接触)")
