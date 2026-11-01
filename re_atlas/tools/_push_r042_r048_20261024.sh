#!/usr/bin/env bash
# =============================================================================
# owner 通道（RE-ATLAS R-042..R-061 合并补推）
# 用户令「全部上传 GitHub」（2026-10-24，两次）。会话内提交动作被 ZCode Bash 层
# L3 钩子（整树扫描，D-07 B 案的原生 git 门禁不让位于该层）拦截已第 25 次实测；
# 本脚本给 **用户自己的终端** 执行（现场 git 层 = GOAL-3T 线 `mimosa git-gate
# install` 落地的 pre-commit/pre-push diff-only 门禁，双对照已实证 §436/§437；
# staged 集只含 re_atlas/ ⇒ 他线 high 不再挡本线）。
# 纪律：代理会话不得运行本脚本（绕钩子=--no-verify 等价物，§415/D-07 禁令）。
# 详见 re_atlas/LEDGER.md §5、lead/PENDING_DECISIONS.md D-07 已裁决记录。
# 多会话索引安全：[4] 用显式路径提交，只纳入本线路径，别的会话暂存的 lead/ 文件
# 不受影响也不被带走（教训源：R-056 轮 60→191 件跳变）。
# =============================================================================
set -euo pipefail
cd "D:/Project/ra2-campaign-forge"

echo "== [1] 同步远端（rebase autostash；本线暂存件受保护）=="
git pull --rebase --autostash

echo "== [2] 显式路径重加本线 132 件（tmp_qwen_grade 除外；多会话可能重置索引）=="
git add -- re_atlas ":(exclude)re_atlas/tmp_qwen_grade"

echo "== [3] 门禁自检：本线暂存集零二进制/零 cpp·h（按本线路径作用域检查）=="
BIN=$(git diff --cached --name-only -- re_atlas | grep -Ei '\.(exe|dll|bin|obj|lib|dmp|mix|png|jpg|so|cpp|hpp|cc|cxx|h)$' || true)
if [ -n "$BIN" ]; then
  echo "ABORT: 本线暂存集含二进制/源码件："; echo "$BIN"; exit 1
fi
echo "OK: $(git diff --cached --name-only -- re_atlas | wc -l) 件本线文本交付（预期 >=132）"

echo "== [4] 合并提交（十九轮欠账收口 + R-054..R-061；显式路径只带本线）=="
# 注：本轮**不带** lead/PENDING_DECISIONS.md —— 该文件工作区里另有他会话未提交的
# 大重构（115 行 D-06/07/08/09 全文被修剪为摘要），按多会话纪律不得替他们把删除
# 带进本线提交。D-06 的执行登记已在 LEDGER R-060 §5 完成；该文件的删除归监督线自提。
git commit -m "re-atlas: R-042..R-061 合并补推——十九轮欠账收口 + R-055..R-058 INI 查找族收束（孪生/二分核/teardown 收口、容器结构坐实、RTTI 链 vtable->COL->TD 归属定谳 CCINIClass:INIClass、闭 L-25、定名 INISection、孪生协议不对称 twinA 13/22 vs twinB 0/20）+ R-059 G-79 对账落地（存量套件 6 条零杀手补齐、恒真式两类改写 G-80、见证↔实例否定式、0x7E1AF4=析构专用表）+ R-060 D-06 C 案执行（fn_walk/fn_census/门禁修到对齐读法、自证 LOWER 12,792/UPPER 13,683/4.28%..4.07%、UPPER 勘误 13,682→13,683、560 幻影双向变异可杀 G-81、区分性对 C11/C12、fn_census 静默丢 83% 修复、G-82 自我误判入册；D-02 随自动落 A 定稿）+ R-061 C26-04 见证 this 上行（★推翻 R-059 §2③：分支图闭包重做 13/13=mov esi,[reg+8] 包装对象、容器=[[this+8]+0x2C]；5 宿主 global-direct 直方图钉值/7 宿主 UNKNOWN 保留；工厂 0x52CB90 钉；门禁 194/194；round-5 变异 194 例全杀→冻结候选 mutate_r061_gate.py；辅批次 1 R-053/054/055 G-79 收官 17/17·27/27·20/20；辅批次 2/3 收官 R-047..R-055 全口径——R-050 12/12·R-047 12/12·R-048 13/13 加尾段，R-051 X7/X8 补 M13/M14 14/14，R-052 Y2/Y4 补 M14/M15 + attestation 时序修 PRISTINE 15/15，R-049 N/A 如实登记；域外 5 件同 pattern 移交零改动；G-83/84/85）+ 新坑 G-61..G-85" -- re_atlas

echo "== [5] 推送（分支级连带待推提交，同仓在册接受）=="
git push origin main

echo "== [6] 终验：同步态应 0/0；推送区间零二进制 =="
git rev-list --left-right --count HEAD...origin/main
git log --oneline -1
echo "DONE. 若 [1]/[4]/[5] 任何一步报 Mimosa L3，说明钩子已覆盖终端层——停下别重试，回会话报告即可。"
