package ebm;

import java.util.Vector;

import org.jdom.Element;

import gov.nih.nlm.nls.metamap.*;

/** 
 * Store information about a UMLS match between a word/phrase and a concept in the UMLS metathesaurus.
 * @author rlsummerscales
 */

public class UmlsConcept {
	
	/** UMLS concept id */
	String id = "";
	/** SNOMED CT code */
	String snomedCode = "";
	/** list of UMLS semantic types */
	Vector<String> types = new Vector<String>();
    /** list of sources (RXNORM, SNOMEDCT, or OTHER) */
	Vector<String> sources = new Vector<String>();
	/** mapping score assigned by metamap (between 0 and 1000) */
	int score = 0;
	/** has metamap determined that this concept is negated? */
	boolean isNegated = false;
	
	UmlsConcept(Ev metamapEv){
		try {
			id = metamapEv.getConceptId();
			score = -metamapEv.getScore();
			for(String semType: metamapEv.getSemanticTypes()){
				types.add(semType);
			}
			for(String source: metamapEv.getSources()){
				if(source.equalsIgnoreCase("snomedct") || source.equalsIgnoreCase("rxnorm")){
					sources.add(source);
				} 
			}
		} catch (Exception e) {
			System.out.println(e.getLocalizedMessage());
			e.printStackTrace();
		}
		
	}
	
	public Element getXMLElement(){
		Element uElement = new Element("umls");
		uElement.setAttribute("id", id);
		uElement.setAttribute("score", Integer.toString(score));
		if(isNegated){
			uElement.setAttribute("negated", "true");
		} else {
			uElement.setAttribute("negated", "false");
		}
		if(snomedCode.isEmpty() == false){
			uElement.setAttribute("snomed", snomedCode);
		}
		for(String type: types){
			Element typeElement = new Element("type");
			typeElement.addContent(type);
			uElement.addContent(typeElement);
		}

		if(sources.size() > 0){
			for(String source: sources){
				Element sourceElement = new Element("source");
				sourceElement.addContent(source);
				uElement.addContent(sourceElement);
			}
		}

		return uElement;
	}

}

