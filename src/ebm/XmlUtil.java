
package ebm;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.jdom.*;
import org.jdom.filter.*;

/** XmlUtil.java 
 * Misc functions for working with xml elements
 * @author rlsummerscales
 */

public class XmlUtil {
	public static final String lessThanToken = "less than";
	public static final String lessThanEqualToken = "less_than_equal_to";
	public static final String greaterThanToken = "greater than";
	public static final String greaterThanEqualToken = "greater_than_equal_to";
	public static final String plusOrMinusToken = "plus_minus";
	
	public static final HashSet<Character> punctuationSet;
	static {
		HashSet<Character> hMap = new HashSet<Character>();
		hMap.add('(');
		hMap.add(')');
		hMap.add('[');
		hMap.add(']');
		hMap.add('{');
		hMap.add('}');
		hMap.add('.');
		hMap.add(':');
		hMap.add('?');
		hMap.add(';');
		hMap.add('/');
		hMap.add('!');
		punctuationSet = hMap;
	}
	
	public static final Map<String, Integer> numericString;
    static {
        Map<String, Integer> aMap = new HashMap<String, Integer>();
        aMap.put("zero", 0);
        aMap.put("one", 1);
        aMap.put("two", 2);
        aMap.put("three", 3);
        aMap.put("four", 4);
        aMap.put("five", 5);
        aMap.put("six", 6);
        aMap.put("seven", 7);
        aMap.put("eight", 8);
        aMap.put("nine", 9);
        aMap.put("ten", 10);
        aMap.put("eleven", 11);
        aMap.put("twelve", 12);
        aMap.put("thirteen", 13);
        aMap.put("fourteen", 14);
        aMap.put("fifteen", 15);
        aMap.put("sixteen", 16);
        aMap.put("seventeen", 17);
        aMap.put("eighteen", 18);
        aMap.put("nineteen", 19);
        
        aMap.put("twenty", 20);
        aMap.put("thirty", 30);
        aMap.put("fourty", 40);
        aMap.put("forty", 40);
        aMap.put("fifty", 50);
        aMap.put("sixty", 60);
        aMap.put("seventy", 70);
        aMap.put("eighty", 80);
        aMap.put("ninety", 90);

        aMap.put("hundred", 100);
        aMap.put("thousand", 1000);
        
        HashMap<Integer, String> wordForm = new HashMap<Integer, String>();
        wordForm.put(1, "one");
        wordForm.put(2, "two");
        wordForm.put(3, "three");
        wordForm.put(4, "four");
        wordForm.put(5, "five");
        wordForm.put(6, "six");
        wordForm.put(7, "seven");
        wordForm.put(8, "eight");
        wordForm.put(9, "nine");
        wordForm.put(20, "twenty");
        wordForm.put(30, "thirty");
        wordForm.put(40, "forty");
        wordForm.put(50, "fifty");
        wordForm.put(60, "sixty");
        wordForm.put(70, "seventy");
        wordForm.put(80, "eighty");
        wordForm.put(90, "ninety");

        for(int tens = 20; tens < 100; tens += 10){
        	for(int ones = 1; ones < 10; ones++) {
        		String tensString = wordForm.get(tens);
        		String onesString = wordForm.get(ones);
        		aMap.put(tensString+"-"+onesString, tens+ones);        		
        	}
        }
        numericString = Collections.unmodifiableMap(aMap);
    }
 
	public static String removeCommas(String text){
		Pattern p = Pattern.compile("(\\d+),(\\d\\d\\d$|\\d\\d\\d\\D)");
		String oldText;
		do {
			oldText = text;
			Matcher m = p.matcher(text);
			text = m.replaceAll("$1$2");
		} while(oldText.equalsIgnoreCase(text) == false);
		return text;
	}
	
