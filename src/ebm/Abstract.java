
package ebm;

import java.io.*;
import java.util.*;
import org.jdom.Document;
import org.jdom.Element;
import org.jdom.ProcessingInstruction;
import org.jdom.input.SAXBuilder;
import org.jdom.output.Format;
import org.jdom.output.XMLOutputter;

/**
 * Class for storing a medical abstract
 * @author rodney summerscales
 */
public class Abstract {
	/** all sentences (including title) in abstract */
	public Vector<Sentence> sentences = new Vector<Sentence>();
	/** title of paper */
	public Vector<Sentence> title = new Vector<Sentence>();
    /** unique id for abstract */
	public String id = "";
	/** list of mesh topics for the article */
	public Element meshHeadingList = null;
	/** information regarding journal and publicatioin date */
	public Element journal = null;
	/** names and affiliations of the authors */
	public Element authorList = null;
	/** list of classifications for the article */
	public Element publicationTypeList = null;
	/** Country journal published in */
	public Element country = null;
	/** list of sentences describing the affiliations of the authors of the study */
	public Vector<Sentence> affiliations = new Vector<Sentence>();
	public NctReport nctReport = null;

	/** load abstract from xml file
	 * @param file  name of file to load
	 * @param models object containing opennlp tokenizer & tagger models
	 * @return true if successfull, false otherwise
	 * @note this function loads abstracts in the new (post-May 2011) xml format
	 */
	@SuppressWarnings("unchecked")
	public boolean load(String file, LanguageModels models, String reportPath) {
		// load file
		try {
			// read xml file
			SAXBuilder builder = new SAXBuilder();
			Document doc = builder.build(file);
			

			// build list of sentences
			sentences.clear();
			// start at root of xml tree (Abstract element)
			Element root = doc.getRootElement();
			
			Element pubmedArticle = root.getChild("PubmedArticle");
			Element medlineCitationElement = pubmedArticle.getChild("MedlineCitation");
			id = medlineCitationElement.getChildTextNormalize("PMID");
			Element article = medlineCitationElement.getChild("Article");
			journal = article.getChild("Journal");
			authorList = article.getChild("AuthorList");
			publicationTypeList = article.getChild("PublicationTypeList");
			

			// process title. title may contain one or more sentence like things
			// add these to list of sentences for abstract
			Element tElement = article.getChild("ArticleTitle");
			Vector<RawTextFragment> fragmentList = XmlUtil.toRawTextFragmentList(tElement);			
			title = models.AnnotateAndReturnSentences(fragmentList, "title", "title", true);
			
			Vector<Sentence> sList = null;
			List<Element> absTextList = article.getChild("Abstract").getChildren("AbstractText");
			for (Element abstractText: absTextList) {
				// convert text with xml tags to list of strings with associated tags
				// also preprocess each of the fragments
				fragmentList = XmlUtil.toRawTextFragmentList(abstractText);
				String sectionLabel = abstractText.getAttributeValue("Label");
				String nlmCategory = abstractText.getAttributeValue("NlmCategory");				
				
				// apply stanford core nlp and convert result to list of sentences
				sList = models.AnnotateAndReturnSentences(fragmentList, sectionLabel, nlmCategory, true);
				sentences.addAll(sList);						
			}

			// read affiliation
			tElement = article.getChild("Affiliation");
			if(tElement != null){
				fragmentList = XmlUtil.toRawTextFragmentList(tElement);
				affiliations.addAll(models.AnnotateAndReturnSentences(fragmentList, "affiliation", "affiliation", false));
			}
			
			country = medlineCitationElement.getChild("MedlineJournalInfo").getChild("Country");
			
            // read registry numbers (if any)
//            try{
//            	List<Element> dbList = article.getChild("DataBankList").getChildren("DataBank");
//            	for(Element db: dbList){
//            		List<Element> ids = db.getChild("AccessionNumberList").getChildren("AccessionNumber");
//            		for(Element idNode: ids){
//            			String id = idNode.getTextTrim();
//            			System.out.println(id);
//            			addReportInformation(id, reportPath, models);
//
//            		}
//            	}
//            } catch (Exception e){
//
//            }
			// read mesh terms
//			meshHeadingList = medlineCitationElement.getChild("MeshHeadingList");
		} catch (Exception e) { // error reading file
			System.out.println(e.getLocalizedMessage());
			e.printStackTrace();
			return false;
		}
		
		return true;
	}
	
