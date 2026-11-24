# -*- coding: utf-8 -*-
# _fgR2_fpcheck.py —— 终评报告撰写员指纹核验（只读既有件；stdout 输出）
# 核验对象：编排方指纹六件 + 复核回件绑定对象 _fg_VERDICT_20261108.md（复核 sha256Line 所绑）
import hashlib

ITEMS = [
    (r"D:\Project\ra2-campaign-forge\lead\criteria_r3_verify_20261108\R2_BREAKPOINTS_CLOSURE.md",
     "bf426786db82c34dd6b6d21e3022678285e3e22f52dbdaa5085d85c3b6f8fbde", 22351),
    (r"D:\Project\ra2-campaign-forge\lead\r2_unclosed_b_20261108\B_BREAKPOINTS_2_6.md",
     "3aad3bddda087e171d9add1977849b70c01f7ddb5dff23b575186dfb517403ae", 19527),
    (r"D:\Project\ra2-campaign-forge\lead\r2_unclosed_cd_20261108\CD_BREAKPOINTS.md",
     "affaeae091178c13935caa283f861799b33358e4a162ece130671bb0ea3468dd", 24904),
    (r"D:\Project\ra2-campaign-forge\lead\dtrigger_round2_20261107\CRITERIA_ROUND2.md",
     "bcd7c8e53f6987a899f78fd1bd8ae90247193f1897aadf15cc58daa45211982a", 49968),
    (r"D:\Project\ra2-campaign-forge\lead\dtrigger_round2_20261107\_dA_out.txt",
     "8825e115f92bdf407cf20dde724e5633adc4e08e3f97bcee58299b95a8cb6d43", 29813),
    (r"D:\Project\ra2-campaign-forge\lead\dtrigger_round2_20261107\_dA_design.md",
     "d5d487a7792da6ce89e143faa05727a4fe484cb66b400622c02511230770e0df", 20819),
    # 复核回件绑定对象（复核 sha256Line 绑定终评报告本体）
    (r"D:\Project\ra2-campaign-forge\lead\r2_final_grade_20261108\_fg_VERDICT_20261108.md",
     "d40f9f6d36ed6b2c903f4e576cedc17f35f6598e37b89461d96d3826919d4df7", 14530),
]

for p, eh, eb in ITEMS:
    with open(p, "rb") as f:
        b = f.read()
    h = hashlib.sha256(b).hexdigest()
    name = p.replace("\\", "/").rsplit("/", 1)[1]
    print("MATCH" if (h == eh and len(b) == eb) else "MISMATCH",
          name, "bytes=%d" % len(b), h)
