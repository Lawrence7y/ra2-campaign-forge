# -*- coding: utf-8 -*-
import importlib.util, pathlib
p = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\gate_fp7_20261108\_g7_predicates.py")
s = importlib.util.spec_from_file_location("_cs_g7x", p)
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print("r10-like names:", [x for x in dir(m) if x.startswith("r10")])
print("has r10_scan:", hasattr(m, "r10_scan"))
print("callable:", callable(getattr(m, "r10_scan", None)))
