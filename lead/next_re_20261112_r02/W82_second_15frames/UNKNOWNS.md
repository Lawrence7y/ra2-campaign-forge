# W82 · UNKNOWNS（未定谳 / 待运行验证）

## U1 · +90 的最终归属（本卡唯一未闭合环节）
- 已证 `[本次实测]`：`timer.started = [0xA8ED84] @ 装弹`（`0x726431`），`duration = N×15`（`0x72643F`），
  求值 `fired ⟺ frame − started ≥ duration`（`0x71EC33`）。实测律 `冻结 frame = 15N + 90`（W79 `[转引]`）。
- 两个候选读法（都与全部实测点相容）：
  - **(a) 装弹发生在帧 90**：触发器实例化（`0x725FA0` ← `0x6E4F38`/`0x6C1ACE`/`0x726630`）或某次
    `0x726400` 重装弹发生在场景帧复位（`0x68466B`/`0x686765`）后的第 90 帧 ⇒ 命中恰在 `15N+90`。
  - **(b) 装弹在帧 0**：命中在 `15N`，其后有 90 帧固定胜利转场后才冻结 frame。
- 静态未定谳原因：触发器实例化相对帧复位的先后顺序、以及胜利→结算屏转场是否为固定 90 帧，
  都是运行时时序问题；静态链只能证到 `started = frame@装弹`。
- **判别观察点（真机一行即可裁决）**：进图后 2 秒读
  `started = *(DWORD*)(Trigger+0x34)`、`duration = *(DWORD*)(Trigger+0x3C)`：
  - (a) ⇒ `started≈90, duration=15N`；帧冻结时 `frame−started == 15N`。
  - (b) ⇒ `started≈0, duration=15N`；帧冻结时 `frame−started ≈ 15N+90`。
  Trigger 指针可经 TriggerTypeClass 链（`[type+0xAC]` 首事件反查）或触发器列表 `0xA8EAEC` 取。

## U2 · 事件 type 0..12 的求值器未定位
- step3 T2 找到的两个 `cmp eax,0xc` 候选（`0x6173EB`：`lea eax,[esi-2]`；`0x61AE74`：`lea eax,[ebx-0x4A7]`）
  索引基与事件语义不符，未确认是触发器事件分发（可能是其它枚举的 dispatcher）。不影响本卡判定
  （13 在 `0x71E940` 的分发已闭合），留给后续卡补全 0..12 段。

## U3 · `[Scen+0x352C]`（type 45/46 使用）语义未定谳
- 全镜像 15 处引用：ctor 清零（`0x6838D9`）、INI 读侧写（`0x68A85C`）、三处向 `[Scen+0x3530]`
  收敛的调整（`0x55B45E/0x55B470/0x55B490/0x55B4AE`，随后 `mov byte [Scen+0x34AB],1`）、
  求值器两处比较。**无逐帧 inc 写点** ⇒ 不是活动时钟，更像静态配置/缓慢调整量；
  精确语义（par time？难度调整量？）未定。

## U4 · `[Events]`/`[Actions]` INI 解析侧未定位
- `"Events"`/`"Actions"`/`"Triggers"` 字符串在 .text 内 0 处 imm32 引用（走节注册表或其它路径）。
  事件节点布局 `{+0x28 next, +0x2C type, +0x30 param1, +0x34 param2}` 由**求值器与装弹器两侧读取
  一致性**反推（`1,13,0,N` → type@+0x2C、N@+0x34 与 ra2forge `(13,(0,seconds))` 序列化吻合）；
  解析函数本体留待后续卡。

## U5 · Spring 宿主上游链未上溯到主循环
- `0x6E5414`（Spring 唯一调用点）宿主 ~`0x6E53A0` 遍历 `[ebp+0x28]` 触发链，全局闸 `[0xA8ED6B]`；
  再上游（谁每帧调它）未继续追。不影响判定。

## U6 · type 51 的 ×15 分支参数先 `/2` 加权
- `0x726453..0x726494` 对 type 51（与 13 共享 case 0 定时器）有独立装弹式：
  `cdq; sub eax,edx; sar eax,1`（/2）+ 加 `call 0x65c7e0` 返回值后再 `lea×3; lea×5`（×15）。
  其参数语义（`[事件+0x34]` 经何种规则取半/取整）未深究。
