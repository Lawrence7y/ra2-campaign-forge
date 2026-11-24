# -*- coding: utf-8 -*-
"""M61 复核：证明 PANEL.md 相对改前只发生了三处字面编辑，
主面板（覆盖面板 L53-L77）与严格双列表（L91-L140）逐字节未变。
方法：把当前文件在内存中逆向还原三处编辑，其 sha256 必须等于改前 sha256。
只读，不写任何项目文件。
"""
import hashlib, sys
sys.stdout.reconfigure(encoding="utf-8")

P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md"
BEFORE_SHA = "065F6F6C34C3C1C639028393A55F0BB7AD51DC86DF927B9DF042E2DC8D6AF79A"

with open(P, "r", encoding="utf-8") as f:
    cur = f.read()

rev = cur
# 逆向 1b：去掉追加的 M61 备注
note = "；M61 按盘上重算更正：1,479/1,474 为 M55 后截面，落后 M56 +2、M58 +8、M59 +7；现值为 1,496/1,490（atlas 外 6）"
assert rev.count(note) == 1, "note count != 1"
rev = rev.replace(note, "")
# 逆向 1a：数值还原
assert rev.count("**1,496 / 1,490** | M55 并表 19 行原地升格") == 1
rev = rev.replace("**1,496 / 1,490** | M55 并表 19 行原地升格",
                  "**1,479 / 1,474** | M55 并表 19 行原地升格")
# 逆向 2：去掉 M61 标记行 + 其后新增的空行
marker = "> ⚠️ **M61 标记**：本表为 M47 时点快照，其中 S09 / S15 / S16 的 proved 三格已被后续并表的现值覆写（现显示 114 / 106 / 47，M47 时点应为 106 / 101 / 46），**不可作为历史依据引用**。当前权威值见上方主面板与严格双列表（S09 114/97、S15 106/53、S16 47/21）。\n\n"
assert rev.count(marker) == 1, "marker count != 1"
rev = rev.replace(marker, "")

rev_sha = hashlib.sha256(rev.encode("utf-8")).hexdigest().upper()
print("逆向还原后 sha256 =", rev_sha)
print("改前 sha256        =", BEFORE_SHA)
print("完全一致           =", rev_sha == BEFORE_SHA)

# 若还原一致，则当前文件 = 改前 + 三处编辑，其它任何行都未变。
# 额外给出主面板 / 严格双列表两个区块的 sha256（当前 vs 还原），逐块证明未变。
if rev_sha == BEFORE_SHA:
    def block_sha(text, start, end):  # 1-based inclusive line numbers
        lines = text.split("\n")
        seg = "\n".join(lines[start-1:end])
        return hashlib.sha256(seg.encode("utf-8")).hexdigest().upper(), seg
    for name, s, e in [("主面板(覆盖面板 L53-L77)", 53, 77),
                        ("严格双列表(L91-L140)", 91, 140)]:
        hc, sc = block_sha(cur, s, e)
        hr, sr = block_sha(rev, s, e)
        print(f"{name}: 当前sha={hc}")
        print(f"{' '*(len(name)+1)}还原sha={hr}  相同={sc==sr}")
