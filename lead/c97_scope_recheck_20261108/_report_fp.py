# -*- coding: utf-8 -*-
# C97_SCOPE_RECHECK.md（最终交付）指纹绑定脚本 —— 只读，零写入，零真机。
# 用法: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/c97_scope_recheck_20261108/_report_fp.py
import hashlib, os, datetime

def fp(path):
    h = hashlib.sha256()
    n = 0
    with open(path, 'rb') as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
            n += len(b)
    return h.hexdigest(), n

# (绝对路径, 期望 sha256 或 None, 期望 bytes 或 None, 标签)
ITEMS = [
    # ―― 六件编排方指纹 ――
    ("D:/Project/ra2-campaign-forge/lead/direction_ruling_20261108/RULING_DIRECTION.md",
     "0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653", 16514,
     "编排方指纹1 RULING_DIRECTION.md"),
    ("D:/Project/ra2-campaign-forge/lead/r2_unclosed_cd_20261108/CD_BREAKPOINTS.md",
     "affaeae091178c13935caa283f861799b33358e4a162ece130671bb0ea3468dd", 24904,
     "编排方指纹2 CD_BREAKPOINTS.md"),
    ("D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md",
     "4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726", 48343,
     "编排方指纹3 CRITERIA_COMPARE.md"),
    ("D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_dC_recompute.py",
     "ec64adac558e87e5cdf53563368c7aacea712222e70f303ca85deb83eb08ee3a", 23115,
     "编排方指纹4 _dC_recompute.py"),
    ("D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_dC_out.txt",
     "a0deb34a4aed83efe3d0b80dfff4f05eb28eeec5fac5613ff49316fd8081337a", 13473,
     "编排方指纹5 _dC_out.txt"),
    ("D:/Project/ra2-campaign-forge/lead/r2_final_grade_20261108/R2_FINAL_GRADE.md",
     "7ce09812f7bd905a95114a2cc2cea56b3dc3dbaef3d8e0d14c58685762ecab24", 30140,
     "编排方指纹6 R2_FINAL_GRADE.md"),
    # ―― 重评轮另加核对对象 ――
    ("D:/Project/ra2-campaign-forge/lead/direction_ruling_20261108/_dr_RULING.md",
     "c6fa7a0a3315cdc95bd71916c40c4b565f5066ee2c51ad239d01db5977330316", 20942,
     "另加 _dr_RULING.md"),
    ("D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt",
     "f0177d2cbafdb4dbd388d6b38b97d14ae73688f36f58df4f0fff7edc31a59b66", 5088,
     "另加 supplement 原件 _dtrigger_supplement_out.txt"),
    # ―― 重评三交付件 ――
    ("D:/Project/ra2-campaign-forge/lead/c97_scope_recheck_20261108/_c97_scope_recheck.md",
     "ee7b3a167c9d99301474a59036cc5cc47c81bfe933cfbd653991b0d1d59ac0b1", 10995,
     "重评交付件 _c97_scope_recheck.md"),
    ("D:/Project/ra2-campaign-forge/lead/c97_scope_recheck_20261108/_c97_check.py",
     "059aba6218c13e68a0d34d467d913fca33e47b0550aff7dcc0fe44f106c193ff", 10698,
     "重评交付件 _c97_check.py"),
    ("D:/Project/ra2-campaign-forge/lead/c97_scope_recheck_20261108/_c97_check_out.txt",
     "38d5541f8c3ce04afb2be1adde15fe740e50a110138e2fa4fe84514b1a9e2023", 7375,
     "重评交付件 _c97_check_out.txt"),
    ("D:/Project/ra2-campaign-forge/lead/c97_scope_recheck_20261108/_c97_check_stderr.txt",
     None, 0, "重评轮 stderr（应 0 字节）"),
    # ―― 复核轮核验件 ――
    ("D:/Project/ra2-campaign-forge/lead/c97_scope_recheck_20261108/_verify_reply.json",
     "1fe6b1b6160e218703627ce91d449e76452060cfe52b6cc5c3c8fbac04ded62f", 4034,
     "复核轮 _verify_reply.json（被核对象=重评回件转录本）"),
    ("D:/Project/ra2-campaign-forge/lead/c97_scope_recheck_20261108/_verify_fp.py",
     None, None, "复核轮 _verify_fp.py"),
    ("D:/Project/ra2-campaign-forge/lead/c97_scope_recheck_20261108/_verify_counts.py",
     None, None, "复核轮 _verify_counts.py"),
    ("D:/Project/ra2-campaign-forge/lead/c97_scope_recheck_20261108/_verify_ast.py",
     None, None, "复核轮 _verify_ast.py"),
]

core_ok = True
all_ok = True
for idx, (path, esha, ebytes, tag) in enumerate(ITEMS):
    sha, n = fp(path)
    ok = (esha is None or sha == esha) and (ebytes is None or n == ebytes)
    has_exp = (esha is not None or ebytes is not None)
    verdict = ("MATCH" if ok else "MISMATCH") if has_exp else "-"
    if has_exp:
        all_ok = all_ok and ok
        if idx < 6:
            core_ok = core_ok and ok
    print("被核对象 SHA256 = %s，字节数 = %d（%s）-> %s" % (sha, n, tag, verdict))

print()
for p in [
    "D:/Project/ra2-campaign-forge/lead/r2_final_grade_20261108/R2_FINAL_GRADE.md",
    "D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md",
    "D:/Project/ra2-campaign-forge/lead/PENDING_DECISIONS.md",
]:
    st = os.stat(p)
    print("mtime %s = %s" % (os.path.basename(p),
          datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")))

print()
print("六件编排方指纹绑定结果 = %s" % ("全 MATCH" if core_ok else "存在 MISMATCH"))
print("全部带期望值条目 = %s" % ("全 MATCH" if all_ok else "存在 MISMATCH"))
