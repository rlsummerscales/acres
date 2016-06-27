package ebm;
import java.util.*;

import org.jdom.Attribute;

/** Class for storing XML tag info for a word
 * @author rlsummerscales */
public class XmlTag{
	/** name of tag */
	public String name = "";
	/** attributes given in tag */
	public HashMap<String,String> attributes = new HashMap<String,String>();

	public XmlTag(String tagName){
		this.name = tagName;
	}

	public XmlTag(String tagName, List<Attribute> attribList){
		this.name = tagName;
		for(Iterator<Attribute> aIter = attribList.iterator(); aIter.hasNext();){
			Attribute a = (Attribute) aIter.next();
			attributes.put(a.getName(), a.getValue());
		}
			
	}
}