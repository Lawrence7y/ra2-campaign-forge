/* ============================================================================
 * ra2nullguard.c  --  ②-a 修复：六个容器例程的 NULL-this 入口守卫
 *
 * This file contains NO inline assembly on purpose. The six stubs are byte
 * arrays produced and verified by stub_gen.py (capstone-disassembled), so the
 * artifact is checkable on a machine without a 32-bit compiler. At install time
 * the code is copied into VirtualAlloc'd RWX memory and only the final
 * `jmp rel32 <resume>` displacement is patched.
 *
 * 缺陷与依据（台账 §825 / §833）
 *   [0x00887368] 是"当前 CCToolTip 容器"指针，允许为 NULL（分配失败写 0、销毁
 *   路径主动清 0）。全 .text 有 50 处无守卫调用点把它当 this 送进 6 个例程，
 *   而这些例程只检查计数/数组，不检查 this ⇒ NULL 时首次访存即崩。
 *   两个主要例程的首访都恰在 this+0x250（故故障地址相同，只能靠 EIP 区分）。
 *
 * 为什么必须 hook 不能原地打补丁
 *   最小的两个例程只有 13 字节，最短守卫（jecxz 2B + 原体）仍需 15B ⇒ 放不下；
 *   .detour 段在 SizeOfImage 之外且不可执行 ⇒ 不能当 code cave（台账 §827）。
 *
 * 构建（本机当前无 32 位工具链，见台账 §834）
 *   i686-w64-mingw32-gcc -shared -O2 -o ra2nullguard.dll ra2nullguard.c -Wl,--kill-at
 *   MSVC x86:  cl /LD /O2 ra2nullguard.c
 *   —— 目标 gamemd.exe 是 32 位，必须编译为 x86。
 * ==========================================================================*/

#include <windows.h>
#include "stubs_generated.h"
#include "sites_generated.h"

static BOOL is_gamemd(void);   /* forward decl: used by both hook groups */

/* ============================================================================
 * 第二部分：第三条缺陷（台账 §831 / §837）
 * FUN_006f3f40 内有 3 处 `[obj+0xAC]` 未判空就解引用（+0x155 / +0x159 / +0x15A）。
 * 每处都是 12 字节的定长序列，紧跟 `test al,al`，因此可以整体替换为
 *     E8 <rel32 -> helper>  +  7 x 0x90
 * helper 做原样的 load + 判空；为空时 al=0（调用方的 `je` 会跳过该块）。
 * ==========================================================================*/

typedef struct {
    DWORD site;               /* 12 字节序列的起始 VA */
    const unsigned char *helper;
    DWORD helper_len;
    BYTE  original[12];
    void *helper_mem;
    int   patched;
} SITE;

static SITE g_s[] = {
    { 0x006F409C, helper_006F409C, sizeof(helper_006F409C), {0}, 0, 0 },
    { 0x006F4124, helper_006F4124, sizeof(helper_006F4124), {0}, 0, 0 },
    { 0x006F4173, helper_006F4173, sizeof(helper_006F4173), {0}, 0, 0 },
};
#define NS (sizeof(g_s)/sizeof(g_s[0]))

/* 3 处原始 12 字节（用于 fail-closed 校验） */
static const BYTE ORIG_S0[12] = {0x8B,0x91,0xAC,0x00,0x00,0x00, 0x8A,0x82,0x55,0x01,0x00,0x00};
static const BYTE ORIG_S1[12] = {0x8B,0x91,0xAC,0x00,0x00,0x00, 0x8A,0x82,0x59,0x01,0x00,0x00};
static const BYTE ORIG_S2[12] = {0x8B,0x88,0xAC,0x00,0x00,0x00, 0x8A,0x81,0x5A,0x01,0x00,0x00};
static const BYTE *ORIGS[3] = { ORIG_S0, ORIG_S1, ORIG_S2 };

BOOL RA2NG_InstallSites(void) {
    DWORD i, j;
    if (!is_gamemd()) return FALSE;
    for (i = 0; i < NS; i++) {
        SITE *s = &g_s[i];
        BYTE *p = (BYTE *)(UINT_PTR)s->site;
        DWORD old;
        LONG disp;

        if (s->patched) continue;
        if (memcmp(p, ORIGS[i], 12) != 0) return FALSE;   /* fail-closed */

        if (s->helper_mem == NULL) {
            s->helper_mem = VirtualAlloc(NULL, s->helper_len,
                                         MEM_COMMIT | MEM_RESERVE,
                                         PAGE_EXECUTE_READWRITE);
            if (s->helper_mem == NULL) return FALSE;
            memcpy(s->helper_mem, s->helper, s->helper_len);
            FlushInstructionCache(GetCurrentProcess(), s->helper_mem, s->helper_len);
        }

        memcpy(s->original, p, 12);
        if (!VirtualProtect(p, 12, PAGE_EXECUTE_READWRITE, &old)) return FALSE;
        disp = (LONG)((DWORD)(UINT_PTR)s->helper_mem - ((DWORD)(UINT_PTR)p + 5));
        p[0] = 0xE8;                       /* call rel32 */
        *(LONG *)(p + 1) = disp;
        for (j = 5; j < 12; j++) p[j] = 0x90;
        VirtualProtect(p, 12, old, &old);
        FlushInstructionCache(GetCurrentProcess(), p, 12);
        s->patched = 1;
    }
    return TRUE;
}

