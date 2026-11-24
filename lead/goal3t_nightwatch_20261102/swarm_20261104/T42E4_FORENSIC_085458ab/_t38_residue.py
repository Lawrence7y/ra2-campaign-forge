import os, datetime
R = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T38"
for f in ("measure_w1.json", "measure_w1_end_x.png", "measure_w2.json", "measure_w2_end_x.png"):
    p = os.path.realpath(R + "/" + f)
    s = os.stat(p)
    print(f, s.st_size, datetime.datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d %H:%M:%S.%f"), "%.9f" % s.st_mtime)
res = os.stat(os.path.realpath(R + "/measure_w1_end_x.png")).st_mtime
w1j = os.stat(os.path.realpath(R + "/measure_w1.json")).st_mtime
print("residue vs (T38 own w1 json + 66.8ms expected png):", round((w1j + 0.0668) - res, 2), "s earlier")
