/** Sentence.java 
 *  Store a sentence from an xml abstract
 *  @author rlsummerscales
 */

package ebm;

import java.io.*;
import java.util.*;


import org.jdom.*;

import edu.stanford.nlp.ling.CoreLabel;
import edu.stanford.nlp.ling.HasWord;
import edu.stanford.nlp.ling.CoreAnnotations.PartOfSpeechAnnotation;
import edu.stanford.nlp.parser.lexparser.LexicalizedParser;
//import edu.stanford.nlp.ling.CoreAnnotations.TokensAnnotation;
//import edu.stanford.nlp.trees.GrammaticalStructure;
import edu.stanford.nlp.trees.GrammaticalStructure;
import edu.stanford.nlp.trees.GrammaticalStructureFactory;
import edu.stanford.nlp.trees.Tree;
import edu.stanford.nlp.trees.TreeFactory;
import edu.stanford.nlp.trees.TreePrint;
import edu.stanford.nlp.trees.TypedDependency;
//import edu.stanford.nlp.trees.TreeCoreAnnotations.TreeAnnotation;
//import edu.stanford.nlp.trees.semgraph.SemanticGraph;
//import edu.stanford.nlp.trees.semgraph.SemanticGraphCoreAnnotations;
//import edu.stanford.nlp.util.CoreMap;

public class Sentence {
	/** keep track of tokens temporarily removed from the sentence */
	private class RemovedTokens{
		/** list of removed tokens */
		Vector<Token> list = null;
		/** index of place holder token in sentence */ 
		int index = -1;    
		
		RemovedTokens(int index){
			this.index = index;
			this.list = new Vector<Token>();
		}
	}
	
	/** section label (if any) for section of abstract containing sentence */
	public String section = "";            
	/** NLM label (if any) for section of abstract containing sentence */
	public String nlmCategory = "";
	
	/** parse tree for sentence */
	private Tree tree = null;
	/** dependency graph for sentence */
	private Collection<TypedDependency> dependencies = null;
	/** list of tokens in the sentence */
	private Vector<Token> tokens = null;
	
	private static final String numericToken = "2";
	
	
	/** create a new sentence from a list of tokens (CoreLabel objects) */
	public Sentence(List<HasWord> tokenList, String sectionLabel, String nlmCategory){
		this.section = sectionLabel;
		this.nlmCategory = nlmCategory;
		this.tokens = new Vector<Token>();
		int i = 0;
    	for (HasWord token: tokenList){
    		CoreLabel label = (CoreLabel) token;
    		this.tokens.add(new Token(label, i++));
    	}
	}
	
	/** set the parse tree for this sentence. Also set the POS tags for each token from the parse tree. */
    public void setParseTree(Tree parseTree){
    	// set the POS tags for each token in the sentence
    	int i = 0;
		for (CoreLabel label: parseTree.taggedLabeledYield()){
			Token token = this.tokens.get(i++);
			// parse tree tokens not lined up with sentence tokens if this is false
			assert token.getText().equalsIgnoreCase(label.word());
			
			token.setPOS(label.get(PartOfSpeechAnnotation.class));
		}
		this.tree = parseTree;
    }
    
	/** set the dependency properties for this sentence.*/
    public void setDependencies(Collection<TypedDependency> typedDepList){    
		// process parse trees
        this.dependencies = typedDepList;
		if (this.dependencies != null){
			
			for(TypedDependency dep: this.dependencies){
				String type = dep.reln().getShortName();
				String specific = dep.reln().getSpecific();
				int governorIdx = dep.gov().index() - 1;
				int dependIdx = dep.dep().index() - 1;
				if (type.equalsIgnoreCase("root") == false){
					Token govToken = this.tokens.get(governorIdx);
					govToken.addDependent(type, specific, dependIdx);
				}
				Token depToken = this.tokens.get(dependIdx);
				depToken.addGovernor(type, specific, governorIdx);
			}
		}
    }
	