BOOL RA2NG_UninstallSites(void) {
    DWORD i;
    for (i = 0; i < NS; i++) {
        SITE *s = &g_s[i];
        BYTE *p = (BYTE *)(UINT_PTR)s->site;
        DWORD old;
        if (!s->patched) continue;
        if (!VirtualProtect(p, 12, PAGE_EXECUTE_READWRITE, &old)) return FALSE;
        memcpy(p, s->original, 12);
        VirtualProtect(p, 12, old, &old);
        FlushInstructionCache(GetCurrentProcess(), p, 12);
        s->patched = 0;
    }
    return TRUE;
}

void RA2NG_ReadSite(DWORD i, BYTE *out12) {
    if (i < NS) memcpy(out12, (void *)(UINT_PTR)g_s[i].site, 12);
}
DWORD RA2NG_SiteCount(void) { return (DWORD)NS; }

typedef struct {
    DWORD fn;                 /* 目标函数入口 VA */
    const unsigned char *stub;/* 未回填的 stub 模板 */
    DWORD stub_len;
    DWORD jmp_disp_off;       /* stub 内 jmp rel32 的 disp32 偏移 */
    DWORD resume;             /* 搬迁字节执行完后跳回的地址 */
    DWORD relocate_len;       /* 入口处需要被覆盖的整指令字节数 */
    BYTE  original[16];       /* 安装前的原始字节 */
    void *stub_mem;           /* 本进程内该 stub 的可执行副本 */
    int   patched;
} ENTRY;

/* 逐项对应 stub_gen.py 的产物 */
static ENTRY g_e[] = {
    { 0x007241A0, stub_007241A0, sizeof(stub_007241A0), 0, 0x007241A5,  5, {0}, 0, 0 },
    { 0x00724520, stub_00724520, sizeof(stub_00724520), 0, 0x0072452A, 10, {0}, 0, 0 },
    { 0x00724530, stub_00724530, sizeof(stub_00724530), 0, 0x00724536,  6, {0}, 0, 0 },
    { 0x00724540, stub_00724540, sizeof(stub_00724540), 0, 0x00724546,  6, {0}, 0, 0 },
    { 0x00724580, stub_00724580, sizeof(stub_00724580), 0, 0x00724588,  8, {0}, 0, 0 },
    { 0x00724730, stub_00724730, sizeof(stub_00724730), 0, 0x00724736,  6, {0}, 0, 0 },
};
#define NE (sizeof(g_e)/sizeof(g_e[0]))

/* jmp_disp_off 由 stub_gen.py 算出：它是最后一个 E9 之后 disp32 的位置。
   这里在运行时自检定位，避免手抄偏移出错。 */
static DWORD find_jmp_disp(const unsigned char *s, DWORD len) {
    DWORD i;
    /* 模板里唯一一个 E9 且后随 4 个 0 */
    for (i = 0; i + 5 <= len; i++) {
        if (s[i] == 0xE9 && s[i+1] == 0 && s[i+2] == 0 && s[i+3] == 0 && s[i+4] == 0)
            return i + 1;
    }
    return 0xFFFFFFFFu;
}

static BOOL is_gamemd(void) {
    char path[MAX_PATH];
    int n, i;
    static const char tail[] = "gamemd.exe";
    GetModuleFileNameA(NULL, path, MAX_PATH);
    n = lstrlenA(path);
    if (n < (int)sizeof(tail) - 1) return FALSE;
    for (i = 0; i < (int)sizeof(tail) - 1; i++) {
        char a = path[n - (sizeof(tail) - 1) + i];
        char b = tail[i];
        if (a >= 'A' && a <= 'Z') a = (char)(a - 'A' + 'a');
        if (b >= 'A' && b <= 'Z') b = (char)(b - 'A' + 'a');
        if (a != b) return FALSE;
    }
    return TRUE;
}

