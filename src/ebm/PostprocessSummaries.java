
package ebm;

import java.io.*;
import java.util.List;

import org.jdom.Document;
import org.jdom.Element;
import org.jdom.input.SAXBuilder;
import org.jdom.output.Format;
import org.jdom.output.XMLOutputter;

/** Read abstract summaries and lookup snomed codes for detected mentions.  
 * @author rlsummerscales  
 */
public class PostprocessSummaries {

	/** read a summary file (in xml format) and return the resulting XML document 
	 * 
	 * @param filename name of summary file to read
	 * @return XML document or null if there was an error
	 */
	public static Document readSummary(String filename){
		try {
			// read xml file
			SAXBuilder builder = new SAXBuilder();
			Document doc = builder.build(filename);
			return doc;
		} catch (Exception e) { // error reading file
			System.out.println(e.getLocalizedMessage());
			e.printStackTrace();
			return null;
		}
	}
	
	/** Write summary to an xml file
	 * @param doc  XML document containing the summary
	 * @param filename name of the target XML file
	 * @return True if successful, False otherwise
	 */
	public static boolean writeSummary(Document doc, String filename){
		try {
			PrintWriter pw = new PrintWriter(new FileWriter(new File(filename)));
			Format format = Format.getPrettyFormat();
			format.setLineSeparator("\n");
			format.setEncoding("ISO-8859-1");
//			format.setOmitEncoding(true);
			XMLOutputter xmlOut = new XMLOutputter(format);
			xmlOut.output(doc, pw);
			pw.close();
		} catch (Exception e){
			System.out.println(e.getLocalizedMessage());
			e.printStackTrace();
			return false;
		}

		return true;
	}
	
	/** Read a summary in XML format, lookup snomed codes for detected mentions.
	 * Write modified summary back to original file
	 * @param filename is the name of the summary file
	 * @param models is the language model file that contains metamap & snomed lookups
	 */
	@SuppressWarnings("unchecked")
	public static void processSummary(String filename, LanguageModels models){
		// load summary
		Document doc = readSummary(filename);
		if(doc == null){
			System.out.println("Unable to load "+filename);
			return;
		} 
		System.out.println(filename + " loaded");
		
		Element root = doc.getRootElement();

		Element conditionsElement = root.getChild("ConditionsOfInterest");
		if(conditionsElement != null) {
			List<Element> cElements = conditionsElement.getChildren("Condition");
			for(Element child: cElements){
				lookupCodes(child, models);
			}
		}

		Element subjectElement = root.getChild("Subjects");
		if (subjectElement != null){
			Element eligibilityElement = subjectElement.getChild("Eligibility");
			List<Element> cElements = eligibilityElement.getChildren("Criteria");
			for(Element child: cElements){
				lookupCodes(child, models);
			}


			List<Element> gElements = subjectElement.getChildren("Group");
			for(Element child: gElements){
				lookupCodes(child, models);
			}
		}
		Element outcomesElement = root.getChild("Outcomes");
		if(outcomesElement != null) {
			List<Element> outElements = outcomesElement.getChildren();
			for(Element child: outElements){
				lookupCodes(child, models);
			}
		}
		
		
		// process outcome information
		
		
		// write abstract to file
		System.out.println("writing "+filename);				
		writeSummary(doc, filename);
//		writeSummary(doc, filename+".out.txt");
	
	}
	
	/** Given an XML element with a name node, find relevant snomed/umls codes for text in the name element
	 * @param element is the XML element containing a name element
	 * @param models is the language model that has loaded a metmap server
	 */
	public static void lookupCodes(Element element, LanguageModels models){
		// delete old codes if there
		element.removeChildren("CodedText");
		Element nameElement = element.getChild("Name");
		if(nameElement != null){
			String text = nameElement.getTextNormalize();
			List<Element> codeList = models.lookupCodes(text);
			if (codeList.isEmpty() == false){
				element.addContent(codeList);
			}		
		}

	}
	/** Read abstracts and generate phrases for each sentence 
	 * @param args = name of XML file
	 */
	public static void main(String[] args) {
		if(args.length < 1) {			
			System.out.println("USAGE: java PostprocessSummaries -snomed <FILE> <files> ");
			System.out.println("OPTIONS: ");
			System.out.println("-snomed <FILE>        path to RRF file containing both UMLS concept ids and snomed codes");
			System.out.println("-path        path to write output files");
			System.out.println("<files>         are xml files containing summaries (Note: orginal files are modified)");
			System.out.println();
			System.exit(-1);
		}
		LanguageModels models = new LanguageModels();		
	    int i = 0, summaryCount = 0; 
	    String snomedFile = "";
	    
		// process command line arguments
		for(i=0; i<args.length; i++){
			if(args[i].equalsIgnoreCase("-snomed")){
				snomedFile = args[++i];				
			} else {
				break;
			}
		}
		
	    
		// load tokenizer, postagger
	    System.out.print("Loading model files...");
	    models.initSnomed(snomedFile);
	    models.initMetaMap();
	    System.out.println("[completed]");
		
		try {
			
			// load summaries, process and write results to file
			while(i<args.length){
				System.out.println("Reading "+args[i]);
				processSummary(args[i], models);
				summaryCount++;
				i++;
			}
		}catch(Exception e) {
			System.out.println(e.getMessage());
			System.exit(-1);
		}		
		 
		System.out.println(summaryCount+" summaries");
	}
}
