// W108 · Question (C) resolved properly: at each 0x0047C550 / 0x0047C4D0 call site,
// walk BACKWARD from the call on Ghidra instruction boundaries and classify the value
// pushed as `whichChain`. Distinguishes:
//   CONST0  - push 0                      => chain A
//   CONSTnz - push imm8/imm32 != 0        => chain B
//   VAR     - push <reg>                  => must be traced; report the defining insn
// Also resolves 0x0047C520 (no arg, chain A hardcoded at 0x0047C52A).

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.scalar.Scalar;
import java.io.*;
import java.util.*;

public class ChainC extends GhidraScript {

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

    /** instructions of a function in address order */
    List<Instruction> listing(Function f) {
        List<Instruction> out = new ArrayList<>();
        InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
        while (it.hasNext()) out.add(it.next());
        return out;
    }

    /** Walk back up to `maxBack` instructions from the instruction at callAddr. */
    List<Instruction> back(Instruction call, int maxBack) {
        List<Instruction> out = new ArrayList<>();
        if (call == null) return out;
        Instruction cur = call;
        for (int i = 0; i < maxBack; i++) {
            Instruction prev = cur.getPrevious();
            if (prev == null) break;
            out.add(prev);
            cur = prev;
        }
        Collections.reverse(out);
        return out;
    }

    String classifyPush(Instruction ins, Function f) {
        if (ins == null) return null;
        String s = ins.toString();
        if (!s.toUpperCase().startsWith("PUSH")) return null;
        if (ins.getNumOperands() != 1) return "PUSH? " + s;
        Object[] ops = ins.getOpObjects(0);
        if (ops.length > 0 && ops[0] instanceof Scalar) {
            long v = ((Scalar) ops[0]).getUnsignedValue();
            return (v == 0) ? "CONST0 (chain A)" : ("CONST" + v + " (chain B)");
        }
        // register: trace its last definition within the function, before this push
        String reg = ins.getDefaultOperandRepresentation(0).toUpperCase();
        String def = null;
        Instruction cur = ins.getPrevious();
        int guard = 0;
        while (cur != null && guard++ < 120) {
            if (cur.getMnemonicString().toUpperCase().startsWith("MOV")
                || cur.getMnemonicString().toUpperCase().startsWith("LEA")
                || cur.getMnemonicString().toUpperCase().startsWith("XOR")
                || cur.getMnemonicString().toUpperCase().startsWith("MOVZX")
                || cur.getMnemonicString().toUpperCase().startsWith("MOVSX")) {
                String t = cur.toString().toUpperCase();
                if (t.startsWith("MOV " + reg + ",") || t.startsWith("LEA " + reg + ",")
                    || t.startsWith("XOR " + reg + ",") || t.startsWith("MOVZX " + reg + ",")
                    || t.startsWith("MOVSX " + reg + ",")) {
                    def = cur.getAddress() + "  " + cur.toString();
                    break;
                }
            }
            cur = cur.getPrevious();
        }
        return "REG " + reg + "  <- " + (def == null ? "<not found in fn>" : def);
    }

    @Override
    public void run() throws Exception {
        long[] sites550 = { 0x005085D4L, 0x005085E0L, 0x00586816L, 0x005FC4A0L, 0x005FD2BAL,
                            0x0062AB97L, 0x006D57C5L, 0x006E1896L, 0x006E1940L, 0x006E1A0DL };
        long[] sites4d0 = { 0x0047BDC4L, 0x0047C06BL, 0x0047C74AL, 0x0047C813L,
                            0x004812A7L, 0x004812C6L };

        StringBuilder sb = new StringBuilder();
        FunctionManager fm = currentProgram.getFunctionManager();

        sb.append("=== 0x0047C550 call sites: the single stack arg is whichChain ===\n");
        for (long s : sites550) {
            Instruction call = currentProgram.getListing().getInstructionAt(addr(s));
            Function f = fm.getFunctionContaining(addr(s));
            sb.append("\n-- call @ ").append(hex(s)).append("   in ").append(f == null ? "?" : hex(f.getEntryPoint().getOffset())).append("\n");
            sb.append("   ").append(call == null ? "<no insn>" : call.toString()).append("\n");
            List<Instruction> b = back(call, 6);
            for (Instruction i : b) sb.append("     ").append(i.getAddress()).append("  ").append(i.toString()).append("\n");
            // innermost push = the whichChain arg
            String verdict = null;
            for (int k = b.size() - 1; k >= 0; k--) {
                String c = classifyPush(b.get(k), f);
                if (c != null) { verdict = "   whichChain <- " + c + "   [from " + b.get(k).getAddress() + "]"; break; }
            }
            sb.append(verdict == null ? "   whichChain <- <PUSH NOT FOUND in 6 insns>\n" : verdict + "\n");
        }

        sb.append("\n\n=== 0x0047C4D0 call sites: TWO stack args (ret 8); first-pushed = whichChain ===\n");
        for (long s : sites4d0) {
            Instruction call = currentProgram.getListing().getInstructionAt(addr(s));
            Function f = fm.getFunctionContaining(addr(s));
            sb.append("\n-- call @ ").append(hex(s)).append("   in ").append(f == null ? "?" : hex(f.getEntryPoint().getOffset())).append("\n");
            sb.append("   ").append(call == null ? "<no insn>" : call.toString()).append("\n");
            List<Instruction> b = back(call, 8);
            for (Instruction i : b) sb.append("     ").append(i.getAddress()).append("  ").append(i.toString()).append("\n");
            // collect pushes innermost-first
            List<Instruction> pushes = new ArrayList<>();
            for (int k = b.size() - 1; k >= 0; k--) {
                if (b.get(k).toString().toUpperCase().startsWith("PUSH")) pushes.add(b.get(k));
            }
            if (pushes.size() >= 2) {
                sb.append("   arg1 (wanted, innermost) <- ").append(classifyPush(pushes.get(0), f)).append("\n");
                sb.append("   arg2 (whichChain, outer) <- ").append(classifyPush(pushes.get(1), f)).append("\n");
            } else {
                sb.append("   PUSHES FOUND = ").append(pushes.size()).append(" (expected 2)\n");
            }
        }

        sb.append("\n\n=== 0x0047C520: no argument; chain A is hardcoded ===\n");
        Instruction movE4 = currentProgram.getListing().getInstructionAt(addr(0x0047C52AL));
        sb.append("   ").append(movE4 == null ? "?" : movE4.getAddress() + "  " + movE4.toString()).append("\n");

        writeFile("step16_whichchain.txt", sb.toString());
    }
}
