// W151: single-run probe.
//  INFO   : true function bounds for a list of addresses
//  DISASM : full disassembly of a list of functions (with call targets resolved)
//  DECOMP : decompiled C of a list of functions
//  IREF   : every instruction in a function that references a given data address
// @category W151
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class W151Probe extends GhidraScript {

    Address addr(long v) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v);
    }

    long[] INFOS = {
        0x0055B960L, 0x0055B8F0L, 0x0055B880L, 0x004666E0L, 0x00468090L,
        0x00468BB0L, 0x00468D80L, 0x005B20F0L, 0x0053AB70L, 0x004F54A0L,
        0x00421EA0L, 0x006802F0L, 0x0067D300L, 0x0067CEF0L, 0x00686670L,
        0x00468670L, 0x004684E0L, 0x00468000L
    };

    long[] DISASM = { 0x0055B8F0L };

    long[] DECOMP = {
        0x0055B8F0L, 0x004666E0L, 0x00468BB0L, 0x00468D80L,
        0x005B20F0L, 0x0053AB70L, 0x004F54A0L, 0x00421EA0L
    };

    // (function entry, data address of interest)
    long[][] IREF = {
        {0x0055B8F0L, 0x00A8ED50L},
        {0x004666E0L, 0x00A8ED50L},
        {0x004666E0L, 0x0089DE18L},
        {0x005B20F0L, 0x00A8ED50L}
    };

    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        println("=== IMAGEBASE " + currentProgram.getImageBase());

        println("\n=== INFO ===");
        for (long a : INFOS) {
            Function f = fm.getFunctionContaining(addr(a));
            Function ex = fm.getFunctionAt(addr(a));
            println(String.format("%08x  containing=%s  isEntry=%s  size=%d  params=%d",
                a,
                f == null ? "-" : f.getEntryPoint().toString(),
                ex != null ? "YES" : "no",
                f == null ? -1 : f.getBody().getNumAddresses(),
                f == null ? -1 : f.getParameterCount()));
        }

        println("\n=== DISASM ===");
        Listing lst = currentProgram.getListing();
        for (long a : DISASM) {
            Function f = fm.getFunctionContaining(addr(a));
            if (f == null) { println("no fn at " + a); continue; }
            println("--- FN " + f.getEntryPoint() + " size=" + f.getBody().getNumAddresses());
            InstructionIterator it = lst.getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                StringBuilder sb = new StringBuilder();
                sb.append(String.format("%s  %-24s %s %s", ins.getAddress().toString(),
                        ins.getBytes().length <= 12 ? bytes(ins) : "", ins.getMnemonicString(), ops(ins)));
                for (Reference r : ins.getReferencesFrom()) {
                    Address t = r.getToAddress();
                    if (t == null) continue;
                    if (r.getReferenceType().isCall()) {
                        Function tf = fm.getFunctionAt(t);
                        sb.append("   ; CALL->").append(t);
                        if (tf != null) sb.append(" (size=").append(tf.getBody().getNumAddresses()).append(")");
                    } else if (r.getReferenceType().isData()) {
                        sb.append("   ; DATA->").append(t);
                    }
                }
                println(sb.toString());
            }
        }

        DecompInterface di = new DecompInterface();
        di.setOptions(new DecompileOptions());
        di.openProgram(currentProgram);
        for (long a : DECOMP) {
            Function f = fm.getFunctionContaining(addr(a));
            println("\n=== DECOMP " + (f == null ? ("?" + a) : f.getEntryPoint().toString())
                    + " size=" + (f == null ? -1 : f.getBody().getNumAddresses()) + " ===");
            if (f == null) continue;
            DecompileResults res = di.decompileFunction(f, 120, monitor);
            if (res == null || !res.decompileCompleted()) { println("(decompile failed)"); continue; }
            int k = 0;
            for (String ln : res.getDecompiledFunction().getC().split("\n")) {
                println("C| " + ln);
                k++;
            }
            println("C| ### lines=" + k);
        }

        println("\n=== IREF ===");
        for (long[] pair : IREF) {
            Function f = fm.getFunctionContaining(addr(pair[0]));
            println("--- fn " + (f == null ? "?" : f.getEntryPoint().toString()) + " refs to " + pair[1]);
            if (f == null) continue;
            InstructionIterator it = lst.getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                for (int i = 0; i < ins.getNumOperands(); i++) {
                    for (Reference r : ins.getOperandReferences(i)) {
                        if (r.getToAddress() != null && r.getToAddress().getOffset() == pair[1]) {
                            println("   " + ins.getAddress() + "  " + ins.toString());
                        }
                    }
                }
            }
        }
    }

    String bytes(Instruction ins) {
        StringBuilder sb = new StringBuilder();
        try {
            for (byte b : ins.getBytes()) sb.append(String.format("%02x", b));
        } catch (Exception e) {
            return "??";
        }
        return sb.toString();
    }

    String ops(Instruction ins) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < ins.getNumOperands(); i++) {
            if (i > 0) sb.append(",");
            sb.append(ins.getDefaultOperandRepresentation(i));
        }
        return sb.toString();
    }
}
