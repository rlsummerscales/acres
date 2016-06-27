/** Word.java 
 *  Store a word and its features
 *  @author rlsummerscales
 */

package ebm;
import java.util.*;
import java.util.Map.Entry;

//import org.apache.tools.ant.taskdefs.Manifest.Attribute;
import org.jdom.Element;

import edu.stanford.nlp.ling.CoreAnnotations.*;
import edu.stanford.nlp.ling.CoreLabel;


public class Token {
	/** store grammatical or semantic relationship between this token and another token in the sentence */
	public class Relationship{
		/** index of token related to this one (range is [1, n] where n is number of tokens in sentence) */
		int tokenIndex = -1; 
		/** label describing type of relationship */
		String type = "";
		/** the specific type of the collapsed relationship */
		String specific = "";
		
		public Relationship(String type, String specific, int idx){
			this.type = type;
			this.tokenIndex = idx;
			this.specific = specific;
		}
		
		/** return and XML element containing the relationship 
		 * @param name is the name if the XML element
		 * */
		public Element getXMLElement(String name){
			Element rElement = new Element(name);
			rElement.setAttribute("type", this.type);
			if(this.specific != null && this.specific.length() > 0){
				rElement.setAttribute("specific", this.specific);				
			}
			rElement.setAttribute("idx", Integer.toString(this.tokenIndex));
			return rElement;
		}
	}
	
	/** lemma for the token identified by StanfordCore */
	String lemma = "";
	/** tokens index in sentence */
	int index = -1;
	/** list of UMLS concepts that have been mapped to this token */
	HashMap<String,UmlsConcept> umlsConcepts = new HashMap<String,UmlsConcept>();
	/** Chunk tag (B, I, O) representing whether token in a phrase annotated by metamap */
	String metamapChunkTag = "O";
	/** annotation tags index by tag name */
	HashMap<String, XmlTag> tags = new HashMap<String, XmlTag>();
	/** list of dependency relationships where token is governor */
    Vector<Relationship> dependents = new Vector<Relationship>();
	/** list of dependency relationships where token is dependent */
    Vector<Relationship> governors = new Vector<Relationship>();
    /** relationship with token's parent in parse tree */
    Relationship parent = null;
    /** children of token in parse tree */
    Vector<Relationship> children = new Vector<Relationship>();
    
	/** original token object produced by stanfordCore system */
	CoreLabel coreLabel = null;

	private static final String integerPattern = "-?\\d+";
	private static final String numberPattern = "-?\\d*\\.?\\d+";
    	
	public static final HashSet<String> specialTermSet;
	static {
		HashSet<String> hMap = new HashSet<String>();
		hMap.add("itt_analysis");
		hMap.add("per_protocol_analysis");
		hMap.add("95_confidence_interval");
		hMap.add("odds_ratio");
		hMap.add("hazard_ratio");
		hMap.add("absolute_risk_reduction");
		hMap.add("absolute_risk_increase");
		hMap.add("number_needed_to_treat");
		hMap.add("number_needed_to_harm");
		hMap.add("relative_risk_reduction");
		hMap.add("relative_risk_increase");
		hMap.add("relative_risk");

		specialTermSet = hMap;
	}

	/** create a token for a given word*/
	Token(String text, int idx){
		this.coreLabel = new CoreLabel();
		this.setText(text);
    	this.index = idx;
	}
	/** create a token given a stanford token object and the token's index in the sentence */
    Token(CoreLabel coreToken, int idx){
    	this.coreLabel = coreToken;
    	this.lemma = coreToken.get(LemmaAnnotation.class);
    	this.index = idx;
    	// make sure that special terms are replaced with token "SPECIAL_TERM"
		if(specialTermSet.contains(this.getText())){
			this.setText(this.getText());
		}

    }

	/** return an XML element containing all important token information */
	public Element getXMLElement() {
		Element tElement = new Element("token");
		tElement.setAttribute("id", Integer.toString(index));
		tElement.setAttribute("text", getText());
		if(lemma != null && lemma.equalsIgnoreCase(getText()) == false){
			// only include lemma if different from original word
			tElement.setAttribute("lemma", lemma);
		}
		
		tElement.setAttribute("pos", this.getPOS());
				
        if(umlsConcepts.isEmpty() == false){
        	for(UmlsConcept uc: umlsConcepts.values()){
        		tElement.addContent(uc.getXMLElement());
        	}
        }
		if(dependents.isEmpty() == false){
			for(Relationship relationship: dependents){
				Element rElement = relationship.getXMLElement("dep");
				tElement.addContent(rElement);
			}
		}

		if(governors.isEmpty() == false){
			for(Relationship relationship: governors){
				Element rElement = relationship.getXMLElement("gov");
				tElement.addContent(rElement);
			}
		}

		if(tags.isEmpty() == false){
			for(Entry<String, XmlTag> tagEntry: tags.entrySet()){
				XmlTag xmlTag = tagEntry.getValue();
				Element aElement = new Element("annotation");
				aElement.setAttribute("type", xmlTag.name);
				for(Entry<String, String> attribEntry: xmlTag.attributes.entrySet()){
					Element e = new Element(attribEntry.getKey());
					e.addContent(attribEntry.getValue());
					aElement.addContent(e);
				}
				tElement.addContent(aElement);
			}
		}
		
		return tElement;
	}

	
	/** return index in sentence of first character of token */
	public int getStartIdx(){
		return coreLabel.beginPosition();
//		return token.get(CharacterOffsetBeginAnnotation.class);
	}
	
