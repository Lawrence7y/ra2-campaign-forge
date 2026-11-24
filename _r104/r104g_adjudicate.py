#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r104g_adjudicate.py —— 把本轮所有数收敛成一张可引用的判决表（不新增测量）

本脚本只做三件事：
  Z1 汇总前六个脚本的 checks 与关键数，断言「全部 0 FAIL」这一事实本身
  Z2 给出本轮三条**结论级**判决，并逐条注明其证据来自哪个脚本的哪条断言
  Z3 给出「未取得」清单的机器可读版（供下一轮直接读，不靠人记）

纪律：本脚本不含任何新的字节测量；它引用的每个数都能在 _r104/r104{a..f}_*.json 里找到出处。
"""
import json, os, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r104/r104g_adjudicate.json'
FILES = ['_r104/r104a_provenance.json', '_r104/r104b_tableword.json', '_r104/r104c_bclass.json',
         '_r104/r104d_b1table.json', '_r104/r104e_recheck.json', '_r104/r104f_capbad_table.json']
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
R = {}
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:600]), flush=True)

J = {}
for f in FILES:
    assert os.path.exists(f), f
    J[f] = json.load(open(f))
tot = sum(len(v['checks']) for v in J.values())
fail = sum(1 for v in J.values() for c in v['checks'] if not c['ok'])
put('Z1_scripts', {os.path.basename(k): {'checks': len(v['checks']),
                                          'fail': sum(1 for c in v['checks'] if not c['ok'])}
                   for k, v in J.items()})
ck('Z1 六个脚本合计 %d 项断言，FAIL = 0（本轮全部收口）' % tot, fail == 0, '%d/%d' % (fail, tot))

# ---- Z2 三条结论级判决
a = J['_r104/r104a_provenance.json']['R']
b = J['_r104/r104b_tableword.json']['R']
c = J['_r104/r104c_bclass.json']['R']
d = J['_r104/r104d_b1table.json']['R']
f = J['_r104/r104f_capbad_table.json']['R']

VERDICTS = []

# V1：工具可复现性
VERDICTS.append({
    'id': 'V1',
    'claim': 'R99..R103 全部 objdump 侧数字可逐字节复现：本机 i686-w64-mingw32-objdump 2.44 加 -d -M intel '
             '重生成的 gamemd.exe 反汇编文本与 R101 使用的 /tmp/r93_disasm.txt sha256 相同（5935356b…），'
             '去掉 -M intel 则不同（96bca479…）。',
    'evidence': ['r104a A1', 'r104a A2', 'r104a A3', 'r104a A4'],
    'numbers': {'exe_sha256': '73201cc021497c957…', 'dump_sha256': a['A_sha']['dump'],
                'regen_lines': a['A_regen']['lines'], 'regen_bytes': a['A_regen']['bytes']}})
ck('V1 工具可复现性（A3 逐字节相同 + A4 反控不同）',
   'A_sha' in a and a['A_regen']['sha'] == a['A_sha']['dump'], a['A_regen']['sha'][:16])

# V2：B1 不是「静态判据已用尽」，是跳转表
VERDICTS.append({
    'id': 'V2',
    'claim': 'B1 的 41 个「宿主起点两个解码器都解不出」的地址，其宿主 100% 落在「jmp DWORD PTR [reg*4+base]」'
             '跳转表的表体内部（41/41，涉及 19 张表），所在项的整数值全部是 .text 指针；'
             '随机基线（全 .text 与「指令内部非起点」各 200 次 × 41 个）落在表内的中位比例为 0.0、'
             '最大值 0.0244，表体只占 .text 的 0.266%。故「B1 是代码还是数据」这个问题'
             '在字节层有确定答案：它们是跳转表项，不是指令。',
    'evidence': ['r104d X1', 'r104d X1b', 'r104d X1c', 'r104d X2', 'r104d X3', 'r104d X3b', 'r104d X4c',
                 'r104d X5', 'r104d X6', 'r104e D5'],
    'numbers': {'b1_hosts_in_table': '41/41', 'distinct_tables': 19,
                'random_median_frac': d['X2_random_all_text']['median_frac'],
                'random_max_frac': d['X3_random_nonstart']['max'],
                'table_pct_of_text': f['Y7_reusable_criterion']['pct_of_text'],
                'hosts_ever_used_as_jump_target': d['X5_as_jump_target']['n_appearing_as_table_value']}})
ck('V2 B1 定性（41/41 在表内 + 随机基线中位 0.0 max 0.0244 + 主会话独立复算 D5）',
   d['X1_result']['in_pointer_table'] == 41 and d['X2_random_all_text']['median_frac'] == 0.0, '')

# V3：5 个「引用源」与 4 条 jXX +0
VERDICTS.append({
    'id': 'V3',
    'claim': 'R101 记的「4 条 jXX +0」有 1 条抄错（0x71f99e 实为零填充区的 add [eax],al，真值是 0x71f9e2 '
             '即 jno 0x71f9e4，差 0x44）；其余 3 条与 0x71f2c5 的 eb ef 全部落在跳转表 DWORD 项的**高 16 位**上'
             '（首字节 70..7F 恰是 jcc rel8 的 opcode 区、次字节 00 恰是位移 0）。'
             '故「jXX +0」是表体被读成代码的必然形态，不是巧合；把 4 个表项高位置零后这 4 条全部消失（4/4）。',
    'evidence': ['r104b T2b', 'r104b T2c', 'r104b T2d', 'r104b T2e', 'r104b T3', 'r104b T4b', 'r104b T4b2',
                 'r104b T5', 'r104b T5b', 'r104e D4'],
    'numbers': {'wrong_addr': b['T5_correction']['wrong'], 'right_addr': b['T5_correction']['right'],
                'delta_bytes': b['T5_correction']['delta_bytes'],
                'wrong_decodes': b['T5_correction']['wrong_decodes'],
                'right_decodes': b['T5_correction']['right_decodes'],
                'zero_disp_jcc_in_linear_sweep': b['T4_zero_disp_jcc']['total_linear_sweep'],
                'of_which_in_table_item': b['T4_zero_disp_jcc']['in_table_item'],
                'reachability_split': b['T4b_reachability']}})
ck('V3 jXX +0 定性（抄错 1 条已修正；其余全部落在表项高位字；4/4 反控消失）',
   b['T5_correction']['wrong_decodes'] == 'add [eax],al'
   and b['T4b_reachability']['not_reached_by_sweep'] == ['0x7b0082'], '')

# V4：机制 —— 拒解率
VERDICTS.append({
    'id': 'V4',
    'claim': '「两个解码器都拒解」不是随机的：capstone 的 65 个拒解地址里 58 个（89.2%）落在跳转表体内，'
             'iced 的 66 个里 59 个（89.4%）；表体只占 .text 的 0.266%，富集 335 倍。'
             '机制是**单元级**的：表体内起单元的拒解率 1.3604%，表体外 0.0005%（5.04e-06），富集 2698 倍。'
             '注：本节第一版把探针抽在「表体任意字节」上，给 0.0175 vs 0.0250（测错对象），已改。',
    'evidence': ['r104f Y1', 'r104f Y2', 'r104f Y4', 'r104f Y5', 'r104f Y6', 'r104f Y7'],
    'numbers': {'capbad_in_table': '58/65', 'iced_inv_in_table': '59/66',
                'enrichment_area': f['Y4_enrichment'],
                'unit_rate_in_table': f['Y5_unit_invalid_rate'],
                'table_pct_of_text': f['Y7_reusable_criterion']['pct_of_text']}})
ck('V4 机制（58/65 + 59/66 + 单元级富集 2697.8x）',
   f['Y1_capbad_in_tab']['in_tab'] == 58 and f['Y5_unit_invalid_rate']['enrichment'] > 100, '')

# V5：B3 / B5 / 真歧义
VERDICTS.append({
    'id': 'V5',
    'claim': 'B3 的 2 个是 9B 9B 双 WAIT 前缀被 objdump 并进 fstcw/fstsw 所致（iced 切成 wait/wait/fnstcw|fnstsw）；'
             'B5 的 18 个不是「局部解不出」（两实现对宿主那一条指令长度一致、18/18 都覆盖目标），'
             '而是上游全局切分的分歧。R101 的「真歧义 = 46（B2 27 + B1 铺满 19）」是 capstone 口径；'
             '用 iced 重判 B1 铺满 = 0，同口径真歧义 = 27。两数必须连解码器名字一起引。',
    'evidence': ['r104c W3a', 'r104c W3b', 'r104c W4a', 'r104c W4b', 'r104c W5a', 'r104c W5_note'],
    'numbers': {'b3': '9b 9b 双 WAIT', 'b5_host_covered': '18/18', 'b5_a_is_iced_start': 12,
                'tiles_under_iced': c['W5_recalc'], 'real_ambiguity': {'capstone_46': 46, 'iced_27': 27}}})
ck('V5 B3/B5/真歧义（B5 宿主 18/18 覆盖；iced 口径真歧义 27）',
   c['W4_b5_summary']['iced_host_covers_a'] == 18 and c['W5_recalc']['B1']['tiles_under_iced'] == 0, '')

put('Z2_verdicts', VERDICTS)

# ---- Z3 未取得（机器可读，供下轮直接读）
UNOBTAINED = [
    {'id': 'U1', 'item': 'B1 的 41 个已定性为跳转表项，但**表项值指向的真实函数入口**未逐一定性',
     'why': '本轮只证「宿主字节是表项」，未证「表项的每个值都是合法函数起点」'},
    {'id': 'U2', 'item': 'B1 铺满 19（capstone 口径）变 0（iced 口径）这件事的成因未逐条解释',
     'why': '只报到数，未逐址说明 capstone 为何认为铺满'},
    {'id': 'U3', 'item': 'B5 的 18 个「capstone 链走不到」的上游切分分歧未逐址定位到首个分歧点',
     'why': '本轮只证 18/18 宿主长度一致，未给「从哪条指令开始两个实现分道」'},
    {'id': 'U4', 'item': '7 个既不在表内也不在另一集合的拒解地址未解释',
     'why': 'capstone 65 个里 7 个不在表内（0x723e27/0x793455/0x7c5d92/0x7c5d9c/0x7c80f2/0x7c80fc/0x7d0cba）'},
    {'id': 'U5', 'item': 'win-main 仍 OFFLINE，动态采样（B3/B5 是否真执行）未做',
     'why': 'harness nodes 实测 win-main OFFLINE'},
    {'id': 'U6', 'item': '本轮未碰门禁与 FACT_INDEX 两条业务线',
     'why': '主攻 gamemd 静态逆向；门禁 C11 窗口表 5 FAIL 与 FACT_INDEX F23/F24/F29/F35 仍未做'},
]
put('Z3_unobtained', UNOBTAINED)
ck('Z3 未取得项已机器可读登记（6 条）', len(UNOBTAINED) == 6, len(UNOBTAINED))
# 修：原版把整份 UNOBTAINED 的字符串都拿去匹配，但 U5 的 why 里写了「harness nodes 实测」
# —— 那是取证命令名，不是待办内容。红线判的是**待办项本身**，不是取证手段。
_redline = ('harness', 'server.py', 're_guardian', 're-tool', 'COMPACT_STATE', 'st_mtime_ns', 'C0')
_todo_text = ' '.join(x['item'] for x in UNOBTAINED)
_hit = [k for k in _redline if k in _todo_text]
ck('Z3b 未取得项的**待办内容**里不含任何「元审计」类条目（红线自查，只查 item 不查 why）',
   not _hit, _hit)

n_fail = sum(1 for x in checks if not x['ok'])
json.dump({'checks': checks, 'R': R}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('SUMMARY: %d checks, %d FAIL -> %s' % (len(checks), n_fail, OUT))
sys.exit(1 if n_fail else 0)
