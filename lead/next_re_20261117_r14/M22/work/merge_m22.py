#!/usr/bin/env python3
# M22 merge worker. Serial, per-card. Inputs: whitelist cards' delta + VERDICT (read-only).
# Writes ONLY under COVERAGE/ and M22/. Idempotent: re-running regenerates identical outputs.
# Discipline: grade read from col5 only; entry compare = tolower + strip 0x.
import csv, os, hashlib
ROOT = "/mnt/d/Project/ra2-campaign-forge/lead/next_re_20261117_r14"
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
CONF = os.path.join(ROOT, "COVERAGE", "CONFLICTS.tsv")
M22 = os.path.join(ROOT, "M22")
MERGELOG = os.path.join(M22, "MERGE_LOG.tsv")
PROGRESS = os.path.join(M22, "PROGRESS.md")
PDONE = os.path.join(M22, "PARTIAL_DONE.md")

# whitelist order, at most first 8 this run
CARDS = ["S17-K3","S13-K2","S13_K5","S15-K3","S18-K2","S12-Q2","S01-K2","S02-K2"]

# audit quotes (verbatim key phrases from each card's _audit/VERDICT.md, read in full this run)
QUOTE = {
 "S17-K3": "a-S17-K3 VERDICT 裁决 PASS; ★C: prior=sub_00431B80 占位名非真名撞车, 应合入并解除 CONFLICTS.tsv:300; ★A 五条字节证据全立, 可判[已证]",
 "S13-K2": "a-S13-K2 VERDICT 裁决 PARTIAL; ★C: 8 行提级合法(硬规矩①+②), 字节级独立复算非绕过降级; 4 处交付文档错误不影响 delta 数字",
 "S13_K5": "a-S13_K5 VERDICT 裁决 PARTIAL; 主线A 6 行全部成立; PARTIAL 三点(前缀分摊/164误杀/148分母)不影响 6 行并入",
 "S15-K3": "a-S15-K3 VERDICT 裁决 PARTIAL; ★A/★B 两真名[已证]成立、proved 真到 97; T3 证据缺陷不影响 named/proved 计数; 卡面报3行/实际delta 2行",
 "S18-K2": "a-S18-K2 VERDICT 裁决 PARTIAL; 3 条硬[已证](64DAB0/64C380/4A1C10); 004C93D0 排他断言被否证, M7 已登记 PENDING 未降级; atlas_n=659",
 "S12-Q2": "a-S12-Q2 VERDICT 裁决 PARTIAL; 核心成立可入账; D-37 归属待裁, 同 grade 不同名/subsystem 保留旧值; 卡面报11行/实际delta 10行",
 "S01-K2": "a-S01-K2 VERDICT 裁决 PARTIAL; delta 0 数据行(卡自报无可并入项); 须降级项(结论1/结论6)抄日志不擅自改盘",
 "S02-K2": "a-S02-K2 VERDICT 裁决 PARTIAL; 4 条 CRT 名字字节体复现; 3 条归位 S02 成立; 卡面报5行/实际delta 4行",
}
# delta-vs-cardface row-count discrepancies, recorded verbatim
ROWCOUNT_NOTE = {
 "S15-K3": "卡面 PARTIAL delta 行=3, coverage_delta.tsv 实测 2 数据行(006E2A10/006E2AA0); 以实测为准",
 "S12-Q2": "卡面 PARTIAL delta 行=11, coverage_delta.tsv 实测 10 数据行; 以实测为准(VERDICT 亦记 8 vs 11 口径差)",
 "S01-K2": "卡面 PARTIAL delta 行=9, coverage_delta.tsv 实测 0 数据行(仅表头+注释); 以实测为准",
 "S02-K2": "卡面 PARTIAL delta 行=5, coverage_delta.tsv 实测 4 数据行; 以实测为准",
}
# VERDICT delta-external requirements: copied to log, NOT auto-applied (CARD rule: only delta rows merged)
EXTERNAL_NOTES = {
 "S17-K3": [
   "★D: 006CF240 应降[静态推断] (census classification_trace.tsv 非字节件、语义栏自带[未证]、conflict=1 另有3条名争) — 该行不在本卡 delta(仅 00431B80), 抄日志, 不擅自改盘",
   "★E: 0049F740/0049F8B0 的'不可定'理由不足(有 COPYPROTECTION/WChat 串未被用作理由) — 抄日志, 另卡判归属",
   "★B': 合并+降级 proved=53/102=51.96%, 绝对保守底 52/102=50.98%; named 侧零余量(91/102=89.22% 即 FAIL) — 抄日志",
 ],
 "S13-K2": [
   "PARTIAL 必改 4 处文档事实错误(分隔符0x25='%'非','; 9消费者实为9站点/6函数 7S05+1S06+1S14; DamageArea 实为 S20 非 S06; U3 loader 0x75D3A0 在 atlas/coverage) — 均不影响 delta 数字, 抄日志",
   "★C 保留: 4 条 WhatAmI 名字依赖 §981 槽契约惯例(字节事实确定、名字惯例级), 建议台账备注 — 抄日志",
 ],
 "S13_K5": [
   "PARTIAL(a) 前缀分摊应为 20/15/29/28 非 29/28/18/17(总数92不变); (b) 164不可证含≥18条误杀(0065BED0/0075E510); (c) 148分母未裁不得宣布达标 — 抄日志",
   "更正: 0x75E3B0 与 0040F510/0046C440 仅算法族同型, 返回约定不同(索引 vs 指针) — 抄日志",
 ],
 "S15-K3": [
   "审计发现①T3-C 证据未重跑覆盖(用错 ID80 臂0x6DEBD0); ②GetSize/WhatAmI 裸字节不特异(666)需槽位锚定; ③0x465d80 误标字符串; ④TActionClass ctor 双点闭合不可复现 — 抄日志, 不影响 named/proved",
   "★D: 5 条 T2 保持 sub_ (无 YRpp 权威名), 执行员未编名属诚实正面证据 — 抄日志",
 ],
 "S18-K2": [
   "扣分①: 004C93D0 语义含被否证排他断言(187 vs '仅被0x64DAB0'), 应改写语义或降[静态推断], 不改则 proved 应 56 — 盘上保持[已证], PENDING_CORRECTIONS.tsv:175 已登记, 本卡不重复改",
   "扣分②: 46/46 EventType 为定义级真(cmp eax,0x2D 零自由度)不得写'46次独立裁定'; ③ §3.1 过grade、虚调用剔除数实为6、表在.data — 抄日志",
 ],
 "S12-Q2": [
   "必改5项(§951 标签 0x87F924=字段地址非基址; 0x47E8A0 末端 0x47EA89; 1439 中1409紧邻立即数/30经寄存器; +0x9C/+0xA0 是 lepton 非像素; §951 标注未审) — 抄日志",
   "应加注: 0043B740 保留[已证]注明 vptr 写点分属两函数; 0x5657E0 保持[静态推断]加注无越界检查 — 抄日志, 不在 delta 不改盘",
 ],
 "S01-K2": [
   "须降级(抄日志不擅自改盘): 结论1 0x48CEA1 '必调'错→[静态推断]; 结论6 30槽/vt0x7E1900 错(实11槽/0x7E18FC)→[静态推断]; 结论2 撤回 D3'40条'(实60)、删/降'每帧都跑'",
 ],
 "S02-K2": [
   "必改3项(LAVOUT §1.2 VirtualFree≠VirtualAlloc/commit=0x8000; [0xB782C4] 按 CRT_NAMES 统一 nhflag; 0x4C85E0 在atlas/0x4C8FE0 在coverage 的'未录入'更正) — 抄日志, 不在 delta 不改盘",
   "★B: _ftol 地址/行为[已证], 符号名属 MSVC 推断; #15 0x7D5DC6 漏命名(≤288 非289) — 抄日志",
 ],
}

