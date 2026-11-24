# 独立复核员脚本 ⑥：越界检查
# (a) 八件上游指纹再算一遍（与 ① 对比，证明本会话期间未漂移）
# (b) .zcode/workflow-runs 全部 224 文件的 (大小, sha256) 汇总指纹
# (c) gate_subject_id_20261109 / 前序 _dn_* 产物：全量 mtime+sha256 快照（只读）
# (d) 统计本写域内 _dnv_* 与 _dn_* 文件，确认新写件只有 _dnv_ 前缀
import json, hashlib, pathlib, os

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
OUT = ROOT / "lead/gate_doc_name_fix_20261109/_dnv_boundary_out.json"
BASE8 = {
    "lead/gate_subject_id_20261109/GATE_SUBJECT_ID_FIX.md": ("302a45644359f14d4f420225ac56784579a658cb852a0b0df0ddde6532adf63c", 31692),
    "lead/gate_subject_id_20261109/_si_SUBJECT_ID_DEFECT.md": ("8c67dc3fc950baf16e4e39b650ca25210e24e3512307a09eaf30cc9cecd6f4dc", 23441),
    "lead/gate_subject_id_20261109/_si_fix_lib.py": ("54751e9a10bca4becfae3449d4a19155dc7744dff77a8a22d7d70d9a7fd70eee", 2850),
    "lead/gate_subject_id_20261109/_si_gatescan_out.json": ("c8024cb7e538dfbc3766acc08d231789b80d601d7cc4bba4e05ed89d8ff87d94", 611043),
    "lead/gate_subject_id_20261109/_si_wfscan_out.json": ("e326df6b4040dc9e5471f891c8db55d8ede1681434336de5e5626c43e2029f52", 180256),
    "lead/gate_subject_id_20261109/_si_exploit_out.txt": ("151f4f94b890403ba4785a7d570ad11abbe68a4aa12363967682729167e2c587", 5717),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
def fp(p):
    b=p.read_bytes(); return hashlib.sha256(b).hexdigest(), len(b)

up=[]
for rel,(es,en) in BASE8.items():
    s,n=fp(ROOT/rel); up.append({"file":rel,"sha256":s,"bytes":n,"match":(s==es and n==en)})

wf=sorted(p for p in (ROOT/".zcode/workflow-runs").iterdir() if p.is_file())
wfrows=[]
for p in wf:
    s,n=fp(p)
    wfrows.append({"file":p.name,"sha256":s,"bytes":n,"mtime":p.stat().st_mtime})
wf_roll=hashlib.sha256("\n".join(r["file"]+":"+r["sha256"]+":"+str(r["bytes"]) for r in wfrows).encode()).hexdigest()

# 诊断域 + 本写域全量文件
def snap(d):
    rows=[]
    if not d.is_dir(): return rows
    for p in sorted(d.rglob("*")):
        if p.is_file():
            s,n=fp(p)
            rows.append({"file":p.relative_to(ROOT).as_posix(),"sha256":s,"bytes":n,"mtime":p.stat().st_mtime})
    return rows
diag=snap(ROOT/"lead/gate_subject_id_20261109")
wdom=snap(ROOT/"lead/gate_doc_name_fix_20261109")

# 找出本会话新建的 _dnv_* 与原有 _dn_* 分界（按 mtime 排序，列出最后 20 件）
last=sorted(wdom,key=lambda r:r["mtime"])[-20:]
out={"upstream_recheck":{"total":len(up),"matches":sum(1 for r in up if r["match"]),"rows":up},
     "workflow_runs":{"files":len(wfrows),"mjs":sum(1 for r in wfrows if r["file"].endswith(".mjs")),
                      "rolling_sha256":wf_roll,"untracked_by_git":True},
     "diagnostic_domain":{"files":len(diag),"rolling_sha256":hashlib.sha256("\n".join(r["file"]+":"+r["sha256"] for r in diag).encode()).hexdigest()},
     "write_domain":{"files":len(wdom),"newest_20":[{"file":r["file"],"bytes":r["bytes"]} for r in last]},
     "new_dnv_files":[r["file"] for r in wdom if "/_dnv_" in r["file"] or r["file"].endswith("_dnv_sandbox36")],
     "preexisting_dn_files":[r["file"] for r in wdom if "/_dn_" in r["file"] and "/_dnv_" not in r["file"]],
     "diag_files":diag}
OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({k:v for k,v in out.items() if k not in ("diag_files",)},ensure_ascii=False,indent=2))
