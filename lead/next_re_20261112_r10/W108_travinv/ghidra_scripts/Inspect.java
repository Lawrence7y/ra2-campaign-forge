// W108 · Inspect the one and only unlink call site (0x005688EB) with Ghidra's
// authoritative instruction boundaries, plus a full instruction listing of the
// containing function so the "cached node across a freeing call" question is
// settled on decoded instructions, not on my own byte arithmetic.
//
// Usage: -postScript Inspect.java            -> EVIDENCE/step11_inspect_fn.txt
//        -postScript Inspect.java 0x005687F0 0x00569000

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.lang.*;
import java.io.*;
import java.util.*;

public class Inspect extends GhidraScript {

    Address addr(long v) { return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v); }
    static String hex(long v) { return String.format("0x%08X", v); }

    void writeFile(String name, String content) throws IOException {
        File dir = new File(System.getenv("W108_EVID"));
        if (dir == null || !dir.exists())
            dir = new File("D:\\Project\\ra2-campaign-forge\\lead\\next_re_20261112_r10\\W108_travinv\\EVIDENCE");
        File f = new File(dir, name);
        try (Writer w = new OutputStreamWriter(new FileOutputStream(f), "UTF-8")) { w.write(content); }
        println("wrote " + f.getAbsolutePath() + " (" + content.length() + " chars)");
    }

    @Override
    public void run() throws Exception {
        String[] a = getScriptArgs();
        long start = (a.length > 0) ? Long.decode(a[0]) : 0x005687F0L;
        long end   = (a.length > 1) ? Long.decode(a[1]) : 0x00568B60L;

        StringBuilder sb = new StringBuilder();
        FunctionManager fm = currentProgram.getFunctionManager();
        Function f = fm.getFunctionContaining(addr(0x005688EBL));

        sb.append("=== function containing 0x005688EB ===\n");
        sb.append("entry   = ").append(f == null ? "<none>" : hex(f.getEntryPoint().getOffset())).append("\n");
        sb.append("body    = ").append(f == null ? "<none>" : f.getBody().getMinAddress() + " .. " + f.getBody().getMaxAddress()).append("\n");
        sb.append("name    = ").append(f == null ? "<none>" : f.getName()).append("\n\n");

        sb.append("=== instruction listing ").append(hex(start)).append(" .. ").append(hex(end)).append(" ===\n");
        int n = 0;
        int esiWrites = 0;
        for (long va = start; va < end; ) {
            Address at = addr(va);
            Instruction ins = currentProgram.getListing().getInstructionAt(at);
            if (ins == null) {
                // not on a boundary - step forward until the next instruction
                Instruction next = currentProgram.getListing().getInstructionAfter(at);
                if (next == null) break;
                sb.append("-------- GAP, next insn at ").append(next.getAddress()).append("\n");
                va = next.getAddress().getOffset();
                continue;
            }
            sb.append(ins.getAddress()).append("  ")
              .append(String.format("%-24s", ins.toString()))
              .append("   ; ").append(ins.getMnemonicString());
            if (ins.getNumOperands() > 0) {
                for (int k = 0; k < ins.getNumOperands(); k++) {
                    sb.append(" [").append(ins.getDefaultOperandRepresentation(k)).append("]");
                }
            }
            sb.append("\n");
            n++;

            // flag every instruction that writes ESI, to prove whether esi is ever
            // reloaded with a node pointer between the branch and the call.
            String s = ins.toString();
            if (s.startsWith("MOV ESI") || s.startsWith("LEA ESI") || s.startsWith("XOR ESI")
                || s.startsWith("POP ESI") || s.startsWith("MOVSX ESI") || s.startsWith("MOVZX ESI")
                || s.startsWith("ADD ESI") || s.startsWith("SUB ESI")) {
                esiWrites++;
                sb.append("        ^^^ ESI write #").append(esiWrites).append("\n");
            }
            if (ins.getFlowType().isCall()) {
                sb.append("        ^^^ CALL (flow=").append(ins.getFlowType()).append(")\n");
            }
            va = ins.getAddress().add(ins.getLength()).getOffset();
        }
        sb.append("\ntotal instructions listed = ").append(n).append("\n");

        // decompiled function, verbatim
        DecompInterface dec = new DecompInterface();
        dec.toggleCCode(true);
        dec.openProgram(currentProgram);
        if (f != null) {
            DecompileResults dr = dec.decompileFunction(f, 120, monitor);
            sb.append("\n=== decompile of ").append(hex(f.getEntryPoint().getOffset())).append(" ===\n");
            sb.append(dr != null && dr.decompileCompleted()
                      ? dr.getDecompiledFunction().getC() : "// DECOMPILE FAILED\n");
        }
        dec.dispose();

        writeFile("step11_inspect_fn.txt", sb.toString());
    }
}
