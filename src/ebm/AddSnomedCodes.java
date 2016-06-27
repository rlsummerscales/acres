package ebm;

public class AddSnomedCodes
{
	public static void main(String[] args) {
		if(args.length < 1) {			
			System.out.println("USAGE: java AddSnomedCodes -snomed <FILE> -input <PATH> -output <PATH> ");
			System.out.println("-snomed <FILE>        path to RRF file containing both UMLS concept ids and snomed codes");
			System.out.println("-input <PATH>         path of directory containing XML files to read");
			System.out.println("-output <PATH>        where to write the new abstract files with snomed codes");
			System.out.println();
			System.exit(-1);
		}
		String snomedFile = "";
		String inputPath = "", outputPath = "";
        int i = 0;
        
		// process command line arguments
		for(i=0; i<args.length; i++){
			if(args[i].equalsIgnoreCase("-input")){
				inputPath = args[++i];
			} else if(args[i].equalsIgnoreCase("-output")){
				outputPath = args[++i];
			} else if(args[i].equalsIgnoreCase("-snomed")){
				snomedFile = args[++i];				
			} else {
				break;
			}
		}

		XMLManager manager=new XMLManager();
		manager.modify(snomedFile, inputPath, outputPath);
	}
}