	/** attempt to open a report file (NCT for now) and extract the key information and add it to the abstract */
//	private boolean addReportInformation(String id, String reportPath, LanguageModels models){
//		String filename = reportPath+"/"+id+".xml";
//
//		try {
//			// read xml file
//			SAXBuilder builder = new SAXBuilder();
//			Document doc = builder.build(filename);
//			Element root = doc.getRootElement();
//			if(id.startsWith("NCT")){
//				nctReport = new NctReport(root, models);
//			}
//		} catch (FileNotFoundException e){
//			System.out.println("Error: unable to read "+filename);
//			return false;
//		} catch (Exception e) { // error reading file
//			System.out.println(e.getLocalizedMessage());
//			e.printStackTrace();
//			return false;
//		}
//		return false;
//	}

	/** return an XML element containing the abstract */
	public Element getXMLElement(){
		Element aElement = new Element("abstract");
		aElement.setAttribute("id", id);
		
		Element pInfoElement = new Element("PublicationInformation");
		if (journal != null) {
			pInfoElement.addContent((Element) journal.clone());
		}
		
		if (country != null) {
			pInfoElement.addContent((Element) country.clone());
		}

		if (authorList != null) {
			pInfoElement.addContent((Element) authorList.clone());
		}

		if (publicationTypeList != null) {
			pInfoElement.addContent((Element) publicationTypeList.clone());
		}
		aElement.addContent(pInfoElement);
		
		Element tElement = new Element("title");
		aElement.addContent(tElement);
		for(Sentence sentence: title){
			Element sElement = sentence.getXMLElement();
			tElement.addContent(sElement);
		}	

		if(affiliations.size() > 0){
			Element affElement = new Element("affiliation");
			aElement.addContent(affElement);			
			for(Sentence sentence: affiliations){
				Element sElement = sentence.getXMLElement();
				affElement.addContent(sElement);
			}		
		}

		Element bElement = new Element("body");
		aElement.addContent(bElement);
		for(Sentence sentence: sentences){
			Element sElement = sentence.getXMLElement();
			bElement.addContent(sElement);
		}		
		
		if(nctReport != null){
			aElement.addContent(nctReport.getXMLElement());
		}
		if(meshHeadingList != null){
			aElement.addContent((Element) meshHeadingList.clone());
		}
		return aElement;
	}
	
	/** Write abstract to output stream (in XML format) */
	public void writeXML(PrintWriter pw){
		Format format = Format.getPrettyFormat();
		format.setLineSeparator("\n");
		XMLOutputter xmlOut = new XMLOutputter(format);
		Element aElement = getXMLElement();
		String s = xmlOut.outputString(aElement);
		pw.println(s);
	}
	
	/** write abstract (in XML format) out to a file */
	public boolean writeXML(String filename){
		try {
			PrintWriter pw = new PrintWriter(new FileWriter(new File(filename)));
			Format format = Format.getPrettyFormat();
			format.setLineSeparator("\n");
			format.setEncoding("ISO-8859-1");
//			format.setEncoding("UTF-8");

			//			format.setOmitEncoding(true);
			XMLOutputter xmlOut = new XMLOutputter(format);
			Element aElement = getXMLElement();
			Document doc = new Document();
			ProcessingInstruction pi =  new ProcessingInstruction("xml-stylesheet",
					"type='text/xsl' href='http://www.andrews.edu/~summersc/abstract.xsl'");
			doc.addContent(pi);
			doc.addContent(aElement);
			
//			aElement.addContent((Element) pubmedArticle.clone());
			

			xmlOut.output(doc, pw);
			pw.close();
		} catch (Exception e){
			System.out.println(e.getLocalizedMessage());
			e.printStackTrace();
			return false;
		}
		
		return true;
	}
	
}

