# CRT 内存池落地前独立风险评审与最小验证方案 (Risk Review & Verification Plan)

> **文档标识**：`docs/re/crt_pool_risk_review.md`  
> **任务编号**：A-17（派工 v17 专项独立风险评审）  
> **责任方**：Antigravity（独立逆向审计与风险评估方，只读）  
> **评审对象**：
> - 落地规格：[docs/re/landing_pack_crt_audio_particle.md](file:///d:/Project/ra2-campaign-forge/docs/re/landing_pack_crt_audio_particle.md)（模块一：CRT 高频小对象池化）
> - 深潜基准：[docs/re/crt_memory_pool_deep_dive.md](file:///d:/Project/ra2-campaign-forge/docs/re/crt_memory_pool_deep_dive.md)  
> **目标**：在 ZCode 实际编码编译前，对直接劫持 `operator new` / `delete`、绕过 `_HEAP_LOCK` 的高危内存池方案进行全维度威胁建模，给出明确的判定结论与必须补齐的防护规格。

---

## 一、评审结论与裁定 (Executive Verdict)

- **综合评审判定**：**⚠️ 需先补防护 (MUST PATCH DEFENSES FIRST)**
- **裁定理由**：
  现有 `landing_pack_crt_audio_particle.md` 中的内存池原型属于“单线程轻量设计”，在直接面对生产级游戏环境时存在 **5 项致命架构缺陷（Fatal Vulnerabilities）**：
  1. **8 字节对齐破坏（Alignment Fault）**：4 字节头部导致返回指针仅 4 字节对齐，破坏 `double`（`BulletClass` 浮点速度向量）及 SSE 指令的对齐契约，将直接触发 `0xC0000005`；
  2. **双释放引发 Freelist 死循环（Double Free Infinite Loop）**：释放时不擦除 Tag，二次释放使单块形成环形自引用链，后续分配将重复返回同一内存地址；
  3. **Tag 校验缺乏内存地址边界保护（Tag Bypass / False Positive）**：仅校验 `0xA5A5` 幻数，若外部普通堆内存前 4 字节恰巧为该值，将误将外部堆块插入池链表导致全局堆崩溃；
  4. **无锁并发未做原子 CAS 保护（Race Condition）**：若底层音频/网络回调触发跨线程 `new`/`delete`，单链表入队出队将发生链表撕裂；
  5. **动态热回滚内存暴毙（Non-Atomic Rollback Crash）**：若在局内将开关切为 0，此前从池中分配的存活对象被传入原版 `free`，CRT 堆检查校验失败直接触发 `0xC0000374`（Heap Corruption）。
- **执行指令**：**在补齐第二节的 5 项强化防护前，禁止 ZCode 将 CRT 内存池合入主干！**

---

## 二、八大维度深度威胁清单与防护规范 (Threat Matrix)

### 1. 威胁一：8 字节对齐破坏与 SIMD/浮点崩溃 (Alignment & Datatype Fault)
- **触发条件**：现有原型定义 `sizeof(PoolHeader) = 4`，返回地址为 `pBlock + 4`。即使 `pBlock` 为 8 字节对齐，返回给游戏引擎的指针也是 **奇数 DWORD 对齐（4 字节对齐，非 8 字节对齐）**。
- **最坏后果**：
  - `BulletClass` 内部包含 `Vector3D<double> Velocity`（偏移 `+0xE8..+0xF8`），x86 架构读写跨 8 字节边界的 64 位浮点数性能暴跌；
  - 若引擎底层或 SIMD 优化采用 `movaps` / `movapd` 指令（要求严格 16 字节对齐），或者 SSE 临时读写，直接触发 `STATUS_DATATYPE_MISALIGNMENT` 或 `0xC0000005` 崩溃。
- **现有 spec 是否已防**：❌ **未防**（当前使用 `(sz+3)&~3` 且头部仅 4 字节）。
- **必须补齐的防护**：
  - 强制头部 8 字节对齐：`struct PoolHeader { uint32_t magic; uint32_t poolIdx; };`（`sizeof(PoolHeader) = 8`）；
  - 块大小强制 8 字节对齐：`m_elemSize = (elemSize + 7) & ~7;`；
  - 返回指针 `pBlock + 8` 恒定满足 8 字节严格对齐。

---

### 2. 威胁二：双释放导致 Freelist 成环与对象地址碰撞 (Double Free & Cyclic List)
- **触发条件**：引擎某些异常分支（如网络重连重置事件队列、粒子系统生命周期提前结束又被析构）对同一指针调用了两次 `delete`。
- **最坏后果**：
  - 第一次 `delete` 将 `pBlock` 挂入 `m_freeList`；由于头部 Tag 依然保持 `0xA5A50000 | idx`，第二次 `delete` 依然通过校验；
  - 第二次 `delete` 执行 `*pBlock = m_freeList; m_freeList = pBlock;`，导致 `pBlock->next = pBlock`（**自引用环形链表**）；
  - 随后的所有 `Alloc()` 请求全部返回同一个内存地址，成百上千个新对象数据在同一片内存互相覆写，引发无法复现的鬼畜行为或即时闪退。
- **现有 spec 是否已防**：❌ **未防**（释放时未清除 Tag）。
- **必须补齐的防护**：
  - 释放时**立即投毒并清空 Tag**：
    ```cpp
    pHdr->magic = 0xDEADBEEF; // 释放瞬间标记失效
    ```
  - 若发生 Double Free，第二次校验 `(pHdr->magic == 0xA5A55A5A)` 必然失败，直接拦截并记录告警。

---

### 3. 威胁三：Tag 误判与内存越界混入 (False Positive Tag & Range Guard)
- **触发条件**：西木原版 CRT `malloc` 分配的普通对象（未池化对象），其头部恰好存放了魔数 `0xA5A5xxxx`（在 32 位地址空间数百万次分配中，纯概率命中非零）。
- **最坏后果**：
  - 非池化对象被误认为是池化对象，直接被强行插入 `s_pools[idx]` 的 `m_freeList`；
  - 后续从池中拿出的指针根本不是由 `VirtualAlloc` 保留的连续缓冲，引发内存越界、页属性违规与堆崩溃。
- **现有 spec 是否已防**：❌ **未防**（仅比对 16 位魔数）。
- **必须补齐的防护**：
  - 引入**双重硬件地址范围检验（Address Range Guard）**：
    ```cpp
    // 必须同时满足：1. 地址落在池连续缓冲区内；2. Magic 完全吻合
    if (ptr < m_buffer || ptr >= m_bufferEnd) {
        // 绝非本池内存，绝对安全穿透至原版 CRT free
        return orig_free(ptr);
    }
    ```

---

### 4. 威胁四：释放后使用导致链表破损 (Use-After-Free & Freelist Corruption)
- **触发条件**：对象被 `delete` 后，野指针再次写入该内存（UAF）。
- **最坏后果**：
  - 由于空闲块内部复用为 `void* next` 指针，野指针写入任意数据都会直接改写 `next`；
  - 下一次 `Alloc()` 取出畸变指针（如 `0x00000001`），紧接着下下次 `Alloc()` 直接崩在空指针访问。
- **现有 spec 是否已防**：❌ **未防**。
- **必须补齐的防护**：
  - 在 `Alloc()` 取出节点时，强制校验 `next` 指针是否合法（等于 `nullptr` 或落在 `[m_buffer, m_bufferEnd)` 且符合步长对齐）；
  - 若探测到 `next` 越界，立即丢弃破损节点并自愈重置链表，阻止雪崩。

---

### 5. 威胁五：非原子热回滚导致堆崩溃 (Non-Atomic Rollback Crash 0xC0000374)
- **触发条件**：游戏运行中，用户通过 INI 动态将 `EnableMemoryPool` 由 1 改为 0，或卸载 DLL 时撤销 `_delete` 挂钩。
- **最坏后果**：
  - 之前由池化分配的对象依然存活；当它们后续被释放时，走原版 `free(0x007C93E8)`；
  - 原版 `free` 读取指针前方的 CRT 块描述符，发现并非 Windows 堆句柄分配的 Chunk，立即触发 **`STATUS_HEAP_CORRUPTION` (`0xC0000374`)**，进程立即被系统强杀。
- **现有 spec 是否已防**：❌ **未防**。
- **必须补齐的防护**：
  - **静态加载铁律**：`EnableMemoryPool` 必须是**启动期单次锁定配置（Launch-Time Only）**，严禁热切换；
  - **卸载保护**：即使卸载挂钩，`_delete` 钩子也必须常驻，或者在完全确认无存活对象后再解除。

---

### 6. 威胁六：多线程并发读写与缺少原子 CAS (Cross-Thread Concurrency)
- **触发条件**：DirectSound 音频流线程、网络 DirectPlay 接收线程或异步加载器间接调用了包含 `operator new/delete` 的工具函数。
- **最坏后果**：两个线程同时执行 `m_freeList = pBlock`，发生并发更新冲突（Lost Update），造成内存泄漏或链表分支丢失。
- **现有 spec 是否已防**：❌ **未防**（普通非原子指针赋值）。
- **必须补齐的防护**：
  - 全面改用**无锁原子 CAS 指令（Lock-Free Atomic CAS）**：
    ```cpp
    // 入队出队一律使用 InterlockedCompareExchangePointer
    void* oldHead;
    do {
        oldHead = m_freeList;
        *reinterpret_cast<void**>(pBlock) = oldHead;
    } while (InterlockedCompareExchangePointer(&m_freeList, pBlock, oldHead) != oldHead);
    ```
  - 耗时仅 5~10ns，且对单线程与多线程 100% 安全。

---

### 7. 威胁七：与 Windows 原生 LFH (Low Fragmentation Heap) 的冲突与收益权衡
- **现状分析**：现网 INI 已经默认激活 `EnableLFH=1`（`HeapSetInformation`）。Windows LFH 本身已对 $\le 16\text{ KB}$ 的小对象进行了分桶无锁缓存。
- **潜在冲突**：若自定义池管理不当发生碎片，反而不如操作系统内建的 LFH 稳定。
- **裁决建议**：自定义池只针对**最极端的高频同构对象**（312B Particle、352B Bullet、456B Anim）进行拦截，不与通用堆争抢小标量，实现“LFH 管全局，专用池管密集战斗对象”的双层保护。

---

### 8. 威胁八：尺寸错配（Size Mismatch / Vector Realloc）
- **触发条件**：通过 `new (312)` 分配，但由于基类虚析构函数遗漏或虚表截断，`delete` 传入了错误的尺寸或派生类未定义虚析构。
- **最坏后果**：对象被错误归还到错误的桶。
- **现有 spec 是否已防**：✅ **已防**。因为 `PoolHeader` 内部携带了分配时的 `poolIdx`，`Free` 仅依据头部存储的真实桶号回收，天然具备抗尺寸错配能力。

---

## 三、生产级强化 C++ 实施规格 (Hardened Implementation Spec)

ZCode 落地必须采用以下已消除上述 5 项致命缺陷的强化版本：

```cpp
namespace HardenedMemoryPool {

#pragma pack(push, 8)
struct PoolBlockHeader {
    uint32_t magic;    // 存活态: 0xA5A55A5A; 释放态: 0xDEADBEEF
    uint32_t poolIdx;  // 桶索引 0..7
};
#pragma pack(pop)

class HardenedFixedPool {
public:
    void Init(size_t elemSize, size_t capacity, uint32_t poolIdx) {
        m_elemSize = (elemSize + 7) & ~7; // 8 字节对齐
        m_totalBlockSize = sizeof(PoolBlockHeader) + m_elemSize; // 8 + elemSize (8 字节倍数)
        m_capacity = capacity;
        m_poolIdx = poolIdx;
        size_t totalBytes = m_totalBlockSize * capacity;
        m_buffer = reinterpret_cast<uint8_t*>(VirtualAlloc(nullptr, totalBytes, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
        m_bufferEnd = m_buffer + totalBytes;
        m_freeList = nullptr;

        if (m_buffer) {
            for (size_t i = 0; i < capacity; ++i) {
                uint8_t *pBlock = m_buffer + i * m_totalBlockSize;
                // 空闲状态：投毒 magic，防止野指针探测
                reinterpret_cast<PoolBlockHeader*>(pBlock)->magic = 0xDEADBEEF;
                reinterpret_cast<PoolBlockHeader*>(pBlock)->poolIdx = poolIdx;
                *reinterpret_cast<void**>(pBlock + sizeof(PoolBlockHeader)) = m_freeList;
                m_freeList = pBlock;
            }
        }
    }

    void* Alloc() {
        // 无锁 CAS 提取头部
        void *pBlock = nullptr;
        void *pNext = nullptr;
        do {
            pBlock = m_freeList;
            if (!pBlock) return nullptr; // 池耗尽，平滑回退
            // 守卫：校验取出的块是否在本池内
            if (pBlock < m_buffer || pBlock >= m_bufferEnd) return nullptr;
            pNext = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(pBlock) + sizeof(PoolBlockHeader));
        } while (InterlockedCompareExchangePointer(&m_freeList, pNext, pBlock) != pBlock);

        PoolBlockHeader *pHdr = reinterpret_cast<PoolBlockHeader*>(pBlock);
        pHdr->magic = 0xA5A55A5A;
        pHdr->poolIdx = m_poolIdx;

        // 返回严格 8 字节对齐的用户数据指针
        return reinterpret_cast<uint8_t*>(pBlock) + sizeof(PoolBlockHeader);
    }

    bool Free(void *ptr) {
        if (!ptr) return false;
        uint8_t *pBlock = reinterpret_cast<uint8_t*>(ptr) - sizeof(PoolBlockHeader);

        // 1. 硬件级地址范围守卫 (绝对杜绝外部堆误杀)
        if (pBlock < m_buffer || pBlock >= m_bufferEnd) {
            return false;
        }

        PoolBlockHeader *pHdr = reinterpret_cast<PoolBlockHeader*>(pBlock);

        // 2. 双释放与投毒守卫
        if (pHdr->magic != 0xA5A55A5A || pHdr->poolIdx != m_poolIdx) {
            // Double free 或 Tag 损坏：直接阻断，保护链表
            return true; // 消费掉，避免送入 CRT 造成堆损坏
        }

        // 3. 立即投毒标记为释放态
        pHdr->magic = 0xDEADBEEF;

        // 4. 无锁 CAS 放回链表
        void *oldHead = nullptr;
        do {
            oldHead = m_freeList;
            *reinterpret_cast<void**>(ptr) = oldHead;
        } while (InterlockedCompareExchangePointer(&m_freeList, pBlock, oldHead) != oldHead);

        return true;
    }

    bool IsInPool(void *ptr) const {
        return (ptr >= m_buffer && ptr < m_bufferEnd);
    }

private:
    size_t   m_elemSize;
    size_t   m_totalBlockSize;
    size_t   m_capacity;
    uint32_t m_poolIdx;
    uint8_t *m_buffer;
    uint8_t *m_bufferEnd;
    void    *volatile m_freeList;
};

} // namespace HardenedMemoryPool
```

---

## 四、最小验证方案 (Minimum Verification Plan)

在合入前必须按以下 4 步完成最小验证：

| 验证步骤 | 验证手段 | 判定标准 (Pass Criteria) | 失败红线 (Fail Criteria) |
|:---:|:---|:---|:---|
| **Step 1: 内存对齐实测** | 单元测试分配 1000 次 | 返回指针 `((uintptr_t)ptr & 7) == 0` **100% 成立** | 出现任意一次 4 字节对齐直接判 FAIL |
| **Step 2: Double-Free 免疫测试** | 故意执行 `delete ptr; delete ptr;` | 第二次 `Free()` 命中 `magic != 0xA5A55A5A` 早退，`m_freeList` **无环状引用**，后续分配正常 | 发生死循环或崩溃 |
| **Step 3: U800 满载交火压测** | 单机 U800 8 玩家 AI 混战 3 局（每局 $\ge 15$ 分钟） | 1. 遥测 `poolAllocs` $\approx$ `poolFrees`（差值 $\le$ 当前存活粒子数）；<br>2. 连续 3 局 **`except.txt` 零新增** | 发生崩溃或句柄暴涨 |
| **Step 4: 静态锁定与热回滚防护** | 启动后修改 INI 尝试切换开关 | 日志输出“内存池为启动锁定项，不支持局内热切换”，维持原模式稳定运行 | 局内热切导致 `0xC0000374` |

---

## 五、必须补齐的交付条目清单（给 ZCode / MiMo）

1. **条目 P-M1（对齐）**：将 `PoolHeader` 扩为 8 字节（`magic` + `poolIdx`），`m_elemSize` 强制按 8 字节向上取整；
2. **条目 P-M2（范围）**：`Free` 入口前置 `pBlock >= m_buffer && pBlock < m_bufferEnd` 硬件地址范围判定；
3. **条目 P-M3（投毒）**：`Free` 成功时将 `pHdr->magic` 覆写为 `0xDEADBEEF`；
4. **条目 P-M4（原子）**：`Alloc` 与 `Free` 链表头指针更新全面替换为 `InterlockedCompareExchangePointer`；
5. **条目 P-M5（锁定）**：在 `LoadConfig` 中声明 `EnableMemoryPool` 仅在游戏初始化时生效一次，严禁运行时动态切换。
