# -*- coding: utf-8 -*-
import os, datetime
ROOT = r"D:\Project\ra2-campaign-forge"
rel = [
 'lead/cert_realcheck_20261109/_cr_seal.json',
 'lead/gate_pipeline_20261109/_gp_regression_out.json',
 'lead/gate_pipeline_20261109/_gp_regression.py',
 'lead/gate_r9sem_20261109/_r9s_regress_out.json',
 'lead/cert_realcheck_20261109/_cr_build_seal.py',
 'lead/cert_realcheck_20261109/_cr_real_verify.py',
]
t = {}
for r in rel:
    p = os.path.join(ROOT, *r.split("/"))
    st = os.stat(p)
    t[r] = (st.st_ctime, st.st_mtime)
    print("%-70s create=%s mtime=%s" % (
        r,
        datetime.datetime.fromtimestamp(st.st_ctime).isoformat(sep=" ", timespec="seconds"),
        datetime.datetime.fromtimestamp(st.st_mtime).isoformat(sep=" ", timespec="seconds")))
s = t[rel[0]][0]
print()
for r in rel[1:]:
    d = s - t[r][0]
    h, rem = divmod(abs(d), 3600)
    m, sec = divmod(rem, 60)
    print("seal.CreationTime - %-62s = %+7d s = %dh %dm %ds" % (r, d, h, m, sec))
print()
print("seal: CreationTime to mtime gap =", int(t[rel[0]][1] - s), "s")
print("seal_builder mtime - seal CreationTime =", int(t[rel[4]][1] - s), "s")
