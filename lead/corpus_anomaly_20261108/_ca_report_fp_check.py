# -*- coding: utf-8 -*-
"""报告撰写员只读指纹核查：inventory 14 件 + 复核对象件 + _ca_ 产出件。
零真机、零采样、只读；仅打印，不写任何语料/台账。"""
import hashlib
import os

ROOT = r"D:\Project\ra2-campaign-forge"
CORPUS = os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003", "lead", "qc161_u0400_trip")
LEAD = os.path.join(ROOT, "lead")

EXPECT = [
    # (relative path label, absolute path, expected sha256 or None, expected bytes or None)
    ("l1_20261023e4/measure_w0.json", os.path.join(CORPUS, "l1_20261023e4", "measure_w0.json"),
     "8799e08dbc12e7f8674af9f7ade70d38fa4c46437861871b6d472c665616fdf9", 271414),
    ("l1_20261023e4/measure_w1.json", os.path.join(CORPUS, "l1_20261023e4", "measure_w1.json"),
     "9439e8ef02725a76d3ce2dac2eba8b330a2e70b439dc4d3c79c0104590c7834e", 233984),
    ("l1_20261023e4/measure_w2.json", os.path.join(CORPUS, "l1_20261023e4", "measure_w2.json"),
     "8d85ac02ff78e228fc12f65da2c3f8850e6fda0c1f3f35d5ca7aec5dbe2b0540", 106895),
    ("archive_T34/measure_w0.json", os.path.join(CORPUS, "archive_T34", "measure_w0.json"),
     "da30c275d8d985ddec019ce5a64f56c590b08a2f66499a7935d3b1b10df1cecd", 255493),
    ("archive_T34/measure_w1.json", os.path.join(CORPUS, "archive_T34", "measure_w1.json"),
     "39f0aae1feff6c43894ce2011e2ea952d7ac7e5825271af888de3ae8eeb31d0c", 255071),
    ("archive_T34/measure_w2.json", os.path.join(CORPUS, "archive_T34", "measure_w2.json"),
     "7cfe25d8447179772fdd827582c381e0e7d6685ed1f4eb98bf0230f4d140292b", 255122),
    ("archive_T36/measure_w0.json", os.path.join(CORPUS, "archive_T36", "measure_w0.json"),
     "20ecf4cf5274760bdf8c6c5747eaddbabf33367584ca3e70f9c128d56d89572f", 259112),
    ("archive_T36/measure_w1.json", os.path.join(CORPUS, "archive_T36", "measure_w1.json"),
     "434c6267c9fc465a500c48c2c44d06cd0a8ceba058a95171550a170e2c72e485", 255059),
    ("archive_T36/measure_w2.json", os.path.join(CORPUS, "archive_T36", "measure_w2.json"),
     "b389f1a0a155cae913e38e7c97189d363f2af81b9125f1088d2257218c20b448", 255074),
    ("archive_T43/measure_w0.json", os.path.join(CORPUS, "archive_T43", "measure_w0.json"),
     "818f2c00be1499063871e70f03902c8eee8dff4deff6c30909b2663a0674103f", 259244),
    ("archive_T43/measure_w1.json", os.path.join(CORPUS, "archive_T43", "measure_w1.json"),
     "813744fad706f3990564064b3110b754d1aee6184a3939f199c8069474523650", 255094),
    ("archive_T43/measure_w2.json", os.path.join(CORPUS, "archive_T43", "measure_w2.json"),
     "413223078e295f4ef9cc8b6a81a02cce9e642522f4083f5c9adbb5bdcf386358", 255062),
    ("SLOWFRAME_PROXY.md", os.path.join(ROOT, "lead", "slowframe_round2_20261107", "SLOWFRAME_PROXY.md"),
     "5fe880595965de4e0b39639c0d4a80d626476a9715f1cae5efd7361a0c8985d3", 26916),
    ("SLOW_WINDOW_LIMITS.md", os.path.join(ROOT, "lead", "slowwindow_n8_20261108", "SLOW_WINDOW_LIMITS.md"),
     "e7c29e06f48b2380d5bec3f99e08ac2a4ce90d94da27b48b98d5eb2113a75d60", 23707),
    # 复核回件被核对象（复核回件声称 c2b777e2…，4598 B）
    ("_verify_hy4_object.json", os.path.join(ROOT, "lead", "corpus_anomaly_20261108", "_verify_hy4_object.json"),
     "c2b777e27358158b314e208c49e86179c2541b66e4633624995967c92471b385", 4598),
    # 本写域 _ca_ 产出件（只报指纹，无预期值）
    ("_ca_A_item_l1_w2_units12of25.md", os.path.join(ROOT, "lead", "corpus_anomaly_20261108", "_ca_A_item_l1_w2_units12of25.md"), None, None),
    ("_ca_B_item_T34_T36_T43_fps.md", os.path.join(ROOT, "lead", "corpus_anomaly_20261108", "_ca_B_item_T34_T36_T43_fps.md"), None, None),
]

ok = 0
bad = 0
for label, path, exp_sha, exp_bytes in EXPECT:
    try:
        with open(path, "rb") as fh:
            data = fh.read()
        sha = hashlib.sha256(data).hexdigest()
        n = len(data)
        if exp_sha is None:
            print(f"[INFO ] {label} sha256={sha} bytes={n}")
        elif sha == exp_sha and n == exp_bytes:
            print(f"[MATCH] {label} sha256={sha} bytes={n}")
            ok += 1
        else:
            print(f"[DIFF ] {label} got sha256={sha} bytes={n} expected={exp_sha} {exp_bytes}")
            bad += 1
    except OSError as exc:
        print(f"[MISS ] {label}: {exc}")
        bad += 1

print(f"--- checked={len(EXPECT)} match={ok} mismatch/missing={bad}")
