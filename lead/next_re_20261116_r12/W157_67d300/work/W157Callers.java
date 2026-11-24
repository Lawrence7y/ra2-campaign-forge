// W157: caller-context + decompilation probe.
// RANGE dumps raw disassembly with bytes/call/data refs for the 4 xref sites of 0x67CEF0.
// DECOMP dumps decompiled C of key functions.
// @category W157
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class W157Callers extends GhidraScript {
    Address addr(long v) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v);
    }
    String hx(Instruction ins) {
        StringBuilder sb = new StringBuilder();
        try { for (byte b : ins.getBytes()) sb.append(String.format("%02x", b & 0xff)); }
        catch (Exception e) { return "??"; }
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
    String readAscii(Address a) {
        try {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < 128; i++) {
                int b = currentProgram.getMemory().getByte(a.add(i)) & 0xff;
                if (b == 0) break;
                if (b < 0x20 || b >= 0x7f) return null;
                sb.append((char) b);
            }
            return sb.length() >= 2 ? sb.toString() : null;
        } catch (Exception e) { return null; }
    }
    void range(long lo, long hi, String label) throws Exception {
        println("### RANGE " + label + " [" + String.format("%08x", lo) + "," + String.format("%08x", hi) + ")");
        InstructionIterator it = currentProgram.getListing().getInstructions(addr(lo), true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            if (ins.getAddress().getOffset() >= hi) break;
            StringBuilder sb = new StringBuilder();
            sb.append(ins.getAddress()).append("  ").append(String.format("%-20s", hx(ins)))
              .append("  ").append(String.format("%-8s", ins.getMnemonicString())).append("  ").append(ops(ins));
            for (Reference r : ins.getReferencesFrom()) {
                Address t = r.getToAddress();
                if (t == null) continue;
                if (r.getReferenceType().isCall()) sb.append("  ;CALL->").append(t);
                else { String s = readAscii(t); sb.append("  ;DATA->").append(t); if (s != null) sb.append(" \"" + s + "\""); }
            }
            println(sb.toString());
        }
        println("### END RANGE " + label);
    }
    void decomp(long entry, String label, int timeout) throws Exception {
        DecompInterface di = new DecompInterface();
        di.setOptions(new DecompileOptions());
        di.openProgram(currentProgram);
        Function f = currentProgram.getFunctionManager().getFunctionAt(addr(entry));
        println("### DECOMP " + label + " @" + String.format("%08x", entry)
                + (f == null ? " NO FN" : (" size=" + f.getBody().getNumAddresses())));
        if (f == null) return;
        DecompileResults res = di.decompileFunction(f, timeout, monitor);
        if (res == null || !res.decompileCompleted()) { println("### (decompile failed)"); return; }
        int k = 0;
        for (String ln : res.getDecompiledFunction().getC().split("\n")) {
            println("C| " + ln);
            if (++k > 200) { println("C| ...(truncated at 200 lines)"); break; }
        }
        println("### END DECOMP " + label + " lines=" + k);
    }
    public void run() throws Exception {
        println("### IMAGEBASE=" + currentProgram.getImageBase());
        range(0x55DC40L, 0x55DD00L, "xref_55dc92_in_55D360");
        range(0x4C7A60L, 0x4C7B60L, "xref_4c7ac0_4c7b3d");
        range(0x559E40L, 0x559EC0L, "xref_559e85");
        range(0x55DE40L, 0x55DE90L, "frame_counter_55DE6A");
        decomp(0x0067CEF0L, "67CEF0", 90);
        decomp(0x005F6250L, "5F6250", 90);
        decomp(0x0067D300L, "67D300", 120);
        println("### DONE");
    }
}
