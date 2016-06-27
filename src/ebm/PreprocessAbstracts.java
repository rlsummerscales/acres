
package ebm;

import java.io.*;

/** Read abstracts and apply preprocessing steps  
 * @author rlsummerscales  
 */
public class PreprocessAbstracts {

	/** Read abstracts and generate phrases for each sentence 
	 * @param args = name of XML file
	 */
	public static void main(String[] args) {
		if(args.length < 1) {			
			System.out.println("USAGE: java PreprocessAbstracts -snomed <FILE> -path PATH <files> ");
			System.out.println("OPTIONS: ");
			System.out.println("-nometamap        Do not lookup UMLS concept ids for sentences.");			
//			System.out.println("-snomed <FILE>        path to RRF file containing both UMLS concept ids and snomed codes");
			System.out.println("-path        path to write output files");
			System.out.println("<files>         are xml files containing abstracts");
			System.out.println();
			System.exit(-1);
		}
		LanguageModels models = new LanguageModels();		
	    int i = 0, sentenceCount = 0, absCount = 0; 
	    String path = "";
	    String reportPath = "";
//	    String snomedFile = "";
	    boolean loadMetamap = true;
	    long totalTime = 0;
		// process command line arguments
		for(i=0; i<args.length; i++){
			if(args[i].equalsIgnoreCase("-path")){
				path = args[++i];
//			} else if(args[i].equalsIgnoreCase("-snomed")){
//				snomedFile = args[++i];				
			} else if(args[i].equalsIgnoreCase("-nometamap")){
				loadMetamap = false;	
			} else if(args[i].equalsIgnoreCase("-reports")){
				reportPath = args[++i];
			} else {
				break;
			}
		}
		
	    
		// load tokenizer, postagger
	    System.out.print("Loading model files...");
//	    models.initSnomed(snomedFile);
	    models.initStanfordParser("models/stanford/englishPCFG.ser.gz");
//	    models.initStanfordParser("models/stanford/genia.ser.gz");
	    if(loadMetamap){
	    	models.initMetaMap();
	    }
	    System.out.println("[completed]");
	    
		long startTime = System.currentTimeMillis();
		try {
//			mPw.println("<?xml version=\"1.0\" encoding=\"MacRoman\" ?>\n<abstractlist>");
			PrintWriter errorPW = new PrintWriter(new FileWriter(new File("abstracts.error.txt")));
			
			// load abstracts, process and write results to file
			while(i<args.length){
				Abstract a = new Abstract();
				System.out.println("Reading "+args[i]);
				// load abstract
				if(!a.load(args[i], models, reportPath)){
					System.out.println("Unable to load "+args[i]);
					errorPW.println("Error in "+args[i]);
				} 
				// write abstract to file
				String filename = path+a.id+".raw.xml";
				System.out.println("writing "+filename);				
				a.writeXML(filename);

				absCount++;
				sentenceCount += a.sentences.size();
				i++;
			}
			errorPW.close();
		}catch(Exception e) {
			System.out.println(e.getMessage());
			System.exit(-1);
		}		
		long endTime = System.currentTimeMillis();
		totalTime = endTime - startTime;
		
		System.out.println(absCount+" abstracts");
		System.out.println(sentenceCount+" sentences");
		System.out.println("Total time (sec): "+totalTime/1000);
		System.out.println("Total time spent using MetaMap (sec): "+models.getMetaMapTime()/1000);
		System.out.println("Total time spent parsing (sec): "+models.getParsingTime()/1000);

	}
}
