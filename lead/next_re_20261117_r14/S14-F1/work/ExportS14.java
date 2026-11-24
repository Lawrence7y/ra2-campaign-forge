import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;

import java.io.PrintWriter;

public class ExportS14 extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outPath = getScriptArgs()[0];
        PrintWriter out = new PrintWriter(outPath, "UTF-8");
        String[][] ranges = {
            {"004F8440", "004F9370", "HouseUpdate"},
            {"006F0AB0", "006F0FB8", "AITriggerEval"},
            {"0041E720", "0041EAA9", "ConditionMet"},
            {"006E8A90", "006E8DE1", "TeamCtor"},
            {"006F09C0", "006F0A6E", "CreateTeam"},
            {"004DA530", "004DAF48", "FootAI"},
            {"006718D0", "00671960", "AITriggerWeightsINI"},
            {"00670D00", "00670D60", "BuildSpeedINI"},
            {"0066FDE0", "0066FE40", "AIAlternateCreditINI"},
            {"00670150", "006701E0", "CampaignMoneyINI"}
        };
        out.println("; Ghidra 12.1.4 headless -noanalysis, raw disassembly via Ghidra API");
        for (String[] r : ranges) {
            Address start = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(Long.parseUnsignedLong(r[0], 16));
            Address end = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(Long.parseUnsignedLong(r[1], 16));
            out.println("\n===== " + r[2] + " [" + r[0] + "," + r[1] + ") =====");
            Address a = start;
            int guard = 0;
            while (a.compareTo(end) < 0 && guard++ < 100000) {
                boolean ok = disassemble(a);
                Instruction ins = getInstructionAt(a);
                if (ins == null) {
                    a = a.add(1);
                    continue;
                }
                out.printf("%08X  %-20s %-8s %s%n",
                    ins.getAddress().getOffset(),
                    bytesToHex(ins.getBytes()),
                    ins.getMnemonicString(),
                    ins.toString());
                Address next = ins.getAddress().add(ins.getLength());
                if (next.compareTo(a) <= 0) next = a.add(1);
                a = next;
            }
        }
        out.close();
        println("S14-F1 Ghidra export written to " + outPath);
    }

    private String bytesToHex(byte[] b) {
        StringBuilder sb = new StringBuilder();
        for (byte x : b) sb.append(String.format("%02x", x & 0xff));
        return sb.toString();
    }
}
