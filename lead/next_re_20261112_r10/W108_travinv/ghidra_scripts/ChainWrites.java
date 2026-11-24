// W108 · Question (C), closing move: find every code site that writes cell+0xE4 or
// cell+0xE8 (chain head A / B) and every site that writes object field +0x8C (the
// whichChain value UNLINK receives).  If nothing ever inserts into chain B, then
// whichChain is always 0 at runtime and (C) "wrong chain" cannot fire.

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.lang.*;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.util.*;

public class ChainWrites extends GhidraScript {

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

    /**
     * Scan all instructions for a memory WRITE whose displacement equals a given value.
     * Displacement is matched on the *operand object* (Scalar), not on a byte pattern,
     * so there is no false-positive problem of the kind L5 recorded.
     */
    List<Instruction> displaceWrites(long disp) {
        List<Instruction> out = new ArrayList<>();
        InstructionIterator it = currentProgram.getListing().getInstructions(true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            if (ins.getNumOperands() == 0) continue;
            // does any operand carry the scalar displacement?
            boolean hasDisp = false;
            for (int k = 0; k < ins.getNumOperands(); k++) {
                for (Object o : ins.getOpObjects(k)) {
                    if (o instanceof Scalar && ((Scalar) o).getUnsignedValue() == disp) { hasDisp = true; break; }
                }
                if (hasDisp) break;
            }
            if (!hasDisp) continue;
            // is it a write?  cheap and reliable test: the first operand names memory
            // and the result of the instruction is NOT "read only".  We use the
            // decompiler-free heuristic: mnemonic in a known store set.
            String mn = ins.getMnemonicString().toUpperCase();
            boolean store = mn.equals("MOV") || mn.equals("AND") || mn.equals("OR")
                         || mn.equals("XOR") || mn.equals("ADD") || mn.equals("SUB")
                         || mn.equals("INC") || mn.equals("DEC");
            if (!store) continue;
            // verify operand 0 is the memory operand and it is the one with disp
            boolean firstIsMem = false;
            for (Object o : ins.getOpObjects(0)) {
                if (o instanceof Scalar && ((Scalar) o).getUnsignedValue() == disp) firstIsMem = true;
            }
            if (!firstIsMem) continue;
            out.add(ins);
        }
        return out;
    }

    @Override
    public void run() throws Exception {
        StringBuilder sb = new StringBuilder();
        FunctionManager fm = currentProgram.getFunctionManager();

        long[] disps = { 0xE4L, 0xE8L, 0x8CL };
        String[] names = { "cell+0xE4 (chain A head)", "cell+0xE8 (chain B head)", "obj+0x8C (whichChain)" };

        for (int i = 0; i < disps.length; i++) {
            List<Instruction> hits = displaceWrites(disps[i]);
            sb.append("\n=== writes with displacement ").append(hex(disps[i])).append("  ").append(names[i])
              .append("   count=").append(hits.size()).append(" ===\n");
            Map<Long, Integer> byFn = new TreeMap<>();
            for (Instruction ins : hits) {
                Function f = fm.getFunctionContaining(ins.getAddress());
                long e = (f == null) ? 0 : f.getEntryPoint().getOffset();
                byFn.merge(e, 1, Integer::sum);
                sb.append(ins.getAddress()).append("  fn=").append(e == 0 ? "?" : hex(e))
                  .append("  ").append(ins.toString()).append("\n");
            }
            sb.append("-- distinct functions: ").append(byFn.size()).append("\n");
            for (Map.Entry<Long, Integer> e : byFn.entrySet()) {
                sb.append("   fn ").append(hex(e.getKey())).append(" : ").append(e.getValue()).append(" store(s)\n");
            }
        }

        writeFile("step18_chainwrites.txt", sb.toString());
    }
}