	public static String normalizeNumbers(String text){
		String[] tokens = text.split(" ");
		
		int currentNumber = -1;
		String normalizedString = "";
		for(int i = 0; i < tokens.length; i++){
			String token = tokens[i];
			int number = -1;
			// prefix is any non word chars at beginning of string (e.g. '(', ';')
			String p = "^([\\W]+)(.*)$";
			String prefix = "";
			if(token.matches(p)){
				prefix = token.replaceAll(p, "$1");
				token = token.replaceAll("\\W+(.*)$", "$1");
			}
			// suffix is any non word chars at END of string
			String s = ".*?([\\W]+)$";
			String suffix = "";
			if(token.matches(s)){
				suffix = token.replaceAll(s, "$1");
				token = token.replaceAll("(.*?)\\W+$", "$1");
			}
			
			if(prefix.isEmpty() == false){
				if(currentNumber != -1){
					normalizedString += currentNumber + " ";
					currentNumber = -1;
				}
				
				normalizedString += prefix;
				if(token.isEmpty()){
					normalizedString += " ";
				}
				prefix = "";
			}
			
			if(isNumericString(token)){
				number = numericString.get(token.toLowerCase());
				token = "";
			} else {
				token = token + suffix;
				suffix = "";
			}
			
			if(currentNumber == -1){
				// start new number
				currentNumber = number;
			} else if(number == 100 || number == 1000){
				currentNumber *= number;
			} else if(number != -1){
				currentNumber += number;
			}
			
			// check for end of number
			if(token.isEmpty() == false){
				if(currentNumber != -1){
					token = currentNumber + " "+ token;
					currentNumber = -1;
				} 
			} else if(suffix.isEmpty() == false){
				if(currentNumber != -1){
					token = currentNumber + suffix;
					currentNumber = -1;
				} 				
			}
			
			
			if(token.isEmpty() == false){
				if(i < tokens.length-1){
					normalizedString += token + " ";
				} else {
					normalizedString += token;
				}
			}
		}
		if(currentNumber != -1){
			normalizedString += currentNumber;
		}
		return normalizedString.trim();
	}
	
	static boolean isNumericString(String s){
		if(numericString.containsKey(s.toLowerCase())) {
			return true;
		} 
		return false;
	}

	public static String normalizeText(String text){
//		text = text.toLowerCase();
		// only convert the first char in the sentence to lowercase.
//		char[] chars = text.toCharArray();
//		if (chars.length > 1){
//			if (chars[0]>='A' && chars[0]<='Z' && ((chars[1]>='a' && chars[1]<='z') || chars[1] == ' ')){
//				// first char in sentence is uppercase and it is not part of an all uppercase acronym
//				chars[0] += 'a'-'A';
//				text = new String(chars);
//			}
//		}
		text = removeCommas(text);
		text = normalizeNumbers(text);
		text = text.replaceAll("¬∑", ".");	
		
		text = text.replaceAll("â•", " "+greaterThanEqualToken + " ");		
		text = text.replaceAll("â§", " "+lessThanEqualToken + " ");		
		text = text.replaceAll("Â", " ");	

		
//		text = text.replaceAll("â", "");				
//		text = text.replaceAll("‰¤", " "+lessThanEqualToken + " ");		
//		text = text.replaceAll("‰¥", " "+greaterThanEqualToken + " ");
		text = text.replaceAll("¬", " ");		
//		text = text.replaceAll("‚äà", " ");		
		text = text.replaceAll("·", ".");				
//		text = text.replaceAll("€ˆ", " ");	
		

		text = text.replaceAll("±", " "+plusOrMinusToken + " ");		
		text = text.replaceAll("\\+-", " "+plusOrMinusToken + " ");		
		text = text.replaceAll("\\+/-", " "+plusOrMinusToken + " ");		
		text = text.replaceAll("\\+(\\W*| or )?-", " "+plusOrMinusToken + " ");		

		text = text.replaceAll("≥", " "+greaterThanEqualToken + " ");
		text = text.replaceAll("≤", " "+lessThanEqualToken + " ");
		text = text.replaceAll("(\\d%?)-(\\d)", "$1 to $2");		
		text = text.replaceAll("(\\d%?)-(day|week|month|year)", "$1 $2");		

		text = text.replaceAll(">(\\W*| or )?=", " "+greaterThanEqualToken + " ");		
		text = text.replaceAll("=(\\W*| or )?>", " "+greaterThanEqualToken + " ");		

		text = text.replaceAll("(\\S)?>(\\S)?", "$1 " + greaterThanToken + " $2");
		
		text = text.replaceAll("<(\\W*| or )?=", " "+lessThanEqualToken + " ");
		text = text.replaceAll("=(\\W*| or )?<", " "+lessThanEqualToken + " ");

		text = text.replaceAll("(\\S)?<(\\S)?", "$1 " + lessThanToken + " $2");

		text = text.replaceAll("pound(s)?(\\W*)sterling", "pounds");
		text = text.replaceAll("pound(\\d)", "pound $1");
	    text = text.replaceAll("euro(\\d)", "euro $1");
	    text = text.replaceAll("dollar(\\d)", "dollar $1");

		text = text.replaceAll("(\\D)(\\.\\d+)", "$10$2");


//		text = text.replaceAll("(\\d+) \\w*\\s?(of the|of|out of|out of the) (\\d+)", "$1 / $3");

		text = text.replaceAll("(\\d+)/(\\d+)", "$1 / $2");
		text = text.replaceAll("follow(\\s*-\\s*)?up", "follow-up");
		text = text.replaceAll("per(\\W*)cent", "%");

		text = text.replaceAll("fewer than", lessThanToken + " ");
		text = text.replaceAll("at least", greaterThanEqualToken + " ");

		text = text.replaceAll("below (-?\\d)", lessThanToken + " $1");
		text = text.replaceAll("under (-?\\d)", lessThanToken + " $1");

		text = text.replaceAll("above (-?\\d)", greaterThanToken + " $1");
		text = text.replaceAll("over (-?\\d)", greaterThanToken + " $1");		
		text = text.replaceAll("more than", greaterThanToken + " ");
		text = text.replaceAll("at most", lessThanEqualToken + " ");
		
		text = text.replaceAll("(\\W|^)(v|vs|v)\\.?(\\W|$)", "$1versus$3");
		
		text = text.replaceAll("intention to treat(\\s*analysis)?", "itt_analysis");
		text = text.replaceAll("per protocol(\\s*analysis)?", "per_protocol_analysis");
		text = text.replaceAll("95(\\s)*% (confidence interval|CI)", "95_confidence_interval");
		text = text.replaceAll("odds ratio", "odds_ratio");
		text = text.replaceAll("(adjusted\\s*)?hazard ratio", "hazard_ratio");
		text = text.replaceAll("absolute risk reduction", "absolute_risk_reduction");
		text = text.replaceAll("absolute risk increase", "absolute_risk_increase");		
		text = text.replaceAll("number needed to treat", "number_needed_to_treat");
		text = text.replaceAll("number needed to harm", "number_needed_to_harm");
		text = text.replaceAll("relative risk reduction", "relative_risk_reduction");
		text = text.replaceAll("relative risk increase", "relative_risk_increase");
		text = text.replaceAll("risk ratio", "relative_risk");
		text = text.replaceAll("relative risk", "relative_risk");
		
		return text;
		
	}
	
