// 工具验证脚本（不是项目开发）：对给定地址反编译，报告函数边界与函数总数。
// 用途：验证 Ghidra headless + 反编译器能否替代本项目此前的手工 capstone 逐指令活。
// @category Verify

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DecompVerify extends GhidraScript {

    @Override
    public void run() throws Exception {
        DecompInterface di = new DecompInterface();
        di.toggleCCode(true);
        di.toggleSyntaxTree(true);
        if (!di.openProgram(currentProgram)) {
            println("DECOMP_OPEN_FAILED");
        }

        String[] args = getScriptArgs();
        if (args.length == 0) {
            args = new String[] { "0x47EA90", "0x47C520", "0x47C4D0", "0x568940" };
        }

        for (String a : args) {
            String hex = a.startsWith("0x") ? a.substring(2) : a;
            Address addr = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(hex);
            println("");
            println("################################################################");
            println("### TARGET " + a);
            println("################################################################");
            Function f = getFunctionContaining(addr);
            if (f == null) {
                println("  getFunctionContaining = null（该地址不在任何已识别函数内）");
                // 尝试回溯找最近的函数入口
                Function before = getFunctionBefore(addr);
                println("  getFunctionBefore = " + (before == null ? "null"
                        : before.getName() + " @ " + before.getEntryPoint()));
                continue;
            }
            println("  function = " + f.getName()
                    + "  entry = " + f.getEntryPoint()
                    + "  body = " + f.getBody().getNumAddresses() + " bytes");
            DecompileResults r = di.decompileFunction(f, 90, monitor);
            if (!r.decompileCompleted()) {
                println("  DECOMP_INCOMPLETE: " + r.getErrorMessage());
                continue;
            }
            println("---- C PSEUDOCODE ----");
            println(r.getDecompiledFunction().getC());
        }

        println("");
        println("################################################################");
        println("### 覆盖统计");
        println("################################################################");
        int total = currentProgram.getFunctionManager().getFunctionCount();
        println("FUNCTION_COUNT=" + total);
        int defined = 0, thunks = 0, ext = 0;
        FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
        while (it.hasNext()) {
            Function f = it.next();
            if (f.isExternal()) { ext++; continue; }
            if (f.isThunk()) { thunks++; continue; }
            defined++;
        }
        println("FUNCTIONS_NON_EXTERNAL=" + defined);
        println("FUNCTIONS_THUNK=" + thunks);
        println("FUNCTIONS_EXTERNAL=" + ext);
        println("VTABLE_NOTE=Ghidra 12 可用 DataTypeManager/符号表；本脚本只报计数");
    }
}
