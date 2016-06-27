package ebm;

import java.util.*;
import org.jdom.Element;

public class NctReport {
	private class Criteria {
		Vector<Sentence> sentences = null;
		
		public Element getXMLElement(){
			Element cElement = new Element("criteria");
			for (Sentence sentence: sentences){
				cElement.addContent(sentence.getXMLElement());
			}
			
			return cElement;
		}

	}
	
	private class InterventionElement{
		Vector<Sentence> name = null;
		Vector<Sentence> description = null;
		
		public InterventionElement(Element iElement, LanguageModels models){
			Element nElement = iElement.getChild("intervention_name");
			if (nElement != null) {
				String text = nElement.getText();
				name = AnnotateText(text, models);
			}
			Element dElement = iElement.getChild("description");
			if (dElement != null) {
				String text = dElement.getText();
				description = AnnotateText(text, models);
			}

		}
		public Element getXMLElement(){
			Element iElement = new Element("intervention");
			
			if(name != null){
				Element e = new Element("name");
				for (Sentence sentence: name){
					e.addContent(sentence.getXMLElement());
				}
				iElement.addContent(e);
			}
			if(description != null){
				Element e = new Element("description");
				for (Sentence sentence: description){
					e.addContent(sentence.getXMLElement());
				}
				iElement.addContent(e);
			}

			return iElement;
		}
		
	}

	private class OutcomeElement{
		Vector<Sentence> name = null;
		Vector<Sentence> description = null;
		Vector<Sentence> times = null;
		boolean primaryOutcome = false;
		
		public OutcomeElement(Element element, LanguageModels models){
			primaryOutcome = element.getName().equalsIgnoreCase("primary_outcome");
			Element nElement = element.getChild("measure");
			if (nElement != null) {
				String text = nElement.getText();
				name = AnnotateText(text, models);
			}
			Element dElement = element.getChild("description");
			if (dElement != null) {
				String text = dElement.getText();
				description = AnnotateText(text, models);
			}
			Element tElement = element.getChild("time_frame");
			if (tElement != null) {
				String text = tElement.getText();
				times = AnnotateText(text, models);
			}
			

		}
		public Element getXMLElement(){
			Element oElement = new Element("outcome");
			if(primaryOutcome){
				oElement.setAttribute("primary", "true");
			} else {
				oElement.setAttribute("primary", "false");
			}
			
			if(name != null){
				Element e = new Element("name");
				for (Sentence sentence: name){
					e.addContent(sentence.getXMLElement());
				}
				oElement.addContent(e);
			}
			if(description != null){
				Element e = new Element("description");
				for (Sentence sentence: description){
					e.addContent(sentence.getXMLElement());
				}
				oElement.addContent(e);
			}
			if(times != null){
				Element e = new Element("times");
				for (Sentence sentence: times){
					e.addContent(sentence.getXMLElement());
				}
				oElement.addContent(e);
			}

			return oElement;
		}
		
	}

	Vector<InterventionElement> interventions = new Vector<InterventionElement>();
	Vector<OutcomeElement> outcomes = new Vector<OutcomeElement>();
	Vector<Criteria> inclusionCriteria = new Vector<Criteria>();
	Vector<Criteria> exclusionCriteria = new Vector<Criteria>();
	Vector<Criteria> allCriteria = new Vector<Criteria>();
	Vector<Sentence> conditions = new Vector<Sentence>();
	Vector<String> locations = new Vector<String>();
	String gender = "";
	String minAge = "";
	String maxAge = "";
	String id = "";
	
