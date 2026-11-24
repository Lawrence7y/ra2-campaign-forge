# -*- coding: utf-8 -*-
"""确定性门禁：A 组残余引用账及验收记录核验门禁。

运行方式：
    python -I -X utf8 lead/a_residual_20261106/check_a_residual.py

检查项：
1) lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md 与 lead/a_residual_20261106/ACCEPTANCE_RECORDS.json 都存在；JSON 可解析且是数组且非空；
2) 每项 13 个字段齐全（itemId/itemClass/originalClaim/boundedClaim/evidence/tier/citeAs/unresolved/reviewerRole/inputHashes/artifactHashes/decision/timestamp）；
3) itemId 全局唯一；itemClass 覆盖 R1/R2/R3 三类；
4) tier 只能是 CONFIRMED/PARTIAL/UNVERIFIED；decision 只能是 ACCEPT/REJECT/PARTIAL；
5) inputHashes 与 artifactHashes 里的每个哈希：回文件系统实算比对，不符就 FAIL 并 print 是哪个文件；
6) 双向一致：lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md 里出现的每个 itemId 都能在 JSON 找到，反之亦然；
7) lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md 含「## 4 未验」小节且非空。

退出码：
    0 = PASS
    1 = 内容不合格（逐条 print 原因）
    2 = 文件缺失/不可解析
★ 脚本只读，不许改交付件。
"""
import hashlib
import json
import os
import re
import sys

# 确定仓库根目录（以当前执行工作目录为准）
REPO_ROOT = os.path.abspath(os.getcwd())

MD_REL = "lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md"
JSON_REL = "lead/a_residual_20261106/ACCEPTANCE_RECORDS.json"

md_path = os.path.normpath(os.path.join(REPO_ROOT, MD_REL))
json_path = os.path.normpath(os.path.join(REPO_ROOT, JSON_REL))

# -------------------------------------------------------------
# 检查项 1 (文件存在性与可解析性部分) -> 退出码 2
# -------------------------------------------------------------
hard_errors = []

if not os.path.isfile(md_path):
    hard_errors.append(f"Markdown 账目文件不存在: {MD_REL}")
if not os.path.isfile(json_path):
    hard_errors.append(f"JSON 验收记录文件不存在: {JSON_REL}")

if hard_errors:
    print("GATE FAIL (文件缺失/不可解析)")
    for err in hard_errors:
        print(f"  - {err}")
    sys.exit(2)

# 读取并解析 Markdown
try:
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
except Exception as exc:
    print(f"GATE FAIL (文件缺失/不可解析): 读取 Markdown 失败 ({MD_REL}): {exc}")
    sys.exit(2)

# 读取并解析 JSON
try:
    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)
except Exception as exc:
    print(f"GATE FAIL (文件缺失/不可解析): 解析 JSON 失败 ({JSON_REL}): {exc}")
    sys.exit(2)

if not isinstance(records, list):
    print(f"GATE FAIL (文件缺失/不可解析): JSON 根节点不是数组 ({JSON_REL})")
    sys.exit(2)

# -------------------------------------------------------------
# 检查项 1..7 (内容合规性检查) -> 退出码 1
# -------------------------------------------------------------
problems = []

# 1) JSON 是数组且非空
if len(records) == 0:
    problems.append("ACCEPTANCE_RECORDS.json 数组为空，未包含任何验收记录")

# 2) 每项 13 个字段齐全
REQUIRED_FIELDS = (
    "itemId",
    "itemClass",
    "originalClaim",
    "boundedClaim",
    "evidence",
    "tier",
    "citeAs",
    "unresolved",
    "reviewerRole",
    "inputHashes",
    "artifactHashes",
    "decision",
    "timestamp",
)

ALLOWED_TIERS = {"CONFIRMED", "PARTIAL", "UNVERIFIED"}
ALLOWED_DECISIONS = {"ACCEPT", "REJECT", "PARTIAL"}
ALLOWED_CLASSES = {"R1", "R2", "R3"}
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

seen_ids = set()
seen_classes = set()
total_hashes_checked = 0

def safe_abs(rel_path):
    if ".." in rel_path or rel_path.startswith("/") or rel_path.startswith("\\"):
        raise ValueError(f"检测到非法路径跃迁: {rel_path}")
    full = os.path.abspath(os.path.normpath(os.path.join(REPO_ROOT, rel_path)))
    if not full.startswith(REPO_ROOT):
        raise ValueError(f"路径超出仓库根目录范围: {rel_path}")
    return full

for idx, rec in enumerate(records):
    if not isinstance(rec, dict):
        problems.append(f"记录 #{idx} 不是合法 JSON 对象")
        continue

    item_id = rec.get("itemId")
    item_label = f"itemId={item_id}" if item_id else f"记录#{idx}"

    # 检查 13 个字段是否齐全
    missing_fields = [k for k in REQUIRED_FIELDS if k not in rec]
    if missing_fields:
        problems.append(f"{item_label} 缺失字段: {', '.join(missing_fields)}")

    # 3) itemId 全局唯一
    if not item_id or not isinstance(item_id, str) or not item_id.strip():
        problems.append(f"记录 #{idx} 的 itemId 为空或非字符串")
    elif item_id in seen_ids:
        problems.append(f"发现重复的 itemId: {item_id}")
    else:
        seen_ids.add(item_id)

    # 3) itemClass 覆盖 R1/R2/R3 三类
    item_class = rec.get("itemClass")
    if item_class not in ALLOWED_CLASSES:
        problems.append(f"{item_label} itemClass 无效: '{item_class}' (必须为 R1/R2/R3)")
    else:
        seen_classes.add(item_class)

    # 4) tier 只能是 CONFIRMED/PARTIAL/UNVERIFIED
    tier = rec.get("tier")
    if tier not in ALLOWED_TIERS:
        problems.append(f"{item_label} tier 无效: '{tier}' (必须为 CONFIRMED/PARTIAL/UNVERIFIED)")

    # 4) decision 只能是 ACCEPT/REJECT/PARTIAL
    decision = rec.get("decision")
    if decision not in ALLOWED_DECISIONS:
        problems.append(f"{item_label} decision 无效: '{decision}' (必须为 ACCEPT/REJECT/PARTIAL)")

    # 字段非空与类型检查
    for str_field in ("originalClaim", "boundedClaim", "evidence", "citeAs", "reviewerRole", "timestamp"):
        val = rec.get(str_field)
        if val is None or not isinstance(val, str) or not val.strip():
            problems.append(f"{item_label} 字段 '{str_field}' 为空或非字符串")

    unresolved = rec.get("unresolved")
    if unresolved is not None and not isinstance(unresolved, list):
        problems.append(f"{item_label} unresolved 必须为数组")

    # 5) inputHashes 与 artifactHashes 里的每个哈希：回文件系统实算比对，不符就 FAIL 并 print 是哪个文件
    for hash_dict_name in ("inputHashes", "artifactHashes"):
        h_dict = rec.get(hash_dict_name)
        if h_dict is None or not isinstance(h_dict, dict):
            problems.append(f"{item_label} 字段 '{hash_dict_name}' 必须为字典")
            continue
        if len(h_dict) == 0:
            problems.append(f"{item_label} 字段 '{hash_dict_name}' 为空字典")
            continue

        for file_rel, declared_hash in h_dict.items():
            if not isinstance(file_rel, str) or not file_rel.strip():
                problems.append(f"{item_label} {hash_dict_name} 中存在空路径")
                continue
            if not isinstance(declared_hash, str) or not HEX64_RE.match(declared_hash.strip().lower()):
                problems.append(f"{item_label} {hash_dict_name} 文件 '{file_rel}' 的哈希值不是有效的 64 位 SHA256 十六进制值: '{declared_hash}'")
                continue

            try:
                full_path = safe_abs(file_rel)
                if not os.path.isfile(full_path):
                    problems.append(f"{item_label} {hash_dict_name} 引用的文件不存在: {file_rel}")
                    continue
                hasher = hashlib.sha256()
                with open(full_path, "rb") as bf:
                    while chunk := bf.read(65536):
                        hasher.update(chunk)
                actual_hash = hasher.hexdigest()
                total_hashes_checked += 1
                if actual_hash.lower() != declared_hash.strip().lower():
                    problems.append(f"{item_label} {hash_dict_name} 文件哈希不匹配: {file_rel} (声明值={declared_hash}, 实算值={actual_hash})")
            except Exception as ex:
                problems.append(f"{item_label} {hash_dict_name} 校验文件异常 ({file_rel}): {ex}")

# 3) itemClass 覆盖 R1/R2/R3 三类
for req_class in ("R1", "R2", "R3"):
    if req_class not in seen_classes:
        problems.append(f"itemClass 未能覆盖残余分类: {req_class}")

# 6) 双向一致：A_RESIDUAL_REFERENCES.md 里出现的每个 itemId 都能在 JSON 找到，反之亦然
md_heading_ids = set(re.findall(r"^###\s+([A-Za-z0-9]+-[A-Za-z0-9\-]+)", md_text, re.MULTILINE))
md_all_ids = set(re.findall(r"\b(R[123]-[A-Za-z0-9\-]+)\b", md_text))

diff_md = md_heading_ids - seen_ids
diff_json = seen_ids - md_heading_ids

if diff_md:
    problems.append(f"Markdown 账目标题 (###) 包含但 JSON 缺失的 itemId: {sorted(diff_md)}")
if diff_json:
    problems.append(f"JSON 包含但 Markdown 账目标题 (###) 缺失的 itemId: {sorted(diff_json)}")

diff_mentions = md_all_ids - seen_ids
if diff_mentions:
    problems.append(f"Markdown 正文中提及但 JSON 缺失的 itemId: {sorted(diff_mentions)}")

# 7) lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md 含「## 4 未验」小节且非空
sec4_match = re.search(r"^##\s*4\s*未验[^\r\n]*", md_text, re.MULTILINE)
sec4_len = 0
if not sec4_match:
    problems.append("Markdown 缺失「## 4 未验」小节标题")
else:
    rest = md_text[sec4_match.end():]
    next_sec = re.search(r"^##\s+", rest, re.MULTILINE)
    sec4_content = rest[:next_sec.start()] if next_sec else rest
    sec4_stripped = sec4_content.strip()
    sec4_len = len(sec4_stripped)
    if sec4_len == 0:
        problems.append("Markdown 「## 4 未验」小节内容为空")

# 判定输出
if problems:
    print("GATE FAIL (内容不合格)")
    for prob in problems:
        print(f"  - {prob}")
    sys.exit(1)

print("GATE PASS")
print(f"  1) 交付件与解析:   {MD_REL} 与 {JSON_REL} 均存在且解析正常 (非空数组，共 {len(records)} 条)")
print(f"  2) 字段完整性:     全部条目均包含全部 13 个必需字段")
print(f"  3) 唯一性与覆盖度: itemId 全部唯一，itemClass 完整覆盖 {sorted(seen_classes)}")
print(f"  4) 档位与裁决枚举: tier 与 decision 取值全部合法")
print(f"  5) 文件哈希实算:   回文件系统实算比对 {total_hashes_checked} 次，SHA256 全部 100% 吻合")
print(f"  6) 账目双向一致:   Markdown (### 标题 {len(md_heading_ids)} 项) 与 JSON (共 {len(seen_ids)} 项) 完全双向一致")
print(f"  7) 未验小节校验:   「## 4 未验」小节存在且非空 ({sec4_len} 字符)")
sys.exit(0)
