# -*- coding: utf-8 -*-
# _hpv_ulpn_verify.py —— 复核员独立核验脚本（只读；stdout 输出；不写任何文件）
# ① 14 件指纹独立实算 vs 编排方基线 ② 九条改文逐字比对 ③ JSON↔B2B 映射 ④ 包结构
import hashlib, json, os, re, sys

ROOT = r"D:\Project\ra2-campaign-forge"
def rp(rel): return os.path.join(ROOT, rel.replace("/", os.sep))
def rd(rel):
    with open(rp(rel), "rb") as f: b = f.read()
    return b.decode("utf-8").replace("\r\n", "\n")
def sha(rel):
    h = hashlib.sha256()
    with open(rp(rel), "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()
def line(rel, n):
    return rd(rel).split("\n")[n - 1]

PASS = []; FAIL = []
def chk(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f"\n        {detail}"))

# ---------- ① 指纹：编排方基线 14 件 ----------
BASE = {
 "lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md": ("b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b", 22048),
 "lead/v2_precision_fix_20261108/_pf2_findings_20261109.md": ("4aef8957094008262d980640836ab0aec3e797f892b25fe8ff02b6aa87957fe4", 7966),
 "lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md": ("6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8", 29818),
 "lead/w2_samecause_20261109/W2_SAME_CAUSE.md": ("75a0369b97f72f9d615ced86c580c6e63bfcce4f29de1c86bd74e8542aa5c895", 19552),
 "lead/text_fix_unified_20261109/_uf_UNIFIED_FIX_LIST_20261109.md": ("441b073a39a2ac195d90d43e3ba85f3c2202d5fafce31bec9c96e000a01e0923", 25095),
 "lead/u5u6_mirror_20261109/_m5_cells.json": ("ce89f6463d1b2fb64deae55f869db4d94086bcb4bce868cec3870317b2c63bf3", 2525),
 "lead/u5u6_mirror_20261109/U5U6_MIRROR_TEXTS.md": ("f320a80110806e6b57281988085d40776b43e719123db29cdb6564fe68c6c545", 24897),
 "lead/strict_exposure_20261109/STRICT_EXPOSURE.md": ("3a4b1bb7cf7f0bd501b3e99d575c4907dd0e17f5557dd0b8826e5fb07fe2bdc8", 23798),
 "lead/b2b_design_20261106/STATE_MATRIX.json": ("1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
 "lead/b2b_design_20261106/B2B_DESIGN.md": ("565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
 "lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md": ("c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801", 28897),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
print("== ① 指纹实算（hashlib，独立实现） ==")
n_ok = 0
for rel, (es, en) in BASE.items():
    got, n = sha(rel), os.path.getsize(rp(rel))
    ok = got == es and n == en
    n_ok += ok
    print(f"  {'OK ' if ok else 'NG '} {rel}  {got}/{n}")
chk("指纹 13/13 内容件逐字节等于编排方基线", n_ok == 13, f"ok={n_ok}")
cf = rp("lead/counterpart_fix_20261109/COUNTERPART_FIX.md")
chk("COUNTERPART_FIX.md ABSENT（符合编排方 MISSING 登记）", not os.path.exists(cf))
mdr = "lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md"
chk("补登记 MATRIX_DEFECT_REACHABILITY.md = cd03a91a…/27825（包内声称值）",
    sha(mdr) == "cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6" and os.path.getsize(rp(mdr)) == 27825,
    f"{sha(mdr)}/{os.path.getsize(rp(mdr))}")
utfx = "lead/text_fix_unified_20261109/UNIFIED_TEXT_FIX.md"
chk("UNIFIED_TEXT_FIX.md = ec0fb8ec…/42172（包附录C 转引值的旁证实算）",
    sha(utfx) == "ec0fb8ec47cfb71be5b28bc8a76f9152a6cbd377e741e7be1902a0958fbba154" and os.path.getsize(rp(utfx)) == 42172,
    f"{sha(utfx)}/{os.path.getsize(rp(utfx))}")

# ---------- ② 九条改文逐字比对 ----------
print("\n== ② 九条改文逐字比对（包引文 vs 源件正本） ==")
def blocks(p):  # 提取 _hp_U 文件的 ``` 围栏块
    out, cur, inf = [], [], False
    for l in rd(p).split("\n"):
        if l.strip().startswith("```"):
            if inf: out.append("\n".join(cur)); cur = []
            inf = not inf; continue
        if inf: cur.append(l)
    return out

HP = "lead/handoff_pack_20261109/"
U = {i: blocks(HP + f"_hp_U{i}.md") for i in range(1, 10)}
cells = json.loads(rd("lead/u5u6_mirror_20261109/_m5_cells.json"))

v2_91 = line("lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md", 91)
pf2_104 = line("lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md", 104)
pf2_193 = line("lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md", 193)
row5 = rd("lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md").split("\n")
r131, r132, r135 = row5[130], row5[131], row5[134]
json_lines = rd("lead/b2b_design_20261106/STATE_MATRIX.json").split("\n")
b2b_lines = rd("lead/b2b_design_20261106/B2B_DESIGN.md").split("\n")
w2_lines = rd("lead/w2_samecause_20261109/W2_SAME_CAUSE.md").split("\n")
w2_122, w2_124 = w2_lines[121], w2_lines[123]
mdr_lines = rd(mdr).split("\n")
uf = rd("lead/text_fix_unified_20261109/_uf_UNIFIED_FIX_LIST_20261109.md")
mirror = rd("lead/u5u6_mirror_20261109/U5U6_MIRROR_TEXTS.md")
findings = rd("lead/v2_precision_fix_20261108/_pf2_findings_20261109.md")

# U1
chk("U1 原文 == V2:91 实行", U[1][0] == v2_91, f"pack={U[1][0]!r}\n        src={v2_91!r}")
chk("U1 改后替换文本 == pf2:104 逐字", U[1][1] == pf2_104, f"pack={U[1][1]!r}\n        src={pf2_104!r}")
chk("U1 拼装行 == V2:91 把「删除行数 0」原位换成 pf2:104", U[1][2] == v2_91.replace("删除行数 0", U[1][1]) and v2_91.count("删除行数 0") == 1)
chk("U1 变体（pf2_findings:27 粗体版）在源件实存", "九 hunk 内实测 +255/−13（替换位删除 13 行：H03=1、H04=9、H05/H06/H09 各 1；R3:31,43 与 CANDIDATE_LF.diff 实测一致）；**允许范围外删除 = 0**" in findings)

# U2
old2 = re.search(r'"condition":"(.*?)","verdict"', json_lines[1]).group(1)
chk("U2 原文 == STATE_MATRIX.json:2 实行", U[2][0] == json_lines[1])
chk("U2 改后 condition == pf2:193 逐字", U[2][1] == pf2_193, f"pack={U[2][1]!r}\n        src={pf2_193!r}")
chk("U2 改后 condition == _m5_cells.json json2_new", U[2][1] == cells["json2_new"])
chk("U2 拼装整行 == JSON:2 原行仅换 condition 值", U[2][2] == json_lines[1].replace(old2, U[2][1]))
chk("U2 出处 row5:131 明写「pf2 §4.5 :193 文案原样」", "JSON:2 ← pf2 §4.5 :193 文案原样" in r131)

# U3
old5 = re.search(r'"condition":"(.*?)","verdict"', json_lines[4]).group(1)
chk("U3 原文 == STATE_MATRIX.json:5 实行", U[3][0] == json_lines[4])
chk("U3 追加文本 == row5:132 「」内注记逐字", ("「" + U[3][1] + "」") in r132, f"pack={U[3][1]!r}\n        row5:132={r132!r}")
chk("U3 追加后完整 condition == row5:132 去外侧「」 == _m5_cells.json json5_new", U[3][2] == cells["json5_new"] and cells["json5_new"] in r132)
chk("U3 完整 condition = 原文condition + 追加文本（拼接点在原串末尾）", old5 + U[3][1] == cells["json5_new"])

# U4
old4 = re.search(r'"condition":"(.*?)","verdict"', json_lines[3]).group(1)
chk("U4 原文 == STATE_MATRIX.json:4 实行", U[4][0] == json_lines[3])
chk("U4 加句 == row5:135 「」内加句逐字", ("「" + U[4][1] + "」") in r135, f"pack={U[4][1]!r}\n        row5:135={r135!r}")
chk("U4 推荐拼后全文 == _m5_cells.json json4_new_recommended", U[4][2] == cells["json4_new_recommended"])
chk("U4 推荐拼后 = 原文condition + 加句插在「独立 error 出口」后", old4.replace("独立 error 出口", "独立 error 出口" + U[4][1]) == cells["json4_new_recommended"])

# U5/U6/U7
def compose(ln, cell):
    parts = b2b_lines[ln - 1].split("|")
    assert len(parts) == 9 and "|" not in cell
    return "|".join(parts[:3] + [" " + cell + " "] + parts[4:])
for i, (ln, key, mirror_tag) in ((5, (148, "U5", "3.1")), (6, (151, "U6", "3.2")), (7, (150, "U7", "3.3"))):
    pass
chk("U5 原文整行 == B2B_DESIGN.md:148 实行", U[5][0] == b2b_lines[147])
chk("U5 改后整行 = :148 原行仅换第3列 == _m5_cells.json U5.new_condition_cell", U[5][1] == compose(148, cells["U5"]["new_condition_cell"]), f"pack={U[5][1]!r}\n        comp={compose(148, cells['U5']['new_condition_cell'])!r}")
chk("U5 改后整行 == U5U6_MIRROR_TEXTS §3.1 成文交付", U[5][1] in mirror)
chk("U6 原文整行 == B2B_DESIGN.md:151 实行", U[6][0] == b2b_lines[150])
chk("U6 改后整行 = :151 原行仅换第3列 == json U6 cell", U[6][1] == compose(151, cells["U6"]["new_condition_cell"]), f"pack={U[6][1]!r}\n        comp={compose(151, cells['U6']['new_condition_cell'])!r}")
chk("U6 改后整行 == U5U6_MIRROR_TEXTS §3.2 成文交付", U[6][1] in mirror)
chk("U7 原文整行 == B2B_DESIGN.md:150 实行", U[7][0] == b2b_lines[149])
chk("U7 改后整行 = :150 原行仅换第3列 == json U7 cell", U[7][1] == compose(150, cells["U7"]["new_condition_cell"]), f"pack={U[7][1]!r}\n        comp={compose(150, cells['U7']['new_condition_cell'])!r}")
chk("U7 改后整行 == U5U6_MIRROR_TEXTS §3.3 成文交付", U[7][1] in mirror)
chk("U7 JSON:4 推荐拼后全文 == json4_new_recommended == MIRROR §3.3", U[7][2] == cells["json4_new_recommended"] and U[7][2] in mirror)
chk("U7/U4 加句同句逐字（row5:135）", U[4][1] == "（post.read_error 非空时仍先落 post_read_error，见 :5 行）" and ("「" + U[4][1] + "」") in r135)

# U8/U9
chk("U8 原文 == MATRIX_DEFECT_REACHABILITY.md:154 实行", U[8][0] == mdr_lines[153], f"pack={U[8][0]!r}\n        src={mdr_lines[153]!r}")
chk("U8 改后 == W2_SAME_CAUSE §5.2:122 引用块内容逐字（去「> 」前缀）", U[8][1] == w2_122[2:] if w2_122.startswith("> ") else False, f"pack={U[8][1][:60]!r}…\n        src={w2_122[:60]!r}…")
chk("U8 改后亦见 _uf 汇总件 U8 条（同文转载）", U[8][1] in uf)
chk("U9 原文评级格实存于 MDR:146", U[9][0] in mdr_lines[145], f"src:146={mdr_lines[145]!r}")
chk("U9 改后 == W2 §5.2:124 建议注记逐字（至「未验）」）", U[9][1] in w2_124, f"src:124={w2_124!r}")
print(f"        [注] W2:124 建议注记句末在源件带句号收尾（…未验）。——包引文止于「未验）」，句号属源件行文标点；P8（替换/追加形态）未决")
chk("U9 改后亦见 _uf 汇总件 U9 条（同文转载）", U[9][1] in uf)

# ---------- ③ JSON↔B2B 映射 ----------
print("\n== ③ JSON 行 ↔ B2B 行 映射（state/preState 逐行） ==")
bad = []
for i in range(14):
    jl, bl = json_lines[1 + i], b2b_lines[147 + i]
    js = re.search(r'"state":"(.*?)","preState":"(.*?)"', jl)
    bc = [x.strip().strip("`") for x in bl.split("|")]
    if not (js and bc[1] == js.group(1) and bc[2] == js.group(2)):
        bad.append(f"JSON:{2+i} vs B2B:{148+i} {js.groups() if js else None} vs ({bc[1]},{bc[2]})")
chk("映射 i↔148+(i−2)：14 行 state/preState 逐行全等（含 JSON:2↔148、JSON:4↔150、JSON:5↔151）", not bad, "; ".join(bad))
chk("B2B:144 硬声明「下表与之逐行一致」在案", "下表与之逐行一致" in b2b_lines[143])

# ---------- ④ 包结构 ----------
print("\n== ④ 包结构 ==")
for i in range(1, 10):
    t = rd(HP + f"_hp_U{i}.md")
    heads = all(h in t for h in ("## 目标", "## 原文", "## 出处", "## 需谁批准", "## 依赖关系"))
    chk(f"_hp_U{i}.md 六要素齐（目标/原文/改后/出处/批准/依赖）", heads and re.search(r"## (改后|追加|加句)", t) is not None)
ov = rd(HP + "_hp_OVERVIEW.md")
chk("_hp_OVERVIEW.md 单页账 9条/9行/4文件/4次换版/未决16 与声明一致",
    all(k in ov for k in ("9 条", "9 行、4 个文件", "4 次", "16 项", "P1–P16")))

# ---------- 汇总绑定（被核对象 = 15 件 _hp_ 包文件，按文件名排序拼接内容的整体 SHA256） ----------
print("\n== ⑤ 被核对象（整编包 15 件）聚合绑定 ==")
pack_files = sorted([f for f in os.listdir(rp(HP)) if f.startswith("_hp_") and not f.startswith("_hpv_")])
h = hashlib.sha256(); total = 0
for f in pack_files:
    with open(rp(HP + f), "rb") as fh: b = fh.read()
    h.update(b); total += len(b)
    print(f"  {f}  {hashlib.sha256(b).hexdigest()}  {len(b)}")
print(f"PACK_FILES={len(pack_files)}")
print(f"AGGREGATE_SHA256={h.hexdigest()}")
print(f"AGGREGATE_BYTES={total}")

print(f"\n==== SUMMARY: {len(PASS)} PASS / {len(FAIL)} FAIL ====")
for f in FAIL: print("  FAIL:", f)