BOOL RA2NG_Install(void) {
    DWORD i;
    if (!is_gamemd()) return FALSE;

    for (i = 0; i < NE; i++) {
        ENTRY *e = &g_e[i];
        BYTE *p = (BYTE *)(UINT_PTR)e->fn;
        DWORD old, j;
        LONG disp;

        if (e->patched) continue;

        if (e->jmp_disp_off == 0) {
            e->jmp_disp_off = find_jmp_disp(e->stub, e->stub_len);
            if (e->jmp_disp_off == 0xFFFFFFFFu) return FALSE;
        }

        /* fail-closed：入口字节必须仍是镜像原样，否则拒绝安装 */
        if (e->stub_mem == NULL) {
            /* 首次安装：分配 stub 内存 */
            e->stub_mem = VirtualAlloc(NULL, e->stub_len,
                                       MEM_COMMIT | MEM_RESERVE,
                                       PAGE_EXECUTE_READWRITE);
            if (e->stub_mem == NULL) return FALSE;
        }
        memcpy(e->original, p, e->relocate_len);

        /* 校验入口确实是原始字节（用搬迁表的前 relocate_len 字节比对） */
        {
            /* 搬迁字节来自 stub 内 [4, 4+relocate_len) 区间 */
            if (memcmp(e->original, e->stub + 4, e->relocate_len) != 0) {
                return FALSE;
            }
        }

        memcpy(e->stub_mem, e->stub, e->stub_len);
        /* 回填 jmp rel32 -> resume */
        disp = (LONG)(e->resume - ((DWORD)(UINT_PTR)e->stub_mem
                                   + e->jmp_disp_off + 4));
        *(LONG *)((BYTE *)e->stub_mem + e->jmp_disp_off) = disp;
        FlushInstructionCache(GetCurrentProcess(), e->stub_mem, e->stub_len);

        if (!VirtualProtect(p, e->relocate_len, PAGE_EXECUTE_READWRITE, &old)) return FALSE;
        disp = (LONG)((DWORD)(UINT_PTR)e->stub_mem - ((DWORD)(UINT_PTR)p + 5));
        p[0] = 0xE9;
        *(LONG *)(p + 1) = disp;
        for (j = 5; j < e->relocate_len; j++) p[j] = 0x90;
        VirtualProtect(p, e->relocate_len, old, &old);
        FlushInstructionCache(GetCurrentProcess(), p, e->relocate_len);
        e->patched = 1;
    }
    return TRUE;
}

BOOL RA2NG_Uninstall(void) {
    DWORD i;
    for (i = 0; i < NE; i++) {
        ENTRY *e = &g_e[i];
        BYTE *p = (BYTE *)(UINT_PTR)e->fn;
        DWORD old;
        if (!e->patched) continue;
        if (!VirtualProtect(p, e->relocate_len, PAGE_EXECUTE_READWRITE, &old)) return FALSE;
        memcpy(p, e->original, e->relocate_len);
        VirtualProtect(p, e->relocate_len, old, &old);
        FlushInstructionCache(GetCurrentProcess(), p, e->relocate_len);
        e->patched = 0;
    }
    return TRUE;
}

/* 供外部探针核对：返回第 i 个入口的前 8 字节 */
void RA2NG_ReadEntry(DWORD i, BYTE *out8) {
    if (i < NE) memcpy(out8, (void *)(UINT_PTR)g_e[i].fn, 8);
}

DWORD RA2NG_EntryCount(void) { return (DWORD)NE; }
DWORD RA2NG_SiteCountPub(void) { return (DWORD)NS; }
DWORD RA2NG_Version(void)    { return 0x00010000u; }

/* ---- 导出（供外部框架/探针调用）---- */
__declspec(dllexport) BOOL  __stdcall RA2NG_InstallAll(void) {
    return RA2NG_Install() && RA2NG_InstallSites();
}
__declspec(dllexport) BOOL  __stdcall RA2NG_UninstallAll(void) {
    RA2NG_UninstallSites();
    return RA2NG_Uninstall();
}
__declspec(dllexport) void  __stdcall RA2NG_ReadEntryPub(DWORD i, BYTE *out8)  { RA2NG_ReadEntry(i, out8); }
__declspec(dllexport) void  __stdcall RA2NG_ReadSitePub(DWORD i, BYTE *out12) { RA2NG_ReadSite(i, out12); }
__declspec(dllexport) DWORD __stdcall RA2NG_Counts(void) { return (NE << 16) | NS; }
__declspec(dllexport) DWORD __stdcall RA2NG_Ver(void)    { return RA2NG_Version(); }

BOOL WINAPI DllMain(HINSTANCE h, DWORD reason, LPVOID r) {
    (void)h; (void)r;
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(h);
        if (is_gamemd()) {
            RA2NG_Install();        /* ②-a：6 个容器例程的入口守卫 */
            RA2NG_InstallSites();   /* 第三条缺陷：FUN_006f3f40 的 3 处判空 */
        }
    } else if (reason == DLL_PROCESS_DETACH) {
        RA2NG_UninstallSites();
        RA2NG_Uninstall();
    }
    return TRUE;
}
