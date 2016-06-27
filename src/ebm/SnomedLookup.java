package ebm;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class SnomedLookup
{
	private BufferedReader in = null;
//	private int[] RRFUMLId=new int[Config.RRF_ITEM_LINES];
//	private String[] RRFSnomedId=new String[Config.RRF_ITEM_LINES];
    private HashMap<String, String> umlsToSnomedMap = new HashMap<String, String>(); 
	private String regex1="C[0-9]{7}";
	private String regex2="\\|[0-9]{7,12}\\|\\|SNOMEDCT";
	private Pattern p1=Pattern.compile(regex1);
	private Pattern p2=Pattern.compile(regex2);
	
	public SnomedLookup(String snomedFilePath)
	{
		File RRF = new File(snomedFilePath);
		try {
			in = new BufferedReader(new InputStreamReader(new FileInputStream(RRF)));
//			int lineNum=0;
			String line="";
			if(in !=null){
				line = in.readLine();
				while(line != null){
					String umlsId = matchUMLSId(line);
					String snomedId = matchsnomedId(line);
					umlsToSnomedMap.put(umlsId, snomedId);
//					RRFUMLId[lineNum]=matchUMLId(line);
//					RRFSnomedId[lineNum]=matchsnomedId(line);
//					lineNum++;
					line=in.readLine();
				}
			}
			System.out.println("---------------RRF content loaded and initialized!--------------");
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} catch (IOException e){
			e.printStackTrace();
		}
		
	}
	
	public String matchUMLSId(String input)
	{
		Matcher m1=p1.matcher(input);
		if(m1.find()){
			String rs=m1.group();
			return rs;
//			return Integer.parseInt(rs.substring(1));
		}
		else
			return "";
	}
	
	public String matchsnomedId(String input)
	{
		Matcher m2=p2.matcher(input);
		if(m2.find()){
			String rs=m2.group();
			return rs.substring(1, rs.length()-10);
		}
		else
			return "0";
	}
	public String getSnomedId(String umlsId){
		String id = umlsToSnomedMap.get(umlsId);
		if(id == null){
			return "";
		} else {
			return id;
		}
	}
//	public String searchSnomedId(int id){
//		int low=0;
//		int high=RRFUMLId.length-1;
//		int index=0;
//		while(low<=high)
//		{
//			index=(low+high)/2;
//			if(id==RRFUMLId[index]){
//				
//				return RRFSnomedId[index];
//			}
//			else if(id<RRFUMLId[index])
//				high=index-1;
//			else
//				low=index+1;
//		}
//		return "";
//	}
	
//	public static void main(String[] args) {
//		RRFMatcher matcher=new RRFMatcher();
//		System.out.println(matcher.matchUMLId("C0012039|ENG|S|L0012507|PF|S0033298|N|A8380106|166113012|102735002||SNOMEDCT|OP|102735002|Dipalmitoylphosphatidylcholine|9|O|256|"));
//	}
}