// W164: find callers of Locomotion factories + dump context to see store offset in FootClass
// @category W164
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class W164_Factory extends GhidraScript {
    void dump(long s,long e,String title)throws Exception{
        AddressFactory af=currentProgram.getAddressFactory();
        Address st=af.getDefaultAddressSpace().getAddress(s),en=af.getDefaultAddressSpace().getAddress(e);
        println("=== "+title+" ===");
        InstructionIterator ii=currentProgram.getListing().getInstructions(new AddressSet(st,en),true);
        while(ii.hasNext()){Instruction ins=ii.next();println("  "+ins.getAddress()+": "+ins.toString());}
    }
    public void run()throws Exception{
        dump(0x006C4010L,0x006C40A0L,"Drive Locomotion factory 0x6C4010");
        Address a=currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(0x006C4010L);
        println("=== callers of factory 0x6C4010 ===");
        ReferenceIterator it=currentProgram.getReferenceManager().getReferencesTo(a);
        while(it.hasNext()){Reference r=it.next();if(!r.getReferenceType().isCall())continue;
            Function cf=currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
            println("  call@"+r.getFromAddress()+" in "+(cf==null?"?":cf.getEntryPoint())+
                (cf==null?"":" size="+cf.getBody().getNumAddresses()));}
    }
}
