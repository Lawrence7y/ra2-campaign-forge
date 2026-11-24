# R94-T2 门禁窗口修复方案的反伪造审计（审计员卡）

## 0 硬约束（违反即作废）
- 只读 lead/ 下 live 文件，禁止写入或修改 lead/ 下任何文件。
- 只在 _r94/_audit/ 写产物；产物上限 20 MB；卡面与产物不得出现反引号。
- 不得复制 live 树。

## 1 背景（事实，非结论）
门禁 lead/next_re_20261117_r14/check_disc.py 的 C11 项调用 recheck_verify.py 校验 DISC_RECHECK.tsv 第 7 列声明「有（后续轮回跑）」的 30 行。当前结果：
  C11 ok=0 fail=5 frozen-unverifiable=12 claims-none=13，exit 1
5 个 FAIL 是 id 3 4 22 27 28，它们产物的自描述行写 round=R55、at=17:39:19 或 17:40:02，而 recheck_verify.py 内嵌窗口表 _ROUND_ROWS 的 R55 = [17:41:46, 17:46:59)。

拟议修复（主会话在 R94 拟采用，请审计它）：把窗口语义从
  旧: 窗口(N) = [T(N), T(N+1))
改为
  新: 窗口(N) = [T(N-1), T(N))
T(N) 取 R17_LEAD_BASELINE 里 before_rN_HHMMSS.md 的时分秒；缺失端点的轮次标记为不可判定（fail-closed，不合并）。

## 2 你要独立做的事（只做这一件，做深）
对「新语义」做反伪造审计，逐项给结论 PASS 或 FAIL 并给实测数字：

1. 判定翻转面：用新语义重算 DISC_RECHECK.tsv 全部 30 行的 C11 结果（可 import recheck_verify，也可自己重写窗口计算；但必须自己算一遍，不许直接引用主会话数字）。报：ok / fail / frozen-unverifiable / claims-none 四个数与翻转的具体 id 清单。
2. 必须检查的反向风险：DISC_UNVERIFIABLE.tsv 里登记的 12 个冻结 id（1,2,5,6,7,8,9,10,18,20,24,25）在新语义下是否会出现「自描述行变 PASS」的情况。若出现，按 check_disc.py 的 R87-T2 规则那是 FAIL，必须报出来。
3. 放宽不可区分性：把窗口放宽到全天 00:00:00-23:59:59 重算一遍。报哪些行通过。若与第 1 步完全相同，明确写出「门禁层分不清重映射与放宽」。
4. 相邻窗口串味：在新语义下，取 R55 窗口外但 R54 窗口内 / R56 窗口内 的时刻，构造自描述行，看是否 FAIL。若相邻窗口能串过，说明新语义仍在放宽，必须报出。
5. 端点缺失面：r41 无主快照。新语义下哪些轮次窗口缺端点、受影响的 DISC_RECHECK 行是哪些 id。
6. 自证循环面：recheck_verify.py 的 --self-test 是否会把「窗口表被改成任何包含样本的区间」都判 PASS？构造一次实验证明（只在内存或 _r94/_audit 下的临时副本上做，绝不改 live）。

## 3 交付
- 脚本 _r94/_audit/audit_win.py（带断言，正控反控各至少 2 项）
- 结果 _r94/_audit/audit_win.json
- 日志 _r94/_audit/audit_win.log
- 回件正文必须逐项列出第 2 节 1-6 的结论与数字，并单独写一段「这个修复能被怎样伪造」，不许写成通过。
- 用 sha256 前后对比证明你没有改任何 live 文件。