    /** apply a given parser to the sentence */
    public void parse(LexicalizedParser parser, GrammaticalStructureFactory gsf){
    	// simplify the sentence for parsing
//    	System.out.println(this.toString());
    	Vector<RemovedTokens> rtList = this.prepareForParse();
    	
//    	System.out.println(this.toString());

    	// parse the sentence
        Tree parseTree = parser.apply(this.getCoreLabels());
//        parseTree.pennPrint();
//        System.out.println();
            
        this.setParseTree(parseTree);
        
        postProcessParseTree(rtList);
//        parseTree.pennPrint();
//        System.out.println();

        // create collection of dependencies
        GrammaticalStructure gs = gsf.newGrammaticalStructure(parseTree);
        Collection<TypedDependency> tdl = gs.typedDependenciesCCprocessed(true);
//        Collection<TypedDependency> tdl = gs.typedDependencies();
        
//        System.out.println(tdl);
//        System.out.println();
        
        this.setDependencies(tdl);

    }
    
    /** apply transformation rules to tokens in the sentence to prepare it for parsing.
     * The purpose is to normalize the sentences somewhat so there is less variation in the parsed result
     * (e.g. replacing a word with a synonym should not dramatically change the parse tree)
     */
    public Vector<RemovedTokens> prepareForParse(){
    	Vector<RemovedTokens> rtList = new Vector<RemovedTokens>();
        int i = 0;
        
        // remove percent symbols from percentages.
        for(i = 0; i < this.tokens.size(); i++){
        	Token t0 = this.tokens.get(i);

        	if((i+1) < this.tokens.size()){
        		Token t1 = this.tokens.get(i+1);
        		if((t0.isNumber() && t1.equals("%"))){
        			// with "NUM %", simply delete '%' token and add a tag to the number
        			t0.addTag("percentage");

        			this.tokens.remove(i+1);   // remove the '%'    			
        		}
        	}
        }

    	for(i = 0; i < this.tokens.size(); i++){
    		Token token = this.tokens.get(i);
     		
    		// find numeric patterns like INT / INT and replace them with something that is easier to parse
    		RemovedTokens removedTokens = removeNumericPattern(i);
    		if(removedTokens != null){
    			rtList.add(removedTokens);
    		}
    		
    		// handle greater/less than or equal
    		if(token.getText().equalsIgnoreCase(XmlUtil.greaterThanEqualToken)){
    			token.setText("greater");
    			Token nextToken = new Token("than", i+1);
    			this.tokens.add(i+1, nextToken);
    			token.addTag(XmlUtil.greaterThanEqualToken);
    			nextToken.addTag(XmlUtil.greaterThanEqualToken);
    			for(XmlTag tag: token.tags.values()){
    				nextToken.addTag(tag);
    			}
    		} else if(token.getText().equalsIgnoreCase(XmlUtil.lessThanEqualToken)){
    			token.setText("less");
    			Token nextToken = new Token("than", i+1);
    			this.tokens.add(i+1, nextToken);
    			token.addTag(XmlUtil.lessThanEqualToken);
    			nextToken.addTag(XmlUtil.lessThanEqualToken);
    			for(XmlTag tag: token.tags.values()){
    				nextToken.addTag(tag);
    			}    			
    		}

    	}
    	return rtList;
    }
    
    
    /** check if the token at index i in the sentence is part of a common numeric pattern. 
     * If it is, replace all tokens in the pattern with a special tagged token than can be parsed correctly.
     * @param i is index of token in sentence
     * Identify the following patterns and replace with the number 2.
     * NUM %
     * NUM / NUM
     * NUM of NUM
     * NUM +- NUM
     * VAR = NUM (REMOVED: resulted in disconnected dependency graph)
     */
    private RemovedTokens removeNumericPattern(int i){
    	RemovedTokens removedTokens = null;
    	Token t0 = this.tokens.get(i);

    	// find patterns of the form "INT out? of the? INT" and replace with "INT of INT"
    	if(t0.isInteger() && t0.hasTag("percentage") == false){
    		int j = i+1;
    		boolean foundOF = false;
    	    boolean validPattern = true;
    	    boolean patternMatched = false;
    		while(j < this.tokens.size() && j < i+5 && validPattern == true && patternMatched == false){
    			Token t = this.tokens.get(j);
    			if(t.equals("of")){
    				foundOF = true;
    			} else if (foundOF && t.isInteger()) {// && t.hasTag("percentage") == false && t.getValue() > t0.getValue()){
    				patternMatched = true;
    			} else if (t.equals("the") == false && t.equals("out") == false){
    				validPattern = false;
    			}
 
    			j++;
    		}
    		
    		if(patternMatched){
    			// delete all tokens between the two integers and replace with a slash
//    	    	PrintWriter errorPW = null;
//    			try {
//    				errorPW = new PrintWriter(new FileWriter(new File("abstracts.pattern.txt"), true));
//    			} catch (IOException e) {
//    				// TODO Auto-generated catch block
//    				e.printStackTrace();
//    				System.exit(-1);
//    			}

    			int k = 0;
//    			int startIdx = i;
//    			if(i>0){
//    				startIdx--;
//    			}
//    			for(k = startIdx; k < j+1; k++){
//    			    Token t = this.tokens.get(k);
//    			    errorPW.print(t.getText()+" ");
//    			}
//    			errorPW.print(" --> ");
    			
    			
    			for(k = i+1; k < (j-1); k++) {
    				this.tokens.remove(i+1);
    			}
    			Token newToken = new Token("of", i);
    			this.tokens.insertElementAt(newToken, i+1);
    			
    			
//    			for(k = startIdx; k < i+4; k++){
//    			    Token t = this.tokens.get(k);
//    			    errorPW.print(t.getText()+" ");
//    			}
//    			errorPW.println();
//    			errorPW.close();
    		}
    	}

    	if((i+2) < this.tokens.size()){
    		Token t1 = this.tokens.get(i+1);
    		Token t2 = this.tokens.get(i+2);
    		
       		// convert hyphen in number ranges to "to" which is parsed more accurately e.g. 18 - 75 -> 18 to 75
    		if(t0.isNumber() && t2.isNumber() && t1.getText().equalsIgnoreCase("-")){
    			t1.setText("to");
    		}

    		
//    		if((t0.isNumber() && t2.isNumber() && (t1.equals("\\/") || t1.equals("of") || t1.equals(XmlUtil.plusOrMinusToken))) 
//    		   || (t0.getText().length() == 1 && t2.isNumber() && t1.equals("="))) {
    		if(t0.isNumber() && t2.isNumber() && (t1.equals("\\/") || t1.equals("of") || t1.equals(XmlUtil.plusOrMinusToken))) {
    			
    			Token newToken = new Token(numericToken, i);
    			
    			if(t1.equals(XmlUtil.plusOrMinusToken)){
        			newToken.addTag("num_+-_num");    				
//    			} else if(t1.equals("=")){
//    				newToken.addTag("n=num");
    			} else {
        			newToken.addTag("num_of_num");
        			t1.setText("of");
    			}

    			this.tokens.set(i, newToken);  // replace t0
    			this.tokens.remove(i+1);   // remove t1
    			this.tokens.remove(i+1);   // remove t2
    			
    			removedTokens = new RemovedTokens(i);
    			removedTokens.list.add(t0);
    			removedTokens.list.add(t1);
    			removedTokens.list.add(t2);
    		} 
    	} 
    	
    	return removedTokens;
    }

    
    /** perform postprocessing on the parse tree. 
     * Add parse trees for the removed tokens.
     * @param rtList is the list of tokens removed from the sentence before parsing
     */
    private void postProcessParseTree(Vector<RemovedTokens> rtList){
    	List<Tree> leaves = this.tree.getLeaves();
    	int indexOffset = 0;
    	
    	assert leaves.size() == this.tokens.size();
    	
    	for(RemovedTokens removedTokens: rtList) {
    		// as old tokens are put back in the sentence the special token index needs to be updated
    		int tokenSentenceIndex = removedTokens.index + indexOffset;
    		Token specialToken = this.tokens.get(tokenSentenceIndex);
    		Tree tokenNode = leaves.get(removedTokens.index);
    		
    		if(removedTokens.list.size() == 3){
    			Token t0 = removedTokens.list.get(0);
    			Token t1 = removedTokens.list.get(1);
    			Token t2 = removedTokens.list.get(2);
    			TreeFactory treeFactory = tree.treeFactory();
				Tree parent = tokenNode.parent(tree);    				
    			
    			if(specialToken.hasTag("num_of_num") || specialToken.hasTag("num_+-_num")){
    				parent.label().setValue("NP");    	// parent was CD node, but is now NP node
    				parent.removeChild(0);              // delete the special token node
    				
    				parent.addChild(createPosNode(treeFactory, "CD", t0.coreLabel));    				
    				parent.addChild(createPosNode(treeFactory, "IN", t1.coreLabel));
       				parent.addChild(createPosNode(treeFactory, "CD", t2.coreLabel));
//    			} else if(specialToken.hasTag("n=num")){
//    				parent.label().setValue("S");    	// parent was CD node, but is now NP node
//    				parent.removeChild(0);              // delete the special token node
//    				
//    				Tree phraseNode = treeFactory.newLeaf("NP");
//    				phraseNode.addChild(createPosNode(treeFactory, "NN", t0.coreLabel));
//    				parent.addChild(phraseNode);  
//    				
//    				phraseNode = treeFactory.newLeaf("VP");
//    				phraseNode.addChild(createPosNode(treeFactory, "VBZ", t1.coreLabel));
//    				parent.addChild(phraseNode);  
//
//    				phraseNode = treeFactory.newLeaf("NP");
//    				phraseNode.addChild(createPosNode(treeFactory, "CD", t2.coreLabel));
//    				parent.addChild(phraseNode);  

    			}else {
    				System.out.println("ERROR: unsupported special token "+specialToken.getText());
    				System.out.println("in sentence: "+this.toString());
    				System.exit(1);
    			}
    			
    			// prune unnecessary nodes: if a parent of the special token token now has the same
    			// label as its parent and it is the only child of its parent, remove it.
    			Tree grandParent = parent.parent(tree);
    			if (grandParent != null && grandParent.numChildren() == 1 
    					&& grandParent.value().equalsIgnoreCase(parent.value())){
    				grandParent.removeChild(0);
    				grandParent.setChildren(parent.children());
    				
    			}
    			
    			this.tokens.remove(tokenSentenceIndex);
    			this.tokens.add(tokenSentenceIndex, t2);
    			this.tokens.add(tokenSentenceIndex, t1);
    			this.tokens.add(tokenSentenceIndex, t0);
    			indexOffset += 2;   // two tokens added to the sentence	
    		} 
    	}
    }

