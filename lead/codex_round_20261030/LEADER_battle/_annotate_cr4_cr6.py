# -*- coding: utf-8 -*-
"""_annotate_cr4_cr6.py — C-R4/C-R6 处置：追加式标注两文件（行尾保型）。"""

NOTES = [
    (r"D:\Project\ra2-campaign-forge\lead\codex_round_20261030\LEADER_battle\frozen_recheck_h8_pre.txt",
     ["# [作废标注 C-R6 2026-11-01] 本清单系 v1 时代批前采集（第 6 行钉 v1 e29a9a07）；",
      "# v2 落盘后由 frozen_recheck_h8_v2.txt（六行 dd5459fe）取代；",
      "# 本件仅作历史留痕，勿用于批前复验。（XVERIFY_H8_RR_20261031.md C-R6）"]),
    (r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\_adjudicate_h8_offline.py",
     ["# [C-R4 标注 2026-11-01] 本自检采用宽口径（note 文本引用/容器写入=rec 镜像计为引用点），",
      "# 非 _adjudicate_h7.py C4/C12 原口径；严格口径下 H8_FRAME_WAIT_HZ 零代码引用、",
      "# _H8_STATE 4写0读——处置已在 XVERIFY_H8_RR_20261031.md C-R4 登记。"]),
]

for path, lines in NOTES:
    raw = open(path, "rb").read()
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    nl = b"\r\n" if crlf > lf else b"\n"
    body = nl + nl.join(l.encode("utf-8") for l in lines) + nl
    with open(path, "ab") as fh:
        fh.write(body)
    raw2 = open(path, "rb").read()
    print(path.split("\\")[-1], "annotated; CRLF=%d LF=%d" % (raw2.count(b"\r\n"), raw2.count(b"\n")))
