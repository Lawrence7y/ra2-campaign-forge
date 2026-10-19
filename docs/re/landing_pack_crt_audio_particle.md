# CRT 池化 + 音频限频 + 微粒迷雾剔除 三合一生产级落地规格书 (Landing Pack)

> **文档标识**：`docs/re/landing_pack_crt_audio_particle.md`  
> **任务编号**：A-14（派工 v14 专项规格工厂，供 ZCode 生产级连续落地）  
> **责任方**：Antigravity（逆向工程与规格设计方，只读）  
> **输入深潜基线**：
> - [docs/re/crt_memory_pool_deep_dive.md](file:///d:/Project/ra2-campaign-forge/docs/re/crt_memory_pool_deep_dive.md)（CRT 内存池与动态向量扩容机制）
> - [docs/re/audio_engine_deep_dive.md](file:///d:/Project/ra2-campaign-forge/docs/re/audio_engine_deep_dive.md)（音频引擎调度与交火削峰去重）
> - [docs/re/bullet_particle_fog_deep_dive.md](file:///d:/Project/ra2-campaign-forge/docs/re/bullet_particle_fog_deep_dive.md)（弹道与粒子剔除机制）
> - [docs/re/particle_fog_owner_evidence.md](file:///d:/Project/ra2-campaign-forge/docs/re/particle_fog_owner_evidence.md)（A-4 粒子与系统 Owner 链实证）  
> **执行准则**：严禁修改 `ra2render/**` 与台账 `REVERSE_ENGINEERING_AND_PATCHES.md`。

---

## 模块一：CRT 高频小对象池化 (Subsystem 1: CRT Memory Pool)

### 1. 目标挂钩点与原版指令 [实证]
- **`operator new` 入口**：`0x007C8E17`
  - 原版指令（6 字节）：
    ```asm
    0x007C8E17: 6A 01                 push 1
    0x007C8E19: FF 74 24 08           push dword ptr [esp + 8]   ; size
    0x007C8E1D: E8 20 06 00 00        call 0x007C9442            ; malloc 核心
    ```
- **`operator delete` 入口**：`0x007C8B3D`
  - 原版指令（9 字节）：
    ```asm
    0x007C8B3D: FF 74 24 04           push dword ptr [esp + 4]   ; ptr
    0x007C8B41: E8 A2 08 00 00        call 0x007C93E8            ; free 核心
    0x007C8B46: 59                    pop  ecx
    ```

### 2. 补丁方案与定长桶设计
针对重载战斗中粒子（312B）、弹丸（352B）、动画（456B）以及基础定长结构（8B, 12B, 16B, 24B, 40B）设计 8 个定长 Freelist 桶。头部预留 **8 字节块头**（`struct PoolBlockHeader { uint32_t magic; uint32_t poolIdx; }`，`magic` 存活态 `0xA5A55A5A` / 释放态（投毒）`0xDEADBEEF`；`poolIdx` 为独立字段），块大小强制 **8 字节对齐**，返回**池块 + 8**；非池化对象或池耗尽无缝穿透至原版 CRT。
> **【F-06 订正 · 2026-09-26 · task-14】** 改前：「头部预留 **4 字节** Tag（`MAGIC_POOLED = 0xA5A50000 | poolIdx`）」+ `pack(4)` + `(elemSize+3)&~3`；改后：**8B 头 + 8 对齐 + 返回 `pBlock+8`**，`magic` 统一 `0xA5A55A5A`（`poolIdx` 独立字段）。依据：执行总表 §2.4.2 P-M1（`pending_execution_master_table.md:186-196`：`sizeof(PoolBlockHeader)==8`、`m_elemSize=(elemSize+7)&~7`、返回 `pBlock+8`，理由 = `Vector3D<double>` 8 字节自然对齐）与 `TC-ST-04` 一票否决项「**头部为 4 字节**…→ FAIL」（同文 `:422`）`[实证 + 推演]` → 4B 方案与同一总表**内部冲突**。

### 3. Copy-Paste 级 C++ 实施代码

```cpp
// ============================================================================
// CRT 高频对象池实现
// ============================================================================

namespace MemoryPool {

#pragma pack(push, 8)
struct PoolHeader {
    uint32_t magic;   // 存活态 0xA5A55A5A ; 释放态（投毒） 0xDEADBEEF
    uint32_t poolIdx; // 桶索引 0..7（F-06：独立字段，不再与 magic 位域复用）
};
#pragma pack(pop)   // sizeof(PoolHeader) == 8  ← F-06 订正（改前 4）

class FixedPool {
public:
    void Init(size_t elemSize, size_t capacity) {
        m_elemSize = (elemSize + 7) & ~7;   // F-06 订正：8 字节对齐（改前 (elemSize + 3) & ~3）
        m_totalBlockSize = sizeof(PoolHeader) + m_elemSize;
        m_capacity = capacity;
        m_buffer = reinterpret_cast<uint8_t*>(VirtualAlloc(nullptr, m_totalBlockSize * capacity, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
        m_freeList = nullptr;
        if (m_buffer) {
            for (size_t i = 0; i < capacity; ++i) {
                uint8_t *pBlock = m_buffer + i * m_totalBlockSize;
                *reinterpret_cast<void**>(pBlock + sizeof(PoolHeader)) = m_freeList;
                m_freeList = pBlock;
            }
        }
    }

    void* Alloc(uint32_t poolIdx) {
        if (!m_freeList) return nullptr;
        uint8_t *pBlock = reinterpret_cast<uint8_t*>(m_freeList);
        m_freeList = *reinterpret_cast<void**>(pBlock + sizeof(PoolHeader));
        PoolHeader *pHdr = reinterpret_cast<PoolHeader*>(pBlock);
        pHdr->magic = 0xA5A55A5A;   // F-06 订正（改前 0xA5A50000 | poolIdx）
        pHdr->poolIdx = poolIdx;
        return pBlock + sizeof(PoolHeader);
    }

    void Free(void *ptr) {
        if (!ptr) return;
        uint8_t *pBlock = reinterpret_cast<uint8_t*>(ptr) - sizeof(PoolHeader);
        reinterpret_cast<PoolHeader*>(pBlock)->magic = 0xDEADBEEF; // F-06/P-M2：回收前投毒（双释放免疫）
        *reinterpret_cast<void**>(pBlock + sizeof(PoolHeader)) = m_freeList;
        m_freeList = pBlock;
    }

private:
    size_t m_elemSize;
    size_t m_totalBlockSize;
    size_t m_capacity;
    uint8_t *m_buffer;
    void *m_freeList;
};

static FixedPool s_pools[8];
static bool s_poolInitialized = false;
static uint8_t s_origNewBytes[6] = {0};
static uint8_t s_origDeleteBytes[9] = {0};

static inline int SizeToPoolIdx(size_t sz) {
    if (sz <= 8) return 0;
    if (sz <= 12) return 1;
    if (sz <= 16) return 2;
    if (sz <= 24) return 3;
    if (sz <= 40) return 4;
    if (sz == 312) return 5; // ParticleClass
    if (sz == 352) return 6; // BulletClass
    if (sz == 456) return 7; // AnimClass
    return -1;
}

void* __cdecl Hooked_CRT_New(size_t size) {
    if (s_poolInitialized) {
        int idx = SizeToPoolIdx(size);
        if (idx >= 0) {
            void *p = s_pools[idx].Alloc(idx);
            if (p) {
                g_telemetry.poolAllocs++;
                return p;
            }
        }
    }
    g_telemetry.poolFallbacks++;
    // 透传原版 malloc
    typedef void* (__cdecl *MallocFunc)(size_t);
    return reinterpret_cast<MallocFunc>(0x007C9442)(size);
}

void __cdecl Hooked_CRT_Delete(void *ptr) {
    if (!ptr) return;
    if (s_poolInitialized) {
        // ★ 落地实现方补齐（P-M3 范围守卫，见执行总表 §2.4.2）：先做 [m_buffer, m_bufferEnd) 归属校验
        //   再读 -8 处块头；本包模块一只订正 8B 头/对齐/magic 口径（F-06），范围守卫与 CAS 按总表实现。
        PoolHeader *pHdr = reinterpret_cast<PoolHeader*>(reinterpret_cast<uint8_t*>(ptr) - sizeof(PoolHeader));
        if (pHdr->magic == 0xA5A55A5A) {   // F-06 订正（改前 (magic & 0xFFFF0000) == 0xA5A50000）
            uint32_t idx = pHdr->poolIdx;  // F-06 订正（改前 magic & 0x0000FFFF）
            if (idx < 8) {
                s_pools[idx].Free(ptr);
                g_telemetry.poolFrees++;
                return;
            }
        }
    }
    // 透传原版 free
    typedef void (__cdecl *FreeFunc)(void*);
    reinterpret_cast<FreeFunc>(0x007C93E8)(ptr);
}

} // namespace MemoryPool
```

### 4. INI、遥测与回滚
- **INI 键**：`[System] EnableMemoryPool=0`（默认 0；**启动期单次锁定配置，严禁局内热切换**）
  > **【F-02 订正 · 2026-09-26 · task-14】** 改前：`[System] EnableMemoryPool=1`（默认 1）；改后：**默认 0 + 启动期锁定**。依据：执行总表口径（`pending_execution_master_table.md:49,301,322` 默认 `0` + §〇.4「启动期单次锁定，严禁局内动态切换，否则存活对象跨堆释放触发 `0xC0000374`」）`[推演 + 实证]`；本包原值属历史草案 `[实证]`（`mp_landing_consistency.md:227-230` F-02）。
- **遥测项**：`poolAllocs`（池命中分配数）、`poolFrees`（池回收数）、`poolFallbacks`（回退原生堆分配数）
- **回滚机制**：
  在 `0x007C8E17` 写回 6 字节原指令 `6A 01 FF 74 24 08`；
  在 `0x007C8B3D` 写回 9 字节原指令 `FF 74 24 04 E8 A2 08 00 00`。

---

## 模块二：音频引擎并发削峰与智能限频 (Subsystem 2: Audio Engine De-flood)

### 1. 目标挂钩点与原版指令 [实证]
- **`VocClass::PlayGlobal` 入口**：`0x00750920`
  - 原版指令（6 字节）：
    ```asm
    0x00750920: 51                    push ecx
    0x00750921: A0 AC 64 84 00        mov  al, byte ptr [0x008464AC] ; AudioEnabled 全局标志
    ```
- **`VocClass::PlayAt` 入口**：`0x007509E0`
  - 原版指令（**5 字节**，首指令足迹）：
    ```asm
    0x007509E0: A0 AC 64 84 00        mov  al, byte ptr [0x008464AC] ; AudioEnabled
    0x007509E5: 53                    push ebx     ; ← 下一条指令（**不属于本补丁足迹**，禁止一并写入/还原）
    ```
    > **【F-01 订正 · 2026-09-26 · task-14】** 改前：原版指令标注为「**6 字节**」（`A0 AC 64 84 00 53`）；改后：**5 字节**（`A0 AC 64 84 00`）。依据：`gamemd.exe` 机读实测 `0x007509E0 = A0 AC 64 84 00`（5B，`mov al,[0x8464AC]`），第 6 字节 `53` 是**下一条** `push ebx` `[实证]`（`docs/re/anchor_claims.txt:78` 断言行 = `A0 AC 64 84 00 53 84 C0`，即 5B 指令 + `53` + `84 C0`；本包 `:169` 亦自标 `0x007509E5`）。执行总表/回滚表/`TC-ST-05` 全链均按 5B 书写，仅本包按 6B → **按 6B 写入会覆写 `push ebx`**。

### 2. 削峰去重规则与跳板设计
1. **同种音效 80ms 静音窗口**：记录 `s_lastSoundFrame[SoundID]`，若 `CurrentFrame - s_lastSoundFrame[SoundID] < 2`（RA2 15fps 下约 130ms，快速对局下约 80ms），直接短路返回 0（NULL 指针，严禁返回 -1，因调用方将返回值视作 `VocClass*` 解引用）。
2. **单帧全局上限**：每逻辑帧全局最多触发 4 条播放请求（`s_soundsThisFrame >= 4`），多余请求平滑丢弃，杜绝 DirectSound 缓冲区被机枪/光棱折射洪泛撑爆。
3. **ABI 堆栈平衡契约 [Lead v22 / S15 定谳实证]**：
   - `VocClass::PlayGlobal (0x00750920)` 原生禁用分支位于 `0x0075092E`（`33 C0 59 C2 08 00`：`xor eax, eax; pop ecx; ret 8`），出栈清理 8 字节参数；
   - `VocClass::PlayAt (0x007509E0)` 原生禁用分支位于 `0x007509EC`（`33 C0 5B C2 04 00`：`xor eax, eax; pop ebx; ret 4`），出栈清理 4 字节参数；
   - 削峰拦截早退分支必须严格执行 `xor eax, eax`（返回 NULL）与对应 `ret 8` / `ret 4`，严禁使用 0 字节清参 `ret` 或返回 `-1`。

### 3. Copy-Paste 级 C++ 实施代码

```cpp
// ============================================================================
// 音频洪泛削峰与智能限频 (Lead v22 / S15 校验修正版)
// ============================================================================

namespace AudioThrottle {

static uint32_t s_lastSoundFrame[2048] = {0};
static uint32_t s_currentFrameCount = 0;
static uint32_t s_soundsInCurrentFrame = 0;
static bool     g_enableAudioThrottle = true;
static uint32_t g_maxSoundsPerFrame = 4;
static uint32_t g_soundMinIntervalFrames = 2; // ~130ms

static uint8_t  s_origPlayGlobalBytes[6] = {0};
static void*    s_pPlayGlobalTrampoline = nullptr;
static uint8_t  s_origPlayAtBytes[5] = {0};   // F-01 订正：5B（改前 [6]）
static void*    s_pPlayAtTrampoline = nullptr;

bool ShouldThrottleSound(int soundId) {
    if (!g_enableAudioThrottle) return false;
    if (soundId < 0 || soundId >= 2048) return false;

    const uint32_t *pCurrentFrame = reinterpret_cast<const uint32_t*>(0x00A8ED84);
    uint32_t frame = pCurrentFrame ? *pCurrentFrame : 0;

    if (frame != s_currentFrameCount) {
        s_currentFrameCount = frame;
        s_soundsInCurrentFrame = 0;
    }

    // 规则 1：单帧硬限额
    if (s_soundsInCurrentFrame >= g_maxSoundsPerFrame) {
        g_telemetry.soundsThrottled++;
        return true;
    }

    // 规则 2：同类音效频度锁
    if (frame >= s_lastSoundFrame[soundId] && (frame - s_lastSoundFrame[soundId]) < g_soundMinIntervalFrames) {
        g_telemetry.soundsThrottled++;
        return true;
    }

    s_lastSoundFrame[soundId] = frame;
    s_soundsInCurrentFrame++;
    g_telemetry.soundsTriggered++;
    return false;
}

// PlayGlobal: __fastcall (ECX = soundId, EDX = volume/pan, + 8 bytes on stack)
// 出口必须 ret 8，早退返回 0 (NULL VocClass*)
__declspec(naked) void* __fastcall Hook_VocClass_PlayGlobal(int soundId, int volume) {
    __asm {
        push edx
        push ecx
        call ShouldThrottleSound
        test al, al
        jnz  do_silence_global
        pop  ecx
        pop  edx
        // 走跳板执行原版 0x00750920
        jmp  dword ptr [s_pPlayGlobalTrampoline]

    do_silence_global:
        pop  ecx
        pop  edx
        xor  eax, eax                 // return NULL (0, 原生禁用分支 0x0075092E 行为)
        ret  8                        // 严格弹出栈上传递的 2 个 DWORD (8 字节)
    }
}

// PlayAt: __fastcall (ECX = soundId, EDX = CoordStruct*, + 4 bytes on stack)
// 出口必须 ret 4，早退返回 0 (NULL VocClass*)
__declspec(naked) void* __fastcall Hook_VocClass_PlayAt(int soundId, void *pCoord) {
    __asm {
        push edx
        push ecx
        call ShouldThrottleSound
        test al, al
        jnz  do_silence_at
        pop  ecx
        pop  edx
        // 走跳板执行原版 0x007509E0
        jmp  dword ptr [s_pPlayAtTrampoline]

    do_silence_at:
        pop  ecx
        pop  edx
        xor  eax, eax                 // return NULL (0, 原生禁用分支 0x007509EC 行为)
        ret  4                        // 严格弹出栈上传递的 1 个 DWORD (4 字节)
    }
}

} // namespace AudioThrottle
```

### 4. INI、遥测与回滚
- **INI 键**：`[Audio] EnableAudioThrottling=1`, `MaxSoundsPerFrame=4`, `SoundMinIntervalFrames=2`
> 【W3 勘误 · W3-A6/ISSUE-SECTION-AUDIO】[W3-Lead临时裁决] 改前：[Audio] EnableAudioThrottling；改后：[AudioThrottle] ; DC-02 裁决口径: 8 键体系，宿主 ra2render.ini Enable=0 MaxVoicePerFrame=6 VoiceDedupMs=80；依据：docs/re/dispatch/W3_20261001_Lead_DECISION_AND_BOARD.md:41; docs/re/audio_throttle_landing.md:19, 139-147；分级：P0
- **遥测项**：`soundsTriggered`（实际播放数）、`soundsThrottled`（拦截削峰数）
- **回滚机制**：
  还原 `0x00750920` 处的 6 字节原指令 `51 A0 AC 64 84 00`；
  还原 `0x007509E0` 处的 **5 字节**原指令 `A0 AC 64 84 00`。
  > **【F-01 订正】** 改前：「6 字节原指令 `A0 AC 64 84 00 53`」；改后：「**5 字节** `A0 AC 64 84 00`」。依据同上（`53` = 下一条 `push ebx`，**不得**作为本补丁的还原字节）。`[实证]`

---

## 模块三：微粒与微粒系统迷雾隐形剔除 (Subsystem 3: Particle Fog Culling)

### 1. 目标挂钩点与原版指令 [实证]
针对任务 A-4 证实的槽 69 挂载点：
- **`ParticleClass::vtable[69]` (Draw)**：`0x007EFA68`
  - 原虚表指针：`0x0062CEC0`（原版 `ParticleClass::Draw` 入口）
- **`ParticleSystemClass::vtable[69]` (Draw)**：`0x007EFCB0`
  - 原虚表指针：`0x0062E280`（原版 `ParticleSystemClass::Draw` 入口）

### 2. 宿主阵营穿透与坐标网格换算链 [A-15 定谳实证]
依据 A-15 物理读写点定谳证据（详见 `particle_fog_owner_evidence.md`）：
1. **`ParticleSystemClass` 结构偏移 (sizeof=0x100)**：
   - **`+0xFC`：`HouseClass* OwnerHouse`（直接阵营指针）**：
     - 写点：构造函数 `0x0062DD9A`（`89 86 FC 00 00 00 mov [esi+0xFC], eax`，实参 `[esp+0x40]`）；
     - 读点实证：`0x0062C2CC`（`8B 90 FC 00 00 00 mov edx, [eax+0xFC]`，读取阵营指针传给着色虚表）；
   - **`+0xE0`：`TechnoClass* Owner`（发射载体单位指针）**：
     - 写点：构造函数 `0x0062DE37`（非空写实参 `ecx`）与 `0x0062DE54`（空参写 `0`，指针语义）；
     - 读点实证：`0x0062DE6D` / `0x0062ED7B`（取 `[esi+0xE0]` 调虚表 `[eax+0x48]` `GetCoords` 同步载体坐标）；`0x0062F090`（读取 `Owner+0x684` 状态）；
   - **`+0x9C`：`CoordStruct Location`（12 字节世界坐标：X=`+0x9C`, Y=`+0xA0`, Z=`+0xA4`）**：
     - 读写点：`0x0062DE77` 等 15 处 `lea edx, [reg+0x9C]` 严密证实。
2. **`ParticleClass` 结构偏移 (sizeof=0x138)**：
   - **`+0x124`：`ParticleSystemClass* ParticleSystem`（所属父系统指针）**：
     - 写点：构造函数 `0x0062B721`（`89 8E 24 01 00 00 mov [esi+0x124], ecx`）；
     - 读点实证：`0x0062C2C2`（`8B 85 24 01 00 00 mov eax, [ebp+0x124]` 取得系统以访问 `+0xFC` 阵营）；
   - **`+0x9C`：`CoordStruct Location`（粒子当前世界坐标）**：
     - 读点：`0x0062CF30`（`lea eax, [edi+0x9C]`）。
3. **视觉剔除原则**：
   - 己方/友军微粒：100% 正常绘制；
   - 敌方微粒（如 V3/无畏火箭尾迹、光棱散射粒子、着火微粒）：若当前网格不在直视圈内（`s_visionGrid[cellIdx] != s_visionToken`），直接 `return` 跳过绘制！
   - **绝对红线**：只拦截槽 69 虚表，微粒内部物理衰减与生命周期（`Update`）完全不受影响，联机 100% 同步。

### 3. Copy-Paste 级 C++ 实施代码（与现有 FogHooks 统一合并）

```cpp
// ============================================================================
// 微粒与微粒系统迷雾视觉剔除 (扩展现网 FogHooks 类，A-15 定谳版)
// ============================================================================

typedef void (__thiscall *ParticleDrawFunc)(void *pThis, void *pLocation, void *pBounds);
static ParticleDrawFunc s_pOrigParticleDraw = reinterpret_cast<ParticleDrawFunc>(0x0062CEC0);
static ParticleDrawFunc s_pOrigParticleSystemDraw = reinterpret_cast<ParticleDrawFunc>(0x0062E280);
static bool g_enableParticleFog = false;   // F-03 订正：默认 0（改前 true）

// 辅助判定：微粒系统是否应该在迷雾中绘制
static bool ShouldDrawParticleSystem(void *pThis) {
    if (!pThis) return false;
    if (!g_enableParticleFog) return true;

    uintptr_t pSystem = reinterpret_cast<uintptr_t>(pThis);

    // 1. 阵营判定：主路径读 +0xFC (OwnerHouse)，备用路径读 +0xE0 (Owner -> +0x21C)
    void *pOwnerHouse = *reinterpret_cast<void**>(pSystem + 0xFC);
    if (!pOwnerHouse) {
        void *pOwnerTechno = *reinterpret_cast<void**>(pSystem + 0xE0);
        if (pOwnerTechno && reinterpret_cast<uintptr_t>(pOwnerTechno) >= 0x10000) {
            pOwnerHouse = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pOwnerTechno) + 0x21C);
        }
    }

    void *pPlayerHouse = *reinterpret_cast<void**>(0x00A83D4C); // HouseClass::Player
    if (pOwnerHouse && pPlayerHouse) {
        // 若为己方或盟友，全彩放行
        typedef bool (__thiscall *IsAlliedFunc)(void *pThis, void *pOther);
        if (reinterpret_cast<IsAlliedFunc>(0x004F9AB0)(pPlayerHouse, pOwnerHouse)) {
            return true;
        }
    } else if (!pOwnerHouse) {
        return true; // 环境中立微粒 (如地图天然烟囱) 默认放行
    }

    // 2. 敌军微粒：坐标直视核查 (+0x9C CoordStruct: X=+0x9C, Y=+0xA0)
    int32_t worldX = *reinterpret_cast<int32_t*>(pSystem + 0x9C);
    int32_t worldY = *reinterpret_cast<int32_t*>(pSystem + 0xA0);
    int32_t cellX = worldX >> 8;
    int32_t cellY = worldY >> 8;

    if (cellX < 0 || cellX >= 512 || cellY < 0 || cellY >= 512) {
        return false;
    }

    uint32_t cellIdx = static_cast<uint32_t>(cellY * 512 + cellX);
    // 直视圈内核查
    return (s_visionGrid[cellIdx] == s_visionToken);
}

void __thiscall FogHooks::Hook_ParticleSystem_Draw(void *pLocation, void *pBounds) {
    void *pThis = this;
    if (!ShouldDrawParticleSystem(pThis)) {
        g_telemetry.particleSystemsCulledByFog++;
        return; // 迷雾中敌方尾迹/激光直接剔除
    }
    s_pOrigParticleSystemDraw(pThis, pLocation, pBounds);
}

void __thiscall FogHooks::Hook_Particle_Draw(void *pLocation, void *pBounds) {
    void *pThis = this;
    uintptr_t pParticle = reinterpret_cast<uintptr_t>(pThis);
    // 通过 +0x124 穿透至所属 ParticleSystemClass
    void *pSystem = *reinterpret_cast<void**>(pParticle + 0x124);
    if (pSystem && !ShouldDrawParticleSystem(pSystem)) {
        g_telemetry.particlesCulledByFog++;
        return;
    }
    s_pOrigParticleDraw(pThis, pLocation, pBounds);
}

// 在 InstallVTableHooks() 中追加挂载 (统一收口槽 69，严禁二次覆写):
void InstallParticleFogHooks() {
    DWORD oldProtect;
    // 1. ParticleClass::vtable[69] (0x007EFA68)
    VirtualProtect(reinterpret_cast<void*>(0x007EFA68), 4, PAGE_EXECUTE_READWRITE, &oldProtect);
    *reinterpret_cast<void**>(0x007EFA68) = reinterpret_cast<void*>(&FogHooks::Hook_Particle_Draw);
    VirtualProtect(reinterpret_cast<void*>(0x007EFA68), 4, oldProtect, &oldProtect);

    // 2. ParticleSystemClass::vtable[69] (0x007EFCB0)
    VirtualProtect(reinterpret_cast<void*>(0x007EFCB0), 4, PAGE_EXECUTE_READWRITE, &oldProtect);
    *reinterpret_cast<void**>(0x007EFCB0) = reinterpret_cast<void*>(&FogHooks::Hook_ParticleSystem_Draw);
    VirtualProtect(reinterpret_cast<void*>(0x007EFCB0), 4, oldProtect, &oldProtect);

    LogMessage("[ra2render-fog] 成功挂载微粒与微粒系统迷雾剔除 (0x007EFA68 / 0x007EFCB0)！");
}

void RemoveParticleFogHooks() {
    DWORD oldProtect;
    VirtualProtect(reinterpret_cast<void*>(0x007EFA68), 4, PAGE_EXECUTE_READWRITE, &oldProtect);
    *reinterpret_cast<void**>(0x007EFA68) = reinterpret_cast<void*>(0x0062CEC0);
    VirtualProtect(reinterpret_cast<void*>(0x007EFA68), 4, oldProtect, &oldProtect);

    VirtualProtect(reinterpret_cast<void*>(0x007EFCB0), 4, PAGE_EXECUTE_READWRITE, &oldProtect);
    *reinterpret_cast<void**>(0x007EFCB0) = reinterpret_cast<void*>(0x0062E280);
    VirtualProtect(reinterpret_cast<void*>(0x007EFCB0), 4, oldProtect, &oldProtect);
}
```

### 4. INI、遥测与回滚
- **INI 键**：`[FogOfWar] EnableParticleFog=0`（默认 0；验收时**显式置 1**）
  > **【F-03 订正 · 2026-09-26 · task-14】** 改前：`[FogOfWar] EnableParticleFog=1`（默认 1）；改后：**默认 0**。依据：主包与执行总表一致为 0（`landing_pack_particle.md:55,287,298,379,393`；`pending_execution_master_table.md:47,297,324`），且主包验收断言「`=1` 时 `particlesCulledByFog > 0`」以「默认 0、验收显式置 1」为前提（`landing_pack_particle.md:320`）`[实证]`；与 G-01 保守策略同构（`mp_landing_consistency.md:232-235` F-03）。
- **遥测项**：`particlesCulledByFog`（单粒子剔除数）、`particleSystemsCulledByFog`（粒子系统剔除数）
- **回滚机制**：
  向 `0x007EFA68` 写回 `0x0062CEC0`；
  向 `0x007EFCB0` 写回 `0x0062E280`。

---

## 四、三合一落地集成与验收清单 (Integration & Acceptance)

| 落地模块 | 对应源码文件 | 验收准则 (Acceptance Criteria) | 失败判定 (Fail Criteria) |
|---|---|---|---|
| **CRT 小对象池** | `MemoryPool::` | 1. 遥测 `poolAllocs` 与 `poolFrees` 显著递增；<br>2. 高频交火下内存碎片率下降，无堆分配崩溃；<br>3. `poolFallbacks` 维持合理低位。 | 发生悬挂指针崩溃、内存泄漏或 `MAGIC_POOLED` 校验失败。 |
| **音频并发削峰** | `AudioThrottle::` | 1. 50+ 单位光棱折射/交火时音频饱满且无爆音、无杂音卡顿；<br>2. `soundsThrottled` 稳定累加；<br>3. 无声卡 DirectSound 阻塞。 | 关键语音（如基地遭袭警告）被误杀丢弃，或声音滞后。 |
| **微粒迷雾剔除** | `FogHooks::Particle` | 1. 敌军在黑雾中发射 V3/基洛夫炸弹时，无尾迹白烟提前暴露；<br>2. 己方武器尾迹 100% 正常展现；<br>3. 遥测 `particlesCulledByFog > 0`。 | 己方尾迹消失，或未侦察到敌军时在迷雾中看到爆炸火花。 |


---

## 五、P-4 / P-5 字节级跳板执行表（F-05 补全 · 2026-09-26 · task-14）[实证]

> **订正说明**：改前 — 本包模块一（CRT）与模块二（音频）**只有 C++ 代码、没有任何字节级新字节表**，跳板指向运行时变量 `s_pPlayGlobalTrampoline` / `s_pPlayAtTrampoline` / `s_pPlayGlobalTrampoline`（`s_pPlayAtTrampoline`），**无统一基址 → 无法算 rel32**，执行方无法「零推演」落地（`mp_landing_consistency.md` F-05）。
> 改后 — 与 `landing_pack_net_fix.md` §9 同规格：跳板统一落在 `T0 = 0x01B00000` 页内**固定槽位**，`E9 rel32` 为**已算好的真实字节**（非占位符）。
> **依据**：`out/re_work/fixpack/gen_p45_tramp.py` → `out/re_work/fixpack/p45_tramp_bytes.txt`：`gamemd.exe` 原字节 4/4 `MATCH`、槽位与 P-1 占用零重叠、每条 `jmp/call/rel8` 落点 capstone 反汇编校验 `OK` `[实证]`。
> 槽位/指针槽清单与执行总表 `pending_execution_master_table.md` §2.1.1（布局）、§2.4.3 / §2.5.3（字节级表）**逐字节一致**。

### 5.1 槽位与指针槽（cave 页内，避开 NoopArea `0x01B00200`）

| 用途 | 地址 | 宽度 | 内容 |
|:---|:---|:---:|:---|
| `TRAMP_P4_CRT_NEW` | `0x01B00140` | 槽 64B（实用 39B） | P-4.1 `operator new` 跳板 |
| `TRAMP_P4_CRT_DEL` | `0x01B00180` | 槽 64B（实用 35B） | P-4.2 `operator delete` 跳板 |
| `TRAMP_P5_AUD_PG` | `0x01B001C0` | 槽 64B（实用 36B） | P-5.1 `PlayGlobal` 跳板 |
| `NoopHelper` | `0x01B00200` | 1B | `C3`（**既有，勿动**） |
| `RetZeroStub` | `0x01B00204` | 3B | `33 C0 C3`（新增；**缺省助手** = `eax=0` → 直通） |
| `TRAMP_P5_AUD_PA` | `0x01B00240` | 槽 64B（实用 35B） | P-5.2 `PlayAt` 跳板 |
| `p_P4_New` | `0x01B00510` | u32 | 函数指针（安装时填；缺省 `0x01B00204`） |
| `p_P4_Delete` | `0x01B00514` | u32 | 函数指针（缺省 `0x01B00204`） |
| `p_P5_ThrottlePG` | `0x01B00518` | u32 | 函数指针（缺省 `0x01B00204`） |
| `p_P5_ThrottlePA` | `0x01B0051C` | u32 | 函数指针（缺省 `0x01B00204`） |

### 5.2 执行表（照表写入，不做静态推理）

| 步骤 | 地址 | 原字节 | 新字节 | 开关 | 回滚 | 验收 | 标注 |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **0. 分配 cave** | `VirtualAlloc(0x01B00000, 0x1000, RWX)` | — | 4K 页；`+0x200`←`C3`；`+0x204`←`33 C0 C3` | — | `VirtualFree` | 返回 == `0x01B00000`；**失败 → P-4/P-5 全部不安装**（F-07 口径：跳过 + 红字日志 + 遥测计数） | [实证] / [待实测] |
| **1. 写 TRAMP_P4_CRT_NEW** | `0x01B00140` | — | `9C 60 FF 74 24 28 FF 15 10 05 B0 01 83 C4 04 85 C0 75 0D 61 9D 6A 01 FF 74 24 08 E9 BD 8C CC FE 89 44 24 1C 61 9D C3`（39B） | `EnableMemoryPool` | 废弃 | 反汇编 == §5.3 表（`jmp` 落点 `0x007C8E1D`） | [实证] |
| **2. 写 TRAMP_P4_CRT_DEL** | `0x01B00180` | — | `9C 60 FF 74 24 28 FF 15 14 05 B0 01 83 C4 04 85 C0 75 0D 61 9D FF 74 24 04 E8 4A 92 CC FE 59 C3 61 9D C3`（35B） | 同上 | 废弃 | `call` 落点 `0x007C93E8`、已处理出口 `ret`（`void`） | [实证] |
| **3. 写 TRAMP_P5_AUD_PG** | `0x01B001C0` | — | `9C 60 51 FF 15 18 05 B0 01 83 C4 04 85 C0 75 0D 61 9D 51 A0 AC 64 84 00 E9 49 07 C5 FE 61 9D 33 C0 C2 08 00`（36B） | `EnableAudioThrottling` | 废弃 | `jmp` 落点 `0x00750926`；静音出口 `ret 8` | [实证] |
| **4. 写 TRAMP_P5_AUD_PA** | `0x01B00240` | — | `9C 60 51 FF 15 1C 05 B0 01 83 C4 04 85 C0 75 0C 61 9D A0 AC 64 84 00 E9 89 07 C5 FE 61 9D 33 C0 C2 04 00`（35B） | 同上 | 废弃 | `jmp` 落点 `0x007509E5`（**5B 足迹，F-01**）；静音出口 `ret 4` | [实证] |
| **5. 填助手指针** | `0x01B00510/514/518/51C` | `0` | 各填 `0x01B00204`（缺省）或真实助手 | — | 回填 `0x01B00204` | 非空且 **≠ `0x01B00200`（NoopHelper）** | [实证] |
| **6. 装 P-4.1** | `0x007C8E17` | `6A 01 FF 74 24 08` | `E9 24 73 33 01 90` | `EnableMemoryPool`（**启动期锁定**） | `6A 01 FF 74 24 08` | dump 逐字节；`6B` 与 `6B` 等长 | [实证]字节 / [待实测]行为 |
| **7. 装 P-4.2** | `0x007C8B3D` | `FF 74 24 04 E8 A2 08 00 00` | `E9 3E 76 33 01 90 90 90 90` | 同上 | `FF 74 24 04 E8 A2 08 00 00` | dump 逐字节；`9B` 与 `9B` 等长 | [实证]字节 / [待实测]行为 |
| **8. 装 P-5.1** | `0x00750920` | `51 A0 AC 64 84 00` | `E9 9B F8 3A 01 90` | `EnableAudioThrottling` | `51 A0 AC 64 84 00` | dump 逐字节；`6B` 与 `6B` 等长 | [实证]字节 / [待实测]行为 |
| **9. 装 P-5.2** | `0x007509E0` | `A0 AC 64 84 00`（**5B**） | `E9 5B F8 3A 01` | 同上 | `A0 AC 64 84 00` | dump 逐字节；`5B` 与 `5B` 等长（**不得**含 `53`） | [实证]字节 / [待实测]行为 |
| **10. 装后 dump** | 4 处补丁点 | — | 与步骤 6–9「新字节」一致 | — | — | hex 逐字节比对 + `E9 rel32` 落点 == 槽位 | [待实测] |
| **11. 助手语义自检** | — | — | — | — | — | 指针填 `RetZeroStub` 时：P-4 全走原版路径（`OrigOK`）、P-5 零节流（`soundsThrottled == 0`） | [待实测] |
| **12. Remove** | 4 处补丁点 | 见「新字节」 | 见「原字节」列 | 键置 0 | — | 4 处逐字节复原 + `FlushInstructionCache` + `VirtualFree` | [实证]字节 / [待实测]还原 |

### 5.3 跳板逐指令反汇编（capstone 复算 `[实证]`）

`TRAMP_P4_CRT_NEW @ 0x01B00140`：

| VA | 字节 | 指令 | 说明 |
|:---|:---|:---|:---|
| `0x01B00140` | `9C 60` | `pushfd; pushad` | 现场保护 |
| `0x01B00142` | `FF 74 24 28` | `push dword [esp+0x28]` | 原 `[esp+4]` = `size` |
| `0x01B00146` | `FF 15 10 05 B0 01` | `call dword [0x01B00510]` | `uint32_t __cdecl P4_New(size_t)`；非 0 = 池已处理 |
| `0x01B0014C` | `83 C4 04 85 C0` | `add esp,4; test eax,eax` | **须 32 位返回、禁止 `bool`** |
| `0x01B00151` | `75 0D` | `jne 0x01B00160` | 池命中 → 直接返回 |
| `0x01B00153` | `61 9D 6A 01 FF 74 24 08` | `popad; popfd; push 1; push [esp+8]` | 现场还原后**原样重放原 6B** |
| `0x01B0015B` | `E9 BD 8C CC FE` | `jmp 0x007C8E1D` | 回原 `call 0x007C9442` 续跑 |
| `0x01B00160` | `89 44 24 1C 61 9D C3` | `mov [esp+0x1C],eax; popad; popfd; ret` | `[esp+0x1C]` = `pushad` 的 EAX 槽 → 返回池块 |

`TRAMP_P5_AUD_PG @ 0x01B001C0`：

| VA | 字节 | 指令 | 说明 |
|:---|:---|:---|:---|
| `0x01B001C0` | `9C 60 51` | `pushfd; pushad; push ecx` | `ECX = soundId`（`__fastcall` 第 1 参） |
| `0x01B001C3` | `FF 15 18 05 B0 01` | `call dword [0x01B00518]` | `uint32_t __cdecl P5_ThrottlePG(int)`；非 0 = 拦截 |
| `0x01B001C9` | `83 C4 04 85 C0` | `add esp,4; test eax,eax` | — |
| `0x01B001CE` | `75 0D` | `jne 0x01B001DD` | 拦截 → 静音早退 |
| `0x01B001D0` | `61 9D` | `popad; popfd` | 现场还原 |
| `0x01B001D2` | `51 A0 AC 64 84 00` | `push ecx; mov al,[0x008464AC]` | **原样重放原 6B** |
| `0x01B001D8` | `E9 49 07 C5 FE` | `jmp 0x00750926` | 回原 `mov [esp],edx` 续跑 |
| `0x01B001DD` | `61 9D 33 C0 C2 08 00` | `popad; popfd; xor eax,eax; ret 8` | 与原生 `0x0075092E`（`33 C0 59 C2 08 00`）**语义等价** |

### 5.4 助手函数实现要求（落地侧，非本包字节面）

| 助手 | 签名 | 契约 |
|:---|:---|:---|
| `P4_New` | `uint32_t __cdecl P4_New(size_t size)` | 返回**池块指针**（非 0）或 **0 = 走原版**；内部按总表 §2.4.2 P-M1…P-M5（8B 头 / 8 对齐 / 返回 `pBlock+8` / CAS / 启动期锁定） |
| `P4_Delete` | `uint32_t __cdecl P4_Delete(void* ptr)` | 返回 **1 = 已回收**，**0 = 走原版**（`P-M3` 范围守卫：非本池对象一律返回 0，**禁止读池外 `-8` 处**） |
| `P5_ThrottlePG` | `uint32_t __cdecl P5_ThrottlePG(int soundId)` | 返回 **1 = 拦截**（`xor eax,eax; ret 8` 由跳板执行），**0 = 放行**；内部 `ShouldThrottleSound` 语义见 §模块二.3 |
| `P5_ThrottlePA` | `uint32_t __cdecl P5_ThrottlePA(int soundId)` | 同上（出口 `ret 4`） |

> **返回值宽度**：4 个助手**必须返回 32 位整型**（不得 `bool` / `char`），跳板用 `test eax,eax` 全宽判定——高 16 位垃圾会导致误判。
> **缺省值纪律**：安装时若尚未就绪，四指针一律先填 `RetZeroStub`（`0x01B00204`）→ 行为 100% 等价原版；**严禁**填 `NoopHelper`（`0x01B00200`，`C3` 不写 EAX）。

---

## 六、本包勘误与订正登记（F-01…F-06 相关 · 2026-09-26 · task-14）

| 编号 | 位置 | 改前 | 改后 | 依据 | 标注 |
|:---:|:---|:---|:---|:---|:---|
| **F-01** | §模块二.1 `PlayAt` 原版指令 / §模块二.3 `s_origPlayAtBytes` / §模块二.4 回滚 | 「**6 字节**：`A0 AC 64 84 00 53`」；`uint8_t s_origPlayAtBytes[6]` | 「**5 字节**：`A0 AC 64 84 00`」；`s_origPlayAtBytes[5]` | `gamemd.exe` 机读：`0x007509E0 = A0 AC 64 84 00`（5B），`53` 是下一条 `push ebx`（`0x007509E5`）；`anchor_claims.txt:78` | [实证] |
| **F-02** | §模块一.4 INI 键 | `[System] EnableMemoryPool=1`（默认 1） | `=0`（默认 0 + **启动期单次锁定**） | 执行总表 `:49,301,322` + §〇.4 | [推演 + 实证] |
| **F-03** | §模块三.4 INI 键 / §模块三.3 代码默认 | `EnableParticleFog=1`（默认 1）；`g_enableParticleFog = true` | `=0`（默认 0，验收显式置 1）；`= false` | 主包与总表一致 0（`particle:55,287,298,379,393`；`master:47,297,324`）；G-01 保守策略同构 | [实证] |
| **F-04** | — （本包无此问题；见 `landing_pack_particle.md`） | — | — | — | 不适用 |
| **F-05** | 全文缺字节级新字节表 | 仅 C++ 代码 + 运行时跳板指针（无统一基址） | 新增 **§五**：4 槽位 + 助手指针槽 + 真实 `E9 rel32` 与跳板连写 hex + 逐指令反汇编 + 执行表 | `gen_p45_tramp.py` / `p45_tramp_bytes.txt` | [实证] |
| **F-06** | §模块一.2 方案段 / §模块一.3 `PoolHeader` / `Alloc` / `Free` / `Hooked_CRT_Delete` | 4B Tag（`0xA5A50000 \| poolIdx`）、`pack(4)`、`(elemSize+3)&~3`、magic 位域判定 | **8B 头**（`magic=0xA5A55A5A` + `poolIdx` 独立字段）、`pack(8)`、`(elemSize+7)&~7`、返回 `pBlock+8`、回收投毒 `0xDEADBEEF` | 总表 §2.4.2 P-M1/P-M2 与 `TC-ST-04`（4B 头 = 一票否决） | [实证 + 推演] |

> **附带观察（未列入 F-01…F-13，仅登记不改）**：本包遥测命名 `poolAllocs` / `poolFrees` / `poolFallbacks` 与执行总表 `poolAllocations` / `poolFrees` / `poolFallbacks`（`master:346-349`）存在一处命名差异（`poolAllocs` vs `poolAllocations`）；**不在本次裁定范围**，落地时以总表 `MasterForgeTelemetry` 结构体为准。