	/**
	 * Extract the text from elements and convert them to text objects.
	 * @param parent Element whose children will be converted to text objects
	 * @param tag Tag that we are looking to mark
	 * @return a string containing all text in the element
	 */
	@SuppressWarnings("unchecked")
	public static String stringify(Element parent){
		String s = "";
		Filter textAndElements = new ContentFilter(ContentFilter.TEXT|ContentFilter.ELEMENT);
		Filter elementOnly = new ContentFilter(ContentFilter.ELEMENT);
		List<Content> childList = parent.getContent(textAndElements);
		if(childList == null) {
			return s;
		}
			
		for(int i=0; i<childList.size(); i++){
			Content c = (Content) childList.get(i);
			if(elementOnly.matches(c)){ // content element
				Element e = (Element) c;
				s = s + stringify(e);
			} else { // is text element
				Text t = (Text) c;
				s = s + " " + t.getTextNormalize();
				
			}
		}
		
		return s;
	}
	
	/** return version of the string that is ready for xml output (i.e. convert '<' to '&lt', etc)
	 */
	public static String xmlSafe(String s){
		String safeString = s;

		safeString = safeString.replaceAll("&", "&amp;");
		safeString = safeString.replaceAll("<", "&lt;");
		safeString = safeString.replaceAll(">", "&gt;");
		safeString = safeString.replaceAll("'", "&apos;");
		safeString = safeString.replaceAll("\"", "&quot;");
		return safeString;
	}
	
	public static Vector<RawTextFragment> toRawTextFragmentList(Element parent)  
			throws Exception{
		return toRawTextFragmentList(parent, new Vector<XmlTag>());
	}
	
