# -*- coding: utf-8 -*-
"""主体识别三方案修复件（可整段粘贴进 GATE_CODE）。
验证见 _si_exploit_sim.py；诊断全文见 GATE_SUBJECT_ID_FIX.md（同字节副本 _si_SUBJECT_ID_DEFECT.md）。
"""
from pathlib import Path


class GateFail(Exception):
    """主体识别失败——门禁必须 FAIL（fail-closed），禁止静默降级回启发式挑件。"""


def pick_deliverable_explicit(wd, expected_name):
    """方案A（首选）：门禁按任务约定显式命名主件；缺件即 FAIL。

    适用：任务下发时已约定主件文件名（每发 ASK 均应写明，如本发的 GATE_SUBJECT_ID_FIX.md）。
    风险：子代理漏写/改名 → FAIL（安全侧失败，重跑即可）。
    本任务自身门禁 dwfrun-a7468d6e 已采用此方案（_si_gate_self_extracted.py:5-6）。
    """
    p = Path(wd) / expected_name
    if not p.is_file():
        raise GateFail("主交付件未按约定命名 " + str(expected_name))
    return p


def pick_deliverable_unique_bare(wd):
    """方案B（次选）：排除下划线前缀中间稿，要求恰好一份非下划线 md；0 或 ≥2 即 FAIL。

    适用：约定「一域一主件；子代理中间稿一律 _ 前缀」且该约定写入派发纪律后。
    风险：多主件合法的域会 FAIL（现状统计：lead/ 下 112 个目录 bareCount>1，
    如 goal2_rc4_fixv5_20261022 bareCount=31）——须先成文约定或按域白名单放行。
    遍历有界：glob('*.md') 仅单层。
    """
    cands = sorted(Path(wd).glob("*.md"))
    bare = [p for p in cands if not p.name.startswith("_")]
    if not bare:
        raise GateFail("写域内无非下划线 md 主件（全部为中间稿？）")
    if len(bare) > 1:
        raise GateFail("非下划线主件不唯一: " + repr([p.name for p in bare]))
    return bare[0]


def pick_deliverable_largest_bare(cands):
    """方案C（兜底，旧门禁最小补丁）：沿用旧代码的 cands 列表，但
    先滤掉下划线前缀件，再要求滤后恰好一份；不满足即 FAIL。
    滤后唯一时与大小无关——max 不再参与主体识别，仅剩余内容检查。

    适用：最小改动落地（旧门禁只改 2 行）；其余同方案B。
    """
    bare = [p for p in cands if not Path(p).name.startswith("_")]
    if not bare:
        raise GateFail("写域内无非下划线 md 主件")
    if len(bare) > 1:
        raise GateFail("非下划线主件不唯一: " + repr([Path(p).name for p in bare]))
    return bare[0]


def overshadow_warning(wd, chosen):
    """加固（非门禁项）：主件被更大的下划线中间稿遮蔽时返回告警清单，留审计痕。"""
    c = Path(chosen).stat().st_size
    return [p.name for p in sorted(Path(wd).glob("*.md"))
            if p.name.startswith("_") and p.stat().st_size > c]
