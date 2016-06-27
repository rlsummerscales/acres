
package ebm;

import java.util.*;

import org.jdom.Element;
import java.io.StringReader;

import edu.stanford.nlp.parser.lexparser.LexicalizedParser;
//import edu.stanford.nlp.objectbank.TokenizerFactory;
//import edu.stanford.nlp.process.CoreLabelTokenFactory;
import edu.stanford.nlp.process.DocumentPreprocessor;
//import edu.stanford.nlp.process.PTBTokenizer;
import edu.stanford.nlp.process.PTBTokenizer.PTBTokenizerFactory;
import edu.stanford.nlp.ling.HasWord;  
import edu.stanford.nlp.trees.*;


//import edu.stanford.nlp.ling.CoreAnnotations.*;
//import edu.stanford.nlp.pipeline.*;
//import edu.stanford.nlp.util.*;
import gov.nih.nlm.nls.metamap.*;

/** LanguageModels.java 
 *  Store loaded tokenizer, tagger, etc. models
 *  @author rlsummerscales
 */
public class LanguageModels {
	private MetaMapApi metamap = null;
	
	private SnomedLookup snomed = null;
	private boolean metamapInitialized = false;
	
	/** stanford parser */
	private LexicalizedParser parser = null;
    private GrammaticalStructureFactory gsf = null;
	
    private long metamapTime = 0;
    private long parsingTime = 0;
    
    /** initialize snomed lookup database */
    public void initSnomed(String snomedFilePath){
    	if(snomedFilePath.isEmpty() == false){
    		snomed = new SnomedLookup(snomedFilePath);
    	}
    	metamapTime = 0;
    	parsingTime = 0;
    }
    
    /** return the cumulative amount of time spent running metamap */
    public long getMetaMapTime() {
    	return metamapTime;
    }

    /** return the cumulative amount of time spent parsing sentences */
    public long getParsingTime() {
    	return parsingTime;
    }

    /** return the snomed code (if any) for a term with the given umls concept id */
    public String getSnomedCode(String umlsId){
    	if(snomed != null){
    		return snomed.getSnomedId(umlsId);
    	} else {
    		return "";
    	}
    }
    
    /** load parser model */
    public void initStanfordParser(String modelFilename){
    	parser = LexicalizedParser.loadModel(modelFilename);
    	TreebankLanguagePack tlp = new PennTreebankLanguagePack();
    	gsf = tlp.grammaticalStructureFactory();
    }
    
    
    
    /** tokenize, sentence split, pos tag, and parse a list of (possibly tagged) text fragments 
     * @param fragmentList is list of text fragments
     * @param sectionLabel is label (if any) for section of abstract containing text fragments
     * @param nlmCategory is the NLM category label assigned to the section of the abstract containing text fragments
     * @return the resulting list of sentences objects
     */
    public Vector<Sentence> AnnotateAndReturnSentences(Vector<RawTextFragment> fragmentList, 
    		String sectionLabel, String nlmCategory, boolean parseText) {
    	Vector<Sentence> sList = new Vector<Sentence>();
        long startTime;
        long endTime;

		// build string from fragments
		String rawText = "";
		for (RawTextFragment fragment: fragmentList){
			rawText = rawText + fragment.text + " ";
		}
		
    	Iterator<RawTextFragment> fragIter = fragmentList.iterator();
    	RawTextFragment curFragment = fragIter.next();
    	int curFragmentEndIdx = curFragment.text.length();
    	DocumentPreprocessor dp = new DocumentPreprocessor(new StringReader(rawText));
    	dp.setTokenizerFactory(PTBTokenizerFactory.newCoreLabelTokenizerFactory(null));
    	
		// sentence segment, tokenize (in DocumentPreprocessor), and parse the AbstractText string
	    for (List<HasWord> tokenList : dp) {
	        // create new sentence element and match up tokens with their annotations	    	
	    	Sentence sentence = new Sentence(tokenList, sectionLabel, nlmCategory);
	        for(Token token: sentence.getTokens()){
	        	int tokenStartIdx = token.getStartIdx();
//	        	System.out.print(token.getText()+" ");
	        	if(tokenStartIdx > curFragmentEndIdx && fragIter.hasNext()) {
	        		// token in next fragment
	        		curFragment = fragIter.next();
	        		curFragmentEndIdx += curFragment.text.length()+1;
	        		if (tokenStartIdx > curFragmentEndIdx) {
	        			System.err.println("ERROR:  Token not in next fragment.");
	        			System.out.println(token.getText()+"_"+token.getStartIdx()+"_"+token.getEndIdx());
	        			System.out.println(curFragment.text+"_"+curFragmentEndIdx);
	        			System.exit(1);
	        		}
	        	}

	        	// set tags for current element to be tags for current fragment
	        	token.addTags(curFragment.tags);
	        }	        
	    	
	        if(parseText){
	        	startTime = System.currentTimeMillis();
	        	// parse the sentence
	        	sentence.parse(parser, gsf);
	        	endTime = System.currentTimeMillis();
	        	parsingTime += endTime - startTime;
	        }

	        startTime = System.currentTimeMillis();
	        // annotate terms in sentence using metamap
	        metamapAnnotate(sentence);
	        endTime = System.currentTimeMillis();
	        metamapTime += endTime - startTime;
    		
    		sList.add(sentence);
    	}

    	return sList;
    }
	