    /** create a new tree node for a POS tag which has a token node as its only child */
    private Tree createPosNode(TreeFactory treeFactory, String pos, CoreLabel tokenLabel){
		tokenLabel.set(PartOfSpeechAnnotation.class, pos);
		Tree posNode = treeFactory.newLeaf(pos);
		Tree tNode = treeFactory.newLeaf(tokenLabel);
		posNode.addChild(tNode);
		return posNode;
    }
    
	/** append a token to end of token list for sentence */
	public void appendToken(Token token){
		tokens.add(token);
	}

	/** return the list of stanford core label objects */
	public List<CoreLabel> getCoreLabels(){
		Vector<CoreLabel> labelList = new Vector<CoreLabel>();
		for(Token token: this.tokens){
			labelList.add(token.coreLabel);
		}
		return labelList;
	}
	
	/** return an XML element containing information about sentence and its tokens */
	public Element getXMLElement() {
		Element sElement = new Element("sentence");
		if(section != null && section.length() > 0){
			sElement.setAttribute("section", section);
		}
		if(nlmCategory != null && nlmCategory.length() > 0){
			sElement.setAttribute("nlmCategory", nlmCategory);
		}
		for(Token token: tokens){
			Element tElement = token.getXMLElement();
			sElement.addContent(tElement);
		}
		Element uElement = null;
		boolean inChunk = false;
		int i = 0;
		for(Token token: tokens){
			if(inChunk && token.metamapChunkTag.equalsIgnoreCase("I") == false) {
				// reach end of current chunk
				uElement.setAttribute("end", Integer.toString(i-1));
				sElement.addContent(uElement);
				uElement = null;
				inChunk = false;
			}
			if(token.metamapChunkTag.equalsIgnoreCase("B") == true){
				// start new chunk
				uElement = new Element("umlsChunk");
				uElement.setAttribute("start", Integer.toString(i));

				inChunk = true;
			} 
			i++;
		}
		if(uElement != null) {
			// reach end of current chunk
			uElement.setAttribute("end", Integer.toString(i-1));
			sElement.addContent(uElement);
		}

		if(tree != null){
			Element pElement = new Element("parse");
		    StringWriter treeStrWriter = new StringWriter();
		    TreePrint treePrinter = new TreePrint("oneline");//("penn");
		    treePrinter.printTree(tree, new PrintWriter(treeStrWriter, true));

			pElement.addContent(treeStrWriter.toString());
			sElement.addContent(pElement);
		}
		return sElement;
	}
	
