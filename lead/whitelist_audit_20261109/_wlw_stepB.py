import json, pathlib, hashlib, re
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "whitelist_audit_20261109"
MJS = ROOT / ".zcode" / "workflow-runs"
FILES = {
 'A_ruling': 'dwfrun-db5bad08-1aa0-4dea-940f-5f66a8b27a06.mjs',
 'B_reach': 'dwfrun-c482b235-41c5-431b-b9d9-2617c362b1cc.mjs',
 'C_n11': 'dwfrun-903e6b21-eb50-4c2f-a8dd-da3851198786.mjs',
 'D_s604': 'dwfrun-bc9d8b8e-9faa-4226-8022-ccd881335683.mjs',
 'E_r9sem': 'dwfrun-8156bb52-3202-457d-bbde-6774ee112fb8.mjs',
 'F_this': 'dwfrun-5e636329-c206-4e6d-b615-3e9a0255218d.mjs',
}
KEYS = ['需谁批准', '实跑输出', '改前改后', '脚本存在', '可重建', '语义在场', 'WHITELIST_AUDIT',
        '第五步', '第二步', '六节', '必现要素', '要给出', '给出确定结论', '给出判定',
        '逐处给', '逐处改前改后', '必须给', '存在 / 不存在', '可唯一重建', '编排方已实跑确认',
        '构造的输入字典', '实跑返回', '是否一致']
OUT = {}
for tag, fn in FILES.items():
    p = MJS / fn
    t = p.read_text(encoding='utf-8', errors='replace')
    i = t.find("export const payload = ")
    raw = t[i + len("export const payload = "):]
    obj, _ = json.JSONDecoder().raw_decode(raw)
    lowered = obj.get("lowered", "")
    lines = lowered.split("\n")
    print("\n=== %s  %s  lowered_chars=%d sha256=%s ===" % (
        tag, fn, len(lowered), hashlib.sha256(lowered.encode('utf-8')).hexdigest()))
    rec = []
    for n, L in enumerate(lines, 1):
        if any(k in L for k in KEYS):
            rec.append({"n": n, "text": L})
            print("  [%s:%d] %s" % (tag, n, L))
    OUT[tag] = {"file": fn, "lines": rec,
                "sha256": hashlib.sha256(lowered.encode('utf-8')).hexdigest()}
(WDIR / "_wlw_payloads.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\nWROTE _wlw_payloads.json")