	/** set options for metamap */
	public void initMetaMap(){
		metamap = new MetaMapApiImpl();		
//		metamap.setOptions("-R SNOMEDCT -J aapp,acab,anab,anst,antb,bacs,bact,bdsu,cgab,clna,clnd,diap,dysn,horm,imft,lbpr,lbtr,medd,topp,vita,phsu");
//		metamap.setOptions("-R SNOMEDCT");
//		metamap.setOptions("-J aapp,acab,anab,anst,antb,bacs,bact,bdsu,cgab,clna,clnd,diap,dysn,horm,imft,lbpr,lbtr,medd,topp,vita,phsu");

		metamapInitialized = true;
	}
		

//	/** Return list of UMLS concept mappings for a given string */
//	private Vector<UmlsConcept> getConceptList(String text){
//		List<Result> resultList = metamap.processCitationsFromString(text);
//		Vector<UmlsConcept> umlsConcepts = new Vector<UmlsConcept>();
//		for(Result result: resultList){
//			try {								
//				for (Utterance utterance: result.getUtteranceList()){
//					for (PCM pcm: utterance.getPCMList()) {
//						for (Ev ev: pcm.getCandidateList()){
//							UmlsConcept uc = new UmlsConcept(ev);
//	                        umlsConcepts.add(uc);													
//						}						
//					}
//				}
//			} catch (Exception e) {
//				System.out.println(e.getLocalizedMessage());
//				e.printStackTrace();
//			}
//		}
//		return umlsConcepts;
//	}
	
	/** chunk sentence in metamap and identify semantic types and concept ids for phrases */
	public void metamapAnnotate(Sentence sentence){
		if (metamapInitialized == false){
			return;
		}
		HashSet<String> negatedConceptIDs = new HashSet<String>();
//		HashMap<String, AcronymsAbbrevs> acronyms = new HashMap<String,AcronymsAbbrevs>();

		String sString = sentence.toDisplayString();
		List<Result> resultList = metamap.processCitationsFromString(sString);
		// there will typically only be one result and utterance for a given phrase
		for(Result result: resultList){
			try {
				// find best score of all of the candidates (scores are negative, find score that is the most negative)
				
				// create set of negated concept ids
				negatedConceptIDs.clear();
				for (Negation neg: result.getNegationList()){
					for (ConceptPair pair: neg.getConceptPairList()){
						negatedConceptIDs.add(pair.getConceptId());
						
//						System.out.println("negated: "+pair.getConceptId()+", "+pair.getPreferredName());
					}
				}

//				// handle acronyms
//				List<AcronymsAbbrevs> aaList = result.getAcronymsAbbrevs();
//				if (aaList.size() > 0) {
//				  System.out.println("***Acronyms and Abbreviations:");
//				  for (AcronymsAbbrevs e: aaList) {
//					  acronyms.put(e.getAcronym(), e);
//					  System.out.println(e.getAcronym()+", "+e.getExpansion());
//				  }
//				}
//				
//				for(Token token: sentence.getTokens()){
//					if(acronyms.containsKey(token.getText())){
//						AcronymsAbbrevs e = acronyms.get(token.getText());
//						Vector<UmlsConcept> umlsConcepts = getConceptList(e.getExpansion());
//						for(UmlsConcept uc: umlsConcepts){
//							token.addUmlsConcept(uc);
//							if(negatedConceptIDs.contains(uc.id)){
//								uc.isNegated = true;
//							}
//						}
//
//					}
//					
//				}
				
				for (Utterance utterance: result.getUtteranceList()){

					for (PCM pcm: utterance.getPCMList()) {
						for (Ev ev: pcm.getCandidateList()){
							UmlsConcept uc = new UmlsConcept(ev);
							if(negatedConceptIDs.contains(uc.id)){
								uc.isNegated = true;
							}
							
//							System.out.println(uc.score+" Concept:"+uc.id+ev.getMatchedWords());
							for (Position position: ev.getPositionalInfo()) {
								int startIdx = position.getX();
								int endIdx = startIdx + position.getY() - 1;
								Vector<Token> tList = sentence.getTokensInRangeDisplay(startIdx, endIdx); 
								for(Token token: tList){
									token.addUmlsConcept(uc);
								}
							}
							
						}
						
						Position position = pcm.getPhrase().getPosition();
						int startIdx = position.getX();
						int endIdx = startIdx + position.getY() - 1;
						Vector<Token> tList = sentence.getTokensInRangeDisplay(startIdx, endIdx); 
						
						boolean firstToken = true;
						for(Token token: tList){
							if(firstToken){
								token.metamapChunkTag = "B";
								firstToken = false;
							} else {
								token.metamapChunkTag = "I";
							}
						}

					}

				}

			} catch (Exception e) {
				System.out.println(e.getLocalizedMessage());
				e.printStackTrace();
			}
		}
		
	}

