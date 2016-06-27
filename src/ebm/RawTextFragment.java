
package ebm;

import java.util.*;

/** Store a text string and its tags 
 * @author rlsummerscales
 * */
public class RawTextFragment {
	/** text for the fragment */
	public String text = "";
	/** list of annotated xml tags for the fragment (if any) */
	public Vector<XmlTag> tags = new Vector<XmlTag>();
   
	public RawTextFragment(String t){
		text = t;
	}
	
	public RawTextFragment(String t, Vector<XmlTag> tagList){
		text = t;
		if(tagList != null && tagList.isEmpty() == false){
			tags = tagList;
		}
	}
	

}