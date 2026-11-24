import os, datetime
p = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1_20261023e4/except_post_20261026T200053072552.txt"
rp = os.path.realpath(p)
assert rp.startswith("D:\\Project\\ra2-campaign-forge"), rp
s = os.stat(rp)
print("size=", s.st_size, "mtime=", datetime.datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d %H:%M:%S.%f"), "%.9f" % s.st_mtime)
with open(rp, "r", encoding="utf-8", errors="replace") as fh:
    head = fh.read(1200)
print("---- head ----")
print(head)
