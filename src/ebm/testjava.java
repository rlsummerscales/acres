package ebm;

//import java.util.Vector;
//import java.util.regex.Matcher;
//import java.util.regex.Pattern;

public class testjava {

	static String replace(String text){
		return XmlUtil.normalizeText(text);

//		String[] frags = text.split("greater than or equal (to)?");
//		text = "";
//		int i = 0;
//		for(i = 0; i < frags.length; i++){
//			text = text + frags[i];
//			if((i+1) < frags.length){
//				text += "<greater than>_eq ";
//			}
//		}
//
//		frags = text.split("less than or equal (to)?");
//		text = "";
//		for(i = 0; i < frags.length; i++){
//			text = text + frags[i];
//			if((i+1) < frags.length){
//				text += "<less than>_eq ";
//			}
//		}

//		Vector<XmlTag> contextTags = new Vector<XmlTag>();
//		Vector<RawTextFragment> list = XmlUtil.textToFragmentList(text, contextTags);
//		
//		text = "";
//		for(RawTextFragment frag: list){
//			text += " | " + frag.text;
//			for(XmlTag tag: frag.tags){
//              text += "_"+tag.name;
//			}
//		}
//		return text;
	}

	public static void main(String[] args) {
//		System.out.println(replace(""));  
//		System.out.println(replace("less than or equal to 18"));  
//		System.out.println(replace("greater than or equal to 18"));  
//		System.out.println(replace("less than or equal 18 years blah blah ... but age greater than or equal to 2.3 X"));  
//		System.out.println(replace("something greater than 34 aardvarks"));     
//		System.out.println(replace("something greater than or equal 34 aardvarks"));    
		String integerPattern = "-?\\d*\\.?\\d+";
//		String integerPattern = "-?\\d+";
		System.out.println("-30 " + "-30".matches(integerPattern));
		System.out.println("30 " + "30".matches(integerPattern));
		System.out.println("H30 " + "H30".matches(integerPattern));
		System.out.println(".30 " + ".30".matches(integerPattern));
		System.out.println("-.30 " + "-.30".matches(integerPattern));
		System.out.println("-0.30 " + "-0.30".matches(integerPattern));
		System.out.println("0.30 " + "0.30".matches(integerPattern));
		System.out.println("-110.30 " + "-110.30".matches(integerPattern));
		System.out.println("110.30 " + "110.30d".matches(integerPattern));

		System.out.println(replace("0.80-0.99"));  
		System.out.println(replace("30-day"));  
		System.out.println(replace("1-year"));  
		System.out.println(replace("half-year"));  

		System.out.println(replace("there were 35 of 200"));
		System.out.println(replace("there were 35 out of 200 people"));
		System.out.println(replace("there were 35 of the 200 people"));
		System.out.println(replace("there were 35 people out of the 200 people"));
		System.out.println(replace("there were 35 people. Out of the 200 people"));

		System.out.println(replace("there were 35 / 200"));
		System.out.println(replace("(35/200)"));
		System.out.println(replace("there were (35 / 200) "));

		System.out.println(replace("(odds ratio 1�58, 95% CI 1�07-2�36; p=0�019]. 74 (9%) of 840"));
		System.out.println(replace("hazard ratio [HR], 1.01; 95% confidence interval [CI], 0"));
		System.out.println(replace("HR, 0.59; 95% CI, 0.31-1.11; P = .10). C"));
		System.out.println(replace(" difference 0.1%, 95% CI-3.2 to 3.5; p=0.958) "));

		System.out.println(replace("were 208 pound sterling ( 361 sterling ; 308 euro ) compared with 118 pounds   sterling for hospital outpatient care"));
		System.out.println(replace("cost to the NHS was pound11.33 for paracetamol, pound8.49 for ibuprofen, and pound8.16 for both drugs."));
		System.out.println(replace("cost to the NHS was pound11.33 for paracetamol, euro8.49 for ibuprofen, and dollar8.16 for both drugs."));


		System.out.println(replace("two hundred thirty-five (10.9 %) of the"));
		System.out.println(replace("Three hundred and twenty-seven patients (blah 0.5 %) with something-or-other"));
//		System.out.println(replace("three hundred and 27 patients with something-or-other"));
		System.out.println(replace("There were eight people with X and sixty thousand seventy four without"));
		System.out.println(replace(":five:"));
		System.out.println(replace("nothing yet"));
		System.out.println(replace("(sixteen hundred)"));
		System.out.println(replace("fourty seven percent"));
		System.out.println(replace("(fourty seven per cent)"));

		System.out.println(replace("(five v forty-nine)."));

	}
}