	/** Initialize given an xml tree containing an NCT report */
	@SuppressWarnings("unchecked")
	NctReport(Element root, LanguageModels models){
		try {
			Element idElement = root.getChild("id_info").getChild("nct_id");
			id = idElement.getText();
			
			// get conditions
			List<Element> cList = root.getChildren("condition");
			for(Element cElement: cList){
				conditions.addAll(AnnotateText(cElement.getText(), models));
			}
			
			// get locations
			Element lElement = root.getChild("location_countries");
			if(lElement != null){
				cList = lElement.getChildren("country");
				for(Element country: cList){
					locations.add(country.getText());
				}
			}
			
			// get eligibility criteria
			Element eElement = root.getChild("eligibility");
			if (eElement != null) {
				Element cElement = eElement.getChild("criteria");
				if (cElement != null) {
					Element tElement = cElement.getChild("textblock");
					if (tElement != null){
						String textblock = tElement.getText();
						if(textblock.contains("Exclusion Criteria:")){
							String[] blockParts = textblock.split("Exclusion Criteria:");
							String inclusionStr = blockParts[0].replace("Inclusion Criteria:", "");
							String exclusionStr = blockParts[1];
							inclusionCriteria = parseCriteria(inclusionStr, models);
							exclusionCriteria = parseCriteria(exclusionStr, models);
						} else {
							// just grab the entire block
							allCriteria = parseCriteria(textblock, models);
						}
					}
				}
				Element gElement = eElement.getChild("gender");
				if(gElement != null){
					gender = gElement.getText();
				}
				Element mElement = eElement.getChild("minimum_age");
				if(mElement != null){
					minAge = mElement.getText();
				}
				mElement = eElement.getChild("maximum_age");
				if(mElement != null){
					maxAge = mElement.getText();
				}
			}
			
			// get intervention information
			List<Element> iElementList = root.getChildren("intervention");
			for(Element iElement: iElementList){
				interventions.add(new InterventionElement(iElement, models));				
			}
			// get outcome information
			List<Element> oElementList = root.getChildren("primary_outcome");
			for(Element oElement: oElementList){
				outcomes.add(new OutcomeElement(oElement, models));				
			}
			oElementList = root.getChildren("secondary_outcome");
			for(Element oElement: oElementList){
				outcomes.add(new OutcomeElement(oElement, models));				
			}

		} catch (Exception e){
			System.out.println(e.getLocalizedMessage());
			e.printStackTrace();
			System.exit(-1);
		}
	}
	
	private Vector<Criteria> parseCriteria(String text, LanguageModels models){
		Vector<Criteria> cList = new Vector<Criteria>();
		text = text.replaceAll("               -", "vvvvv");
		String[] criteriaElements = text.split("-  ");
		for(String cText: criteriaElements){
			Criteria criteria = new Criteria();
			if(cText.contains("vvvvv")){
				// element contains sublist
				String[] elements = cText.split("vvvvv");
				if(elements.length > 1){
					cText = elements[0] + " " + elements[1];
					int i = 2;
					while(i < elements.length){
						cText += "; "+elements[i];
						i++;
					}
				}
				
			}
			criteria.sentences = AnnotateText(cText, models);
//			System.out.println(cText);
			if(criteria.sentences.size() > 0){
				cList.add(criteria);
			}
		}
		return cList;
	}
	
	private Vector<Sentence> AnnotateText(String text, LanguageModels models){
		Vector<RawTextFragment> fragmentList = new Vector<RawTextFragment>();
		String normalizedText = XmlUtil.normalizeText(text);
		fragmentList.add(new RawTextFragment(normalizedText));
		return models.AnnotateAndReturnSentences(fragmentList, "", "", true); 
	}
	
	/** return an XML element containing the abstract */
	public Element getXMLElement(){
		Element aElement = new Element("report");
		Element idElement = new Element("id");
		idElement.addContent(id);
		aElement.addContent(idElement);
		
		if(gender.length() > 0){
			Element gElement = new Element("gender");
			aElement.addContent(gElement);
			gElement.addContent(gender);
		}
		if(minAge.length() > 0){
			Element mElement = new Element("minAge");
			aElement.addContent(mElement);
			mElement.addContent(minAge);
		}
		if(maxAge.length() > 0){
			Element mElement = new Element("maxAge");
			aElement.addContent(mElement);
			mElement.addContent(maxAge);
		}
		
		if(locations.size() > 0) {
			Element lElement = new Element("location_countries");
			aElement.addContent(lElement);
			for(String country: locations){
				Element cElement = new Element("country");
				cElement.addContent(country);
				lElement.addContent(cElement);
			}
		}
		
		for(Sentence sentence: conditions){
			Element cElement = new Element("condition");
			cElement.addContent(sentence.getXMLElement());
			aElement.addContent(cElement);
		}
		
		if(inclusionCriteria.size() > 0){
			Element iElement = new Element("inclusion");
			aElement.addContent(iElement);
			for (Criteria criteria: inclusionCriteria){
				iElement.addContent(criteria.getXMLElement());
			}
		}
		if(exclusionCriteria.size() > 0){
			Element eElement = new Element("exclusion");
			aElement.addContent(eElement);
			for (Criteria criteria: exclusionCriteria){
				eElement.addContent(criteria.getXMLElement());
			}
		}
		if(allCriteria.size() > 0){
			Element eElement = new Element("eligibility");
			aElement.addContent(eElement);
			for (Criteria criteria: allCriteria){
				eElement.addContent(criteria.getXMLElement());
			}
		}

		for(InterventionElement iElement: interventions){
			aElement.addContent(iElement.getXMLElement());
		}
		for(OutcomeElement oElement: outcomes){
			aElement.addContent(oElement.getXMLElement());
		}
	
		return aElement;
	}

}