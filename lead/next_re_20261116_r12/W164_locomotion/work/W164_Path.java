// W164: pathfinding callers + gating context. Also find callers of Locomotion Process candidates.
// @category W164
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class W164_Path extends GhidraScript {
    void xrefs(long t, String label) throws Exception {
        Address a=currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
        println("=== XREFS to "+label+" @"+a+" ===");
        ReferenceIterator it=currentProgram.getReferenceManager().getReferencesTo(a);
        int n=0;
        while(it.hasNext()){
            Reference r=it.next();
            if(!r.getReferenceType().isCall()) continue;
            Function cf=currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
            println("  call@"+r.getFromAddress()+" in "+(cf==null?"?":cf.getEntryPoint())+
                    (cf==null?"":" size="+cf.getBody().getNumAddresses()));
            n++;
        }
        if(n==0) println("  (no rel call xrefs)");
    }
    void dump(long s,long e,String title)throws Exception{
        AddressFactory af=currentProgram.getAddressFactory();
        Address st=af.getDefaultAddressSpace().getAddress(s), en=af.getDefaultAddressSpace().getAddress(e);
        println("=== "+title+" ===");
        InstructionIterator ii=currentProgram.getListing().getInstructions(new AddressSet(st,en),true);
        while(ii.hasNext()){Instruction ins=ii.next();println("  "+ins.getAddress()+": "+ins.toString());}
    }
    public void run() throws Exception {
        xrefs(0x004CBBA0L,"FootClass::CallFindPath");
        xrefs(0x0042C900L,"PathFinder::FindPath");
        xrefs(0x004D3920L,"FootClass::UpdatePathfinding?");
        xrefs(0x004DA530L,"FootClass::AI");
        // dump bytes at throttle global 0x8871E0 (read dword value stored there, static = pointer)
        int p=currentProgram.getMemory().getInt(currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(0x008871E0L));
        println("=== [0x8871E0] = "+Integer.toHexString(p)+" ; +0x1808 field at "+
                Integer.toHexString(p+0x1808)+" ===");
    }
}
