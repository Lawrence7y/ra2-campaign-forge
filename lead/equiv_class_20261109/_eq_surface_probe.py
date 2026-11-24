# -*- coding: utf-8 -*-
"""_eq_surface_probe.py — J4 判据在其余真实 multi 文档上的行为核查（作用面，只读不写盘）。
复用 _eq_proto.py 的同一 eq_merge 实现（导入 _eq_proto 会幂等重跑 6 案并刷新其输出件）。
零真机、零采样代码、不 commit、不 push。"""
import os
import sys

sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\equiv_class_20261109")
import _eq_proto as P  # noqa: E402  复用 SL / DECL_RE / eq_merge / ROOT

HEX = "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2"

_T = open(r"D:\Project\ra2-campaign-forge\lead\f2d_rootcause_20261109\F2D_ROOT_CAUSE.md",
          encoding="utf-8").read()
_r = P.SL.link(_T, r"D:\Project\ra2-campaign-forge\lead\f2d_rootcause_20261109",
               HEX, 412759, root=P.ROOT)
_m, _i = P.eq_merge(_T, _r)
_dl = [i + 1 for i, ln in enumerate(_T.splitlines()) if P.DECL_RE.search(ln)]
print("F2D_ROOT_CAUSE raw=%s final=%s decl_lines=%s applied=%s"
      % (_r["verdict"], _m["verdict"], _dl, _i.get("applied")))

_T = open(r"D:\Project\ra2-campaign-forge\lead\matrix_binding_20261108"
          r"\_m_CHAIN_VERIFY_20261108.md", encoding="utf-8").read()
_r = P.SL.link(_T, r"D:\Project\ra2-campaign-forge\lead\matrix_binding_20261108",
               HEX, 412759, root=P.ROOT)
_m, _i = P.eq_merge(_T, _r)
_dl = [i + 1 for i, ln in enumerate(_T.splitlines()) if P.DECL_RE.search(ln)]
print("M_CHAIN_VERIFY raw=%s final=%s decl_lines=%s applied=%s"
      % (_r["verdict"], _m["verdict"], _dl, _i.get("applied")))

_T = open(r"D:\Project\ra2-campaign-forge\lead\gate_validate_20261108"
          r"\GATE_TEMPLATE_REGRESSION.md", encoding="utf-8").read()
_r = P.SL.link(_T, r"D:\Project\ra2-campaign-forge\lead\gate_validate_20261108",
               HEX, 412759, root=P.ROOT)
_m, _i = P.eq_merge(_T, _r)
_dl = [i + 1 for i, ln in enumerate(_T.splitlines()) if P.DECL_RE.search(ln)]
print("GATE_TEMPLATE_REGRESSION raw=%s final=%s decl_lines=%s applied=%s"
      % (_r["verdict"], _m["verdict"], _dl, _i.get("applied")))
