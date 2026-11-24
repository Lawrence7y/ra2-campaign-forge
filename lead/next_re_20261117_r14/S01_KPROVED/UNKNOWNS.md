# UNKNOWNS

- U1：0069AE90 是唯一 YRpp 绑定的未证 S01 行（Game::SetProgress, Unsorted.h:43 JMP_STD）。若用户/Lead 裁 (B)「身份替代」放宽到接受 JMP_STD 绑定 + 跨类通用全局的字节吻合，则本行可补 ③b（4 路跳表 @0x69B15C + Sleep 定时循环）+ ④（60 个 direct call），成为最多可升的 1 行。当前按 D-41 裁决前默认 (A) 不升。
- U2：00554400（LoadProgressMgr::slot0）与 00643E80（ProgressScreenClass::slot0）有 vtable/rdata 引用，槽名来自 classification_trace；无足够证据把「槽语义未证」升为 ③b 合同，保持 [静态推断]。
- U3：本卡未改任何 grade / name / semantics；S01 proved 仍 6/53，21 行缺口无法在严格口径下闭合。