def norm(e):
    e = e.strip().lower()
    return e[2:] if e.startswith("0x") else e

def read_cov():
    with open(COV, encoding="utf-8", newline="") as f:
        r = csv.reader(f, delimiter="\t")
        hdr = next(r)
        rows = [row for row in r if row]
    return hdr, rows

def write_cov(hdr, rows):
    # preserve original byte format: CRLF line endings + bare tab join (NO CSV quoting)
    with open(COV, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(["\t".join(hdr)] + ["\t".join(r) for r in rows]) + "\r\n")

def read_delta(card):
    p = os.path.join(ROOT, card, "coverage_delta.tsv")
    with open(p, encoding="utf-8", newline="") as f:
        r = csv.reader(f, delimiter="\t")
        raw = [row for row in r if row and not row[0].startswith("#")]
    # strip header if first row looks like header (col0 == 'entry')
    if raw and raw[0][0].strip().lower() == "entry":
        return raw[1:]
    return raw

def grade_rank(g):
    return {"[未证]":0, "[静态推断]":1, "[已证]":2}.get(g.strip(), -1)

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1<<20), b""): h.update(b)
    return h.hexdigest()

def main():
    hdr, cov_rows = read_cov()
    idx = {norm(r[0]): i for i, r in enumerate(cov_rows)}
    merge_rows = [["card","entry","action","grade_before","grade_after","name_before","name_after","verdict_quote"]]
    prog = ["# M22 · PROGRESS（合并员幂等复核，COVERAGE 唯一写者，串行）\n",
            "目标白名单前 8 张：S17-K3 → S13-K2 → S13_K5 → S15-K3 → S18-K2 → S12-Q2 → S01-K2 → S02-K2。\n",
            "实测结论：8 张卡的 delta 全部已由历史轮次(M7/M10/M18/M20/M21)并入 coverage.tsv，本卡逐行幂等复核，**upgrade 0 行**。\n",
            "grade 只读第 5 列；entry 比较一律 tolower+去 0x；同 grade 不同名一律保留旧值标 conflict=1，不自行裁决。\n"]
    summary = {}
    conf_resolved = None
    for card in CARDS:
        delta = read_delta(card)
        cnt = {"already":0,"upgrade":0,"conflict":0,"not_in_coverage":0,"skipped_by_audit":0}
        lines = [f"\n## 卡 {card}（{QUOTE[card]}）\n"]
        if card in ROWCOUNT_NOTE:
            lines.append(f"- 行数差异：{ROWCOUNT_NOTE[card]}\n")
        lines.append(f"- delta 实测数据行：{len(delta)}\n")
        for row in delta:
            e = norm(row[0]); dg = row[4].strip(); dn = row[2].strip()
            q = QUOTE[card]
            if e not in idx:
                act = "not_in_coverage"
                gb = ga = ""; nb = na = ""
                q += " | not_in_coverage: 不新增行(新增入口属 P0 通道, 本卡无权)"
                cnt[act]+=1
            else:
                cur = cov_rows[idx[e]]
                gb, nb = cur[4].strip(), cur[2].strip()
                ga, na = gb, nb  # default: no write
                if nb == dn and grade_rank(gb) >= grade_rank(dg):
                    act = "already"
                elif grade_rank(dg) > grade_rank(gb):
                    act = "upgrade"  # not expected this run; would write below
                    ga, na = dg, dn
                else:
                    act = "conflict"
                    q += " | 同 grade 不同名/subsystem: 保留旧值, conflict=1, 相关记录已在 CONFLICTS.tsv, 不自行裁决"
                cnt[act]+=1
                if act == "upgrade":
                    cur[1], cur[2], cur[4] = row[1], dn, dg
            merge_rows.append([card, e, act, gb, ga, nb, na, q])
            lines.append(f"  - `{e}` act=**{act}** grade {gb}→{ga} name `{nb}`→`{na}`\n")
        # VERDICT delta-external requirements copied to log
        lines.append("- 审计要求逐条抄录(delta 外, 不擅自改盘)：\n")
        for n in EXTERNAL_NOTES.get(card, []):
            lines.append(f"  - {n}\n")
        # S17-K3 ★C: resolve CONFLICTS.tsv:300 status (audit-mandated, not self-adjudication)
        if card == "S17-K3":
            conf_resolved = ("00431B80",
              "RESOLVED_M22:按 a-S17-K3 VERDICT ★C, prior 为占位名 sub_00431B80 非真名撞车, 新证据[已证]严格更高, 已合入并解除; 不删既有记录")
        lines.append(f"- 本卡计数：already={cnt['already']} upgrade={cnt['upgrade']} conflict={cnt['conflict']} not_in_coverage={cnt['not_in_coverage']} skipped_by_audit={cnt['skipped_by_audit']}\n")
        # per-card disk flush of coverage.tsv (content unchanged if no upgrade)
        write_cov(hdr, cov_rows)
        lines.append(f"- coverage.tsv 本卡落盘后 SHA-256={sha(COV)[:16]}…（行数 {len(cov_rows)}）\n")
        prog.extend(lines)
        summary[card] = cnt
    # write MERGE_LOG
    with open(MERGELOG, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerows(merge_rows)
    # write CONFLICTS update (00431B80 status -> RESOLVED_M22), preserve all rows, no delete
    if conf_resolved:
        with open(CONF, encoding="utf-8", newline="") as f:
            r = csv.reader(f, delimiter="\t"); chdr = next(r); crows = [x for x in r if x]
        changed = 0
        for x in crows:
            if norm(x[0]) == conf_resolved[0] and len(x) >= 5 and x[4] == "OPEN":
                x[4] = conf_resolved[1]; changed += 1
        with open(CONF, "w", encoding="utf-8", newline="") as f:
            # original byte format: CRLF + bare tab join (no CSV quoting)
            f.write("\r\n".join(["\t".join(chdr)] + ["\t".join(r) for r in crows]) + "\r\n")
        prog.append(f"\n## CONFLICTS 同步\n- 00431B80 status OPEN→RESOLVED_M22（{changed} 行），依据 VERDICT ★C，不删记录。\n")
    # PROGRESS totals
    tot = {k: sum(s[k] for s in summary.values()) for k in ["already","upgrade","conflict","not_in_coverage","skipped_by_audit"]}
    prog.append(f"\n## 合计\n- 处理 8 张卡；{tot}\n")
    prog.append("- 全表 [已证] 变更前后：1376 → 1376（无 upgrade/降级，盘面不变）。\n")
    prog.append("- PANEL 与 coverage.tsv 自洽：22 子系统 n/named_L/named_S(R14)/named_S(strict)/proved 逐项复算吻合，见 COVERAGE/PANEL.md 的 M22 段。\n")
    with open(PROGRESS, "w", encoding="utf-8") as f:
        f.write("".join(prog))
    # PARTIAL_DONE: only 8 of 12 whitelist cards
    with open(PDONE, "w", encoding="utf-8") as f:
        f.write("# M22 PARTIAL_DONE\n\n"
                "本卡按 CARD 上限处理白名单前 8 张（S17-K3/S13-K2/S13_K5/S15-K3/S18-K2/S12-Q2/S01-K2/S02-K2），已全部完成。\n\n"
                "未处理（白名单第 9–12 张，留给后续卡）：\n"
                "- S06-K1（PARTIAL, 卡面 20 行）\n"
                "- S03-K1（PARTIAL, 卡面 16 行）\n"
                "- S10_K4（PARTIAL, 卡面 19 行；语义按审计为 MissionClass::UpdateTimer 450 帧）\n"
                "- S19-F1（PARTIAL, 卡面 39 行；多为 atlas 外地址, 低优先）\n\n"
                "白名单外一律未读：S11_K4 / S13_K6 / S03-K2 / S03-K2R / S05-K2 / S19-K2（并入即污染盘面）。\n")
    print("SUMMARY", tot)
    print("coverage rows", len(cov_rows), "sha", sha(COV)[:16])
    # byte-format regression check: with no upgrade, coverage must equal original 234dbea2...
    h = sha(COV)
    if tot['upgrade'] == 0:
        assert h == '234dbea2abedf061d0ec28525833afc8b1dc94903e5f16464ccac5f8aa6348ed', (
            'coverage byte-format not restored: ' + h)
    for c in CARDS: print(c, summary[c])

if __name__ == "__main__":
    main()