	/** return list of UMLS code elements for a given string */
	public List<Element> lookupCodes(String text){
		ArrayList<Element> codeList = new ArrayList<Element>();
		if (metamapInitialized == false){
			return codeList;
		}

		HashSet<String> negatedConceptIDs = new HashSet<String>();

		List<Result> resultList = metamap.processCitationsFromString(text);
		// there will typically only be one result and utterance for a given phrase
		for(Result result: resultList){
			try {
				// create set of negated concept ids
				negatedConceptIDs.clear();
				for (Negation neg: result.getNegationList()){
					for (ConceptPair pair: neg.getConceptPairList()){
						negatedConceptIDs.add(pair.getConceptId());
					}
				}
				
				for (Utterance utterance: result.getUtteranceList()){

					for (PCM pcm: utterance.getPCMList()) {
						Element codeElement = new Element("CodedText");
						codeElement.addContent(XmlUtil.createTextElement("Text", pcm.getPhrase().getPhraseText()));
						boolean containsCodes = false;
						for (Ev ev: pcm.getCandidateList()){
							containsCodes = true;
							String conceptID = ev.getConceptId();
							String snomedCode = getSnomedCode(conceptID);
							Element conceptElement = new Element("Concept");
							codeElement.addContent(conceptElement);
							
							if (snomedCode.isEmpty() == false){
								conceptElement.setAttribute("code", snomedCode);
								conceptElement.setAttribute("type", "snomed");
							} else {
								conceptElement.setAttribute("code", conceptID);
								conceptElement.setAttribute("type", "umls");								
							}
							
							conceptElement.addContent(XmlUtil.createTextElement("Score", Integer.toString(-ev.getScore())));
							if (negatedConceptIDs.contains(conceptID)){
								conceptElement.setAttribute("negated", "true");
							} else {
								conceptElement.setAttribute("negated", "false");								
							}
							conceptElement.addContent(XmlUtil.createTextElement("Preferred", ev.getPreferredName()));
							List<String>  types = ev.getSemanticTypes();
							if(types.size() > 0){
								Element typeListElement = new Element("SemanticTypes");
								conceptElement.addContent(typeListElement);
								for(String type: types){
									typeListElement.addContent(XmlUtil.createTextElement("Type", type));

								}
							}
								
							if(snomedCode.isEmpty() == false){
								break;
							}
							
						}
						if (containsCodes){
							codeList.add(codeElement);						
						}
					}
				}

//				
//				// find best score of all of the candidates (scores are negative, find score that is the most negative)
//				for (Utterance utterance: result.getUtteranceList()){
//
//					for (PCM pcm: utterance.getPCMList()) {
//						int bestScore = 0;	
//						
//						for (Ev ev: pcm.getCandidateList()) {
//							if(ev.getScore() < bestScore) { // && idSet.contains(ev.getConceptId()) == false){
//								bestScore = ev.getScore();
//							}
//						}
//						if(bestScore != 0){
//							for (Ev ev: pcm.getCandidateList()) {
//								if(ev.getScore() == bestScore){
//									// set the concept id and umls semantic types for each token in the phrase
//									Element codeElement = new Element("CodedText");
//									codeElement.addContent(XmlUtil.createTextElement("Score", Integer.toString(-ev.getScore())));
//									String conceptID = ev.getConceptId();
//									if (negatedConceptIDs.contains(conceptID)){
//										codeElement.setAttribute("negated", "true");
//									} else {
//										codeElement.setAttribute("negated", "false");								
//									}
//									String snomedCode = getSnomedCode(conceptID);
//									if (snomedCode.isEmpty() == false){
//										codeElement.addContent(XmlUtil.createTextElement("Code", snomedCode));
//										codeElement.setAttribute("type", "snomed");
//									} else {
//										codeElement.addContent(XmlUtil.createTextElement("Code", conceptID));
//										codeElement.setAttribute("type", "umls");								
//									}
//									codeElement.addContent(XmlUtil.createTextElement("Text", pcm.getPhrase().getPhraseText()));
//									codeElement.addContent(XmlUtil.createTextElement("Preferred", ev.getPreferredName()));
//									List<String>  types = ev.getSemanticTypes();
//									if(types.size() > 0){
//										Element typeListElement = new Element("SemanticTypes");
//										codeElement.addContent(typeListElement);
//										for(String type: types){
//											typeListElement.addContent(XmlUtil.createTextElement("Type", type));
//
//										}
//									}
////									codeElement.addContent(XmlUtil.createTextElement("Types", ev.getSemanticTypes().toString()));
////									codeElement.setAttribute("phrase", pcm.getPhrase().getPhraseText());
////									codeElement.setAttribute("preferred", ev.getPreferredName());
////									codeElement.setAttribute("types", ev.getSemanticTypes().toString());
//									codeList.add(codeElement);										
//									idSet.add(ev.getConceptId());
//								}
//							}
//						}
//
//					}
//
//				}

			} catch (Exception e) {
				System.out.println(e.getLocalizedMessage());
				e.printStackTrace();
			}
		}
		
		return codeList;
	}

	
}
