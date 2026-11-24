# -*- coding: utf-8 -*-
import os, hashlib, datetime

PANEL = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md'
BA = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\MERGE_M81\BEFORE_AFTER.txt'
TZ = datetime.timezone(datetime.timedelta(hours=8))

EXPECTED_BEFORE_SHA = '369cef3c7cf80a53bf5dde70d2fd1db85474785a03fceb7bd014d266d614a2e3'

def state(path):
    st = os.stat(path)
    m = st.st_mtime
    iso = datetime.datetime.fromtimestamp(m, TZ).isoformat()
    b = open(path, 'rb').read()
    return {
        'mtime': m,
        'iso': iso,
        'bytes': len(b),
        'sha': hashlib.sha256(b).hexdigest(),
        'data': b,
    }

# ---- BEFORE ----
before = state(PANEL)
assert before['sha'] == EXPECTED_BEFORE_SHA, 'BEFORE sha mismatch: %s' % before['sha']
assert before['data'][:3] != b'\xef\xbb\xbf', 'unexpected BOM'
assert b'\r\n' not in before['data'], 'unexpected CRLF'
assert before['data'].endswith(b'\n'), 'unexpected missing trailing newline'

# ---- locate insertion point ----
text = before['data'].decode('utf-8')
lines = text.split('\n')   # trailing '' preserved because file ends with \n
# L187 (index186) = M80 header ; L193 (index192) = last M80 line ; L194 (index193) = M77 note
assert 'M80 名更正' in lines[186], 'L187 anchor failed: %r' % lines[186][:60]
assert '其余 8 行' in lines[192], 'L193 anchor failed: %r' % lines[192][:60]
assert 'M77 并表实算说明' in lines[193], 'L194 anchor failed: %r' % lines[193][:60]

DISCLOSURE = """\u003e 🔴 **M81 披露：`[已证]` 的证据可解析率只有 28.90%**
\u003e `EVID_RESOLVE` 对全量 1,654 行 `[已证]` 逐行解析 `evidence_path`：**`R_OK` 478 行（28.90%，至少一个路径解析到真实文件）／`R_MISSING` 374 行（22.61%，指针不完整）／`R_TRACE_ONLY` 802 行（48.49%，只有 `classification_trace`）／`R_EMPTY` 0 行**。
\u003e ⚠️ **两个纠正**：① 「892」是「**含有** `classification_trace`」的行数，按「**只含**」定义是 **802**；差的 90 行是混合记录且其它路径真实存在。② `R_MISSING` **不是证据消失**：361/374 可按后缀唯一还原，根因是 `evidence_path` 丢了卡目录前缀（`EVIDENCE/x.txt` 实际在 `S10-K2/EVIDENCE/x.txt`）；0 行彻底丢失。
\u003e 🔴 **第二层弱化**：`R_OK` 的 478 行虽是真实非空文件（最小 2,317 B、中位 26,496 B、0 空文件、抽 8 行复核通过），但**只落在 70 个不同文件上**，`all848.tsv` 一个文件覆盖 90 行；**文件名含该 entry 号的只有 4 行** ⇒「文件存在」成立，**「逐 entry 专属证据」多数不成立**。
\u003e ⇒ **引用 `[已证]` = 1,654 时必须带此限定**：它表示「按现行口径计分」，不等于「有可核证据」。若修复指针，可核上界到 478+361 = **839 行 / 50.72%**（推断值，非已证）。`classification_trace` 是分类追踪，不是四环证据。"""

new_lines = DISCLOSURE.split('\n')
assert len(new_lines) == 5, 'expected 5 disclosure lines, got %d' % len(new_lines)
assert all(x.startswith('> ') for x in new_lines), 'all disclosure lines must start with "> "'

# insert after L193 (index192) -> at index193
lines[193:193] = new_lines
new_text = '\n'.join(lines)
new_data = new_text.encode('utf-8')

# verify prefix/suffix untouched except insertion
assert new_data.replace(('\n'.join(new_lines) + '\n').encode('utf-8'), b'', 1) == before['data'], 'unexpected non-insertion byte change'

with open(PANEL, 'wb') as f:
    f.write(new_data)

# ---- AFTER ----
after = state(PANEL)
assert after['data'][:3] != b'\xef\xbb\xbf', 'unexpected BOM after'
assert b'\r\n' not in after['data'], 'unexpected CRLF after'
assert after['data'].endswith(b'\n'), 'unexpected missing trailing newline after'

# line numbers of disclosure in new file
nl = after['data'].decode('utf-8').split('\n')
first_idx = next(i for i, x in enumerate(nl) if 'M81 披露' in x)
last_idx = next(i for i, x in enumerate(nl) if 'classification_trace` 是分类追踪' in x)
disclosure_start = first_idx + 1
disclosure_end = last_idx + 1
assert disclosure_end - disclosure_start == 4, 'disclosure line span unexpected'

ba_text = f"""M81 BEFORE_AFTER — PANEL.md（仅追加 M81 披露；coverage.tsv 未改）
记录口径：BEFORE 采集于写入之前；AFTER 复算于写入之后。
本机时区：Asia/Shanghai (+08:00)。
BEFORE PANEL.md sha256 {before['sha'][:8]}… 与 MERGE_M80\\BEFORE_AFTER.txt 记录的 PANEL.md 改后 sha256 一致，确认起点无中间写者介入。
本轮唯一 COVERAGE 写者：agent-270；未 git commit；未碰 R14_COMMON / STATUS_BOARD / 台账 / BOARD_ARCHIVE / EVID_RESOLVE / 任何 R4_* / D47_SURFACE；未改 coverage.tsv；改动仅限 COVERAGE\\PANEL.md 与新建 MERGE_M81 目录。

========================================================================
FILE: COVERAGE\\PANEL.md
========================================================================
  BEFORE mtime  : {before['mtime']!r}  ({before['iso']})
  BEFORE bytes  : {before['bytes']}
  BEFORE sha256 : {before['sha']}
  AFTER  mtime  : {after['mtime']!r}  ({after['iso']})
  AFTER  bytes  : {after['bytes']}
  AFTER  sha256 : {after['sha']}
  DELTA  bytes  : +{after['bytes'] - before['bytes']}
  sha256 changed: {after['sha'] != before['sha']}

说明：PANEL.md 无 BOM / 仅 LF / 末尾换行保持；在 M80 披露（L187-193）之后、M77 并表实算说明之前新插入 M81 披露 5 行（新 L{disclosure_start}-{disclosure_end}）。除该 5 行插入外全文件字节不变（脚本已断言）。
"""
with open(BA, 'w', encoding='utf-8', newline='\n') as f:
    f.write(ba_text)

print('DISCLOSURE_LINES: L%d-L%d' % (disclosure_start, disclosure_end))
print('BEFORE bytes:', before['bytes'], 'sha256:', before['sha'])
print('AFTER  bytes:', after['bytes'], 'sha256:', after['sha'])
print('DELTA bytes: +%d' % (after['bytes'] - before['bytes']))
print('BEFORE_AFTER written:', BA)
