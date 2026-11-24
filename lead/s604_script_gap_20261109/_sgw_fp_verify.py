# -*- coding: utf-8 -*-
# _sgw_fp_verify.py —— 撰写轮（S604_SCRIPT_GAP.md）指纹核验：编排方八件 + 复核绑定对象 + 15 份语料输入。
# 全只读 hashlib 实算；python -I -X utf8 + 绝对路径。
import hashlib, os

BASE = r"D:/Project/ra2-campaign-forge"

def fp(rel):
    p = os.path.join(BASE, rel.replace('/', os.sep))
    raw = open(p, 'rb').read()
    return hashlib.sha256(raw).hexdigest(), len(raw)

# 编排方【编排方指纹】八件（本轮逐一复算）
EXPECT8 = [
    ("lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    ("lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md",
     "7241026122978426838d6c8ccaa8ea3335fe6213adef6bae10ab9c7aa83df2f2", 17272),
    ("lead/s604_attribution_20261108/S604_ATTRIBUTION.md",
     "8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237", 27182),
    ("lead/slowframe_r3_20261108/_r3_recompute_gapdiff.py",
     "9e27495232301018ec8e5b4f38c101d6ab4835feef514215a821be00ca459a78", 12659),
    ("lead/slowframe_r3_20261108/_r3_recompute_out.txt",
     "f1f55791f14bb13669d2fde062a1d85ffaab3c05d7379c59573692c5cb88e54b", 9494),
    ("lead/slowframe_r3_20261108/S604_GAP_RECHECK.md",
     "5d1b0ecc9f0e21ddecc38584c363afa0c758f40089ccc57749f237aeffbdf726", 19291),
    ("lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
     "e7c29e06f48b2380d5bec3f99e08ac2a4ce90d94da27b48b98d5eb2113a75d60", 23707),
]

# 复核回件绑定对象：调查回件 JSON 全文逐字转写（复核 sha256Line 给出的期望值）
BIND = ("lead/s604_script_gap_20261109/_sgv_reply_json.txt",
        "ba37635836dfc3b06f10edd875f83a5ab824141944b19e8a37b522eb6775ebb8", 8211)

# 15 份语料输入件：期望值转录自 _r3_recompute_out.txt [A]（R3 轮 2026-11-08 自算）
CORPUS = {
    ("l1c_20261021", 0): ("9464cac4387ec4e0b1a02cce8f4c63755c5e08b51fd12352cd362fdaa867556f", 257797),
    ("l1c_20261021", 1): ("edf4ed136c011494c954c32cd3253337b01d8a82f227c02fd54fdc4211009b7a", 260075),
    ("l1c_20261021", 2): ("654f3bc44c74e6400c0248a978a124c3fe95449c698176f62f9c6eaca52da726", 260507),
    ("l1d_20261021", 0): ("b3dc3a9abc76c4fdfd223e405964a4935fdf573fe8c4bcb1c122afabd9f04e22", 260734),
    ("l1d_20261021", 1): ("36f59371e61cbe8a18265c70adeaee0e4aababf1a3cd88537c1dbf46f3648ad0", 260644),
    ("l1d_20261021", 2): ("7e994c7cd6ca0bf6d5554611b0748d967bb94986c09b543292ade46823cb8097", 262470),
    ("l1e_20261021", 0): ("b106bd6d3eb30a1910d1e84182a4cfd260ee5d26563b978232019e040c5637e9", 261506),
    ("l1e_20261021", 1): ("3919288d2b172e0d4571f36f412b2cc48df3460a2e416b408245bfba722d40af", 261855),
    ("l1e_20261021", 2): ("043654033d384b4713be18abd1b05dc2c0d97cb4eaa3296ff4d88a524639cd86", 263067),
    ("l3_20261021", 0):  ("e86029187da3482385313034322a66a8d9f0a7846c4f9b541834df309e03473e", 247450),
    ("l3_20261021", 1):  ("273869c17fcc67e580131284775c44896cf029a15f536de96ab2def5cd8f0739", 249000),
    ("l3_20261021", 2):  ("a71d3318a81da871f2c0568ca3411d9f76fe439ebfd7969a307200b71c4bd81a", 256142),
    ("t55k_20261020", 0): ("30c5a6e68e26e02de6014f31ac3b5a6d3fa821436fd6ec02f0a78777aa4bfaf6", 272285),
    ("t55k_20261020", 1): ("3302b2bb0f357516bddecd6b2b2bf323da8ba98e3457573b8a4ba5b14b92a7e4", 272141),
    ("t55k_20261020", 2): ("3cb933142b1abfd8653b1a63902b73ca609824ca1133655ef4b43b09dfe68b84", 272095),
}
CORPUS_DIR = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

def check(rel, want_sha, want_n):
    sha, n = fp(rel)
    ok = (sha == want_sha) and (n == want_n)
    print(("MATCH  " if ok else "MISMATCH") + " " + rel)
    print("         实算 " + sha + " " + str(n) + " B")
    if not ok:
        print("         期望 " + want_sha + " " + str(want_n) + " B")
    return ok

print("== [1] 编排方八件上游指纹复算 ==")
ok8 = 0
for rel, sha, n in EXPECT8:
    ok8 += check(rel, sha, n)
print("八件 MATCH = %d/8" % ok8)

print("== [2] 复核回件绑定对象转验 ==")
okb = check(BIND[0], BIND[1], BIND[2])

print("== [3] 15 份语料输入件在盘且未漂移（对 R3 [A] 记载值） ==")
okc = 0
for (trip, w), (sha, n) in sorted(CORPUS.items()):
    rel = CORPUS_DIR + "/" + trip + "/measure_w%d.json" % w
    okc += check(rel, sha, n)
print("语料 MATCH = %d/15" % okc)

print("== 总计: 八件 %d/8, 绑定对象 %s, 语料 %d/15 ==" %
      (ok8, "MATCH" if okb else "MISMATCH", okc))