	/** return list of tokens in sentence */
	public Vector<Token> getTokens() {
		return tokens;
	}
	
	/** convert sentence to a string and return it */
	public String toString() {
		String sentence = "";
		// build string version of sentence (separate all tokens by a space)
		for(Token token: tokens){
			sentence = sentence + token.getText() + " ";
//			sentence = sentence + " " + w.text + "_" + w.pos;
		}
		return sentence;
	}

	/** convert sentence to a string for display purpose and return it */
	public String toDisplayString() {
		String sentence = "";
		// build string version of sentence (separate all tokens by a space)
		for(Token token: tokens){
			sentence = sentence + token.getDisplayText() + " ";
		}
		return sentence;
	}

	/** return list of tokens in the sentence between two given character indices 
	 * @param startIdx is index of first character of the first token in the sequence
	 * @param endIdx is index of last character of the last token in the sequence
	 * Index = 0 is the first character in the sentence. The character indices assume
	 * a single space between sentence tokens.
	 * */
	public Vector<Token> getTokensInRange(int startIdx, int endIdx){
		Vector<Token> tList = new Vector<Token>();
		int i = 0;
		for(Token token: tokens){
			if(i >= startIdx && (i+token.getText().length()-1) <= endIdx){
				tList.add(token);
			}
			i += 1 + token.getText().length();
		}
		return tList;
	}

	/** return list of tokens in the sentence between two given character indices 
	 * @param startIdx is index of first character of the first token in the sequence
	 * @param endIdx is index of last character of the last token in the sequence
	 * Index = 0 is the first character in the sentence. The character indices assume
	 * a single space between sentence tokens.
	 * */
	public Vector<Token> getTokensInRangeDisplay(int startIdx, int endIdx){
		Vector<Token> tList = new Vector<Token>();
		int i = 0;
		for(Token token: tokens){
			String text = token.getDisplayText();
			int nextEndIdx = i+text.length()-1;
			if(i >= startIdx && nextEndIdx <= endIdx){
				tList.add(token);
			}
			i = nextEndIdx + 2;
		}
		return tList;
	}

}