	/** Convert an XML element into a list of text strings. 
	 * Text strings that appear inside xml tags are associated with those tags.
	 */
	@SuppressWarnings("unchecked")
	public static Vector<RawTextFragment> toRawTextFragmentList(Element parent,  
			Vector<XmlTag> contextTags) throws Exception{

		Vector<RawTextFragment> rawFragments = new Vector<RawTextFragment>();
		Filter textAndElements = new ContentFilter(ContentFilter.TEXT|ContentFilter.ELEMENT);
		Filter elementOnly = new ContentFilter(ContentFilter.ELEMENT);
		List<Content> childList = parent.getContent(textAndElements);
		if(childList == null) {
			return rawFragments;  
		}

		for(int i=0; i<childList.size(); i++){
			Content c = (Content) childList.get(i);

			if(elementOnly.matches(c)){ // content element
				Element e = (Element) c;
				Vector<RawTextFragment> fl = null;
				XmlTag newTag = new XmlTag(e.getName(), e.getAttributes());
				// create new list of current tags (including this one)
				Vector<XmlTag> newContextTags = (Vector<XmlTag>) contextTags.clone();
				newContextTags.add(newTag);
				// continue to recursively convert tagged xml to list of words
				fl = toRawTextFragmentList(e, newContextTags);

				// append list of words to current list
				if(fl.size() > 0){
					rawFragments.addAll(fl);			
				}
			} else { // is text element
				Text t = (Text) c;
				String s = normalizeText(t.getTextNormalize());
				if(s.length() > 0){
					rawFragments.add(new RawTextFragment(s, contextTags));
				}
//				Vector<RawTextFragment> fragList = textToFragmentList(s, contextTags);
//				for(RawTextFragment rtf: fragList){
//					if(rtf.text.length()>0){
//						rawFragments.add(rtf) ;
////						System.out.print(rtf.text+" ");
//					}
//				}
//				System.out.println();
			}
		}		
		return rawFragments;
	}
	
//	/** preprocess and convert a text string to a list of raw fragments */
//	@SuppressWarnings("unchecked")
//	 public static Vector<RawTextFragment> textToFragmentList(String text, Vector<XmlTag> contextTags){
//		Vector<RawTextFragment> fragList = new Vector<RawTextFragment>();
//		int i = 0;
//		text = normalizeText(text);
//		String[] frags = text.split("greater than or equal (to)?");
//		
//		for(i = 0; i < frags.length; i++){
//			if(frags[i].length() > 0){
//				Vector<RawTextFragment> processedList = processLessThanEqual(frags[i], contextTags);
//				for(RawTextFragment processedFrag: processedList){
//					fragList.add(processedFrag);
//				}
//			}
//			if((i+1) < frags.length){
//				Vector<XmlTag> newContextTags = (Vector<XmlTag>) contextTags.clone();
//				XmlTag equalTag = new XmlTag("greater_or_equal");
//				newContextTags.add(equalTag);
//				RawTextFragment gFrag = new RawTextFragment("greater than", newContextTags);
//				fragList.add(gFrag);
//			}
//		}
//		
//		return fragList;
//	}

//	/** preprocess and convert a text string to a list of raw fragments */
//	@SuppressWarnings("unchecked")
//	private static Vector<RawTextFragment> processLessThanEqual(String text, Vector<XmlTag> contextTags){
//		Vector<RawTextFragment> fragList = new Vector<RawTextFragment>();
//		RawTextFragment rtf = null;
//		int i = 0;
//		
//		String[] frags = text.split("less than or equal (to)?");
//		
//		for(i = 0; i < frags.length; i++){
//			if(frags[i].length() > 0){
//				rtf = new RawTextFragment(frags[i], contextTags);
//				fragList.add(rtf);
//			}
//			if((i+1) < frags.length){
//				Vector<XmlTag> newContextTags = (Vector<XmlTag>) contextTags.clone();
//				XmlTag equalTag = new XmlTag("less_or_equal");
//				newContextTags.add(equalTag);
//				RawTextFragment gFrag = new RawTextFragment("less than", newContextTags);
//				fragList.add(gFrag);
//			}
//		}
//		return fragList;
//	}
	
	/** create a new XML element with a given name and text value */
	public static Element createTextElement(String name, String value){
		Element e = new Element(name);
		e.setText(value);
		return e;
	}

	public static Vector<RawTextFragment> toRawTextFragmentList(String text) {
		// TODO Auto-generated method stub
		return null;
	}

}