	/** return index in sentence of last character after the end of an annotation */
	public int getEndIdx(){
		return coreLabel.endPosition();
//		return token.get(CharacterOffsetEndAnnotation.class);
	}
	
	/** set the part of speech tag for the token */
	public void setPOS(String pos){
		this.coreLabel.set(PartOfSpeechAnnotation.class, pos);
	}
	
	/** return the part of speech tag for the token */
	public String getPOS(){
		return this.coreLabel.getString(PartOfSpeechAnnotation.class);
	}
	
	/** set the text string for this token */
	public void setText(String text){
		// if the token was a special term, it has an annotation for this term.
		// since we are changing the text, delete the annotation that went along with it.
		if(this.getText().equalsIgnoreCase("SPECIAL_TERM")){
			for(Iterator<String> termIter = specialTermSet.iterator(); termIter.hasNext();){
				String term = termIter.next();
				if(this.hasTag(term)){
					this.removeTag(term);
				}
			}
		}
		// new text is that of a special term (e.g. risk reduction, number needed to treat)
		// use a generic string for the term, but add an annotation specifying the type of special term
		if(specialTermSet.contains(text)){
			this.addTag(text);
			text = "SPECIAL_TERM";
		} 
		this.coreLabel.setWord(text);
		this.coreLabel.setValue(text);
	}
	
	/** get the text value for this token or an empty string if it is null.*/
	public String getText(){
		if(this.coreLabel.word() == null){
			return "";
		}
		
		return this.coreLabel.word();
	}

	/** return text for display purposes. convert '-LRB-' to '(' */
	public String getDisplayText() {
		if(this.getText().equalsIgnoreCase("-lrb-")){
			return "(";
		}else if(this.getText().equalsIgnoreCase("-rrb-")){
			return ")";
		}else {
			return this.getText();
		}
	}
	/** does the text equal a given string (case insensitive)*/
	public boolean equals(String s){
		String text = getText();
		return text.equalsIgnoreCase(s);
	}
	
	/** is the token an integer */
	public boolean isInteger() {
		return this.getText().matches(integerPattern);
	}

	/** is the token a number (int or float) */
	public boolean isNumber() {
		return this.getText().matches(numberPattern);
	}
	
	/** returns value of string if a number or 0 if not */
	public Float getValue(){
		if(this.isNumber()){
			Float f = Float.parseFloat(this.getText());
			return f;
		} else {
			return (float) 0.0;
		}
	}

	/** add a new UMLS concept to list of UMLS concepts for this token */
	public void addUmlsConcept(UmlsConcept uc){
		if(umlsConcepts.containsKey(uc.id) == false){
			umlsConcepts.put(uc.id, uc);
		}
	}
	
	/** erase tag list */
	public void clearTags(){
		tags = new HashMap<String, XmlTag>();
	}
	
	/** add an xmltag to hash of tags */
	public void addTag(XmlTag tag){
		tags.put(tag.name, tag);
	}

	/** add an xmltag given the name of the tag to hash of tags */
	public void addTag(String name){
		this.addTag(new XmlTag(name));
	}

	/** add a list of xmltags */
	public void addTags(Vector<XmlTag> taglist){
		for(Iterator<XmlTag> tIter=taglist.iterator(); tIter.hasNext();){
			XmlTag tag = tIter.next();
			addTag(tag);
		}
	}
	
	/** remove a tag with given name from list of xmltags */
	public void removeTag(String name){
		XmlTag tag = this.tags.get(name);
		if(tag != null){
			this.tags.remove(tag);
		}
	}
	
	/** check if the token has a tag with a given name */
	public boolean hasTag(String name){
		return this.tags.containsKey(name);
	}
	
	/** add a new dependency relationship where token is governor */
	public void addDependent(String type, String specific, int depIdx){
		this.dependents.add(new Relationship(type, specific, depIdx));
	}

	/** add a new dependency relationship where token is dependent */
	public void addGovernor(String type, String specific, int govIdx){
		this.governors.add(new Relationship(type, specific, govIdx));
	}

	public String toString() {
		return this.getText();
	}
	

}
