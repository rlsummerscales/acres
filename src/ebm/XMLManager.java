package ebm;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.List;

import org.jdom.Document;
import org.jdom.Element;
import org.jdom.JDOMException;
import org.jdom.input.SAXBuilder;
import org.jdom.output.Format;
import org.jdom.output.XMLOutputter;

public class XMLManager
{
	public void doc2XML(Document doc, String filePath) throws Exception{
        Format format = Format.getCompactFormat();   
        format.setEncoding("UTF-8");
        format.setIndent("  ");
      
        XMLOutputter outputter = new XMLOutputter(format);
        FileWriter writer = new FileWriter(filePath);
        outputter.output(doc, writer);  
        writer.close();
    } 
	
	public void modify(String snomedFilePath, String inputPath, String outputPath)
	{
		SnomedLookup matcher=new SnomedLookup(snomedFilePath);
		SAXBuilder builder = new SAXBuilder();
		File file=new File(inputPath);
		if(file.isDirectory())
		{
			String[] fileList = file.list();
			for(int i=0;i<fileList.length;i++)
			{
				System.out.println("---------------------------->"+inputPath+"/"+fileList[i]);
				try {
					Document doc = builder.build(new File(inputPath+"/"+fileList[i]));
					Element root = doc.getRootElement();
					String snomedId="";
					@SuppressWarnings("unchecked")
					List<Element> sentenceNodes = root.getChildren();
					if(sentenceNodes!=null && !sentenceNodes.isEmpty()){
						for(int j=0;j<sentenceNodes.size();j++) {
							@SuppressWarnings("unchecked")
							List<Element> UMLNodes=sentenceNodes.get(j).getChildren("umls");
							for(int k=0;k<UMLNodes.size();k++)
							{
								Element UMLNode=UMLNodes.get(k);
								String id=UMLNode.getAttribute("id").getValue();
								System.out.print("precessed id: "+id);
								snomedId = matcher.getSnomedId(id);
//								snomedId= matcher.searchSnomedId(Integer.parseInt(id.substring(1)));
								if(snomedId != null){
									System.out.println("  searchSnomedId: "+snomedId);
									UMLNode.setAttribute("snomed", snomedId);
								}
								else
									System.out.println("  there is no corresponding snomed code");
							}
						}
					}
					//if the xml file name was not xxxxxxxx.raw.xml any more, the next line should be modified!
					doc2XML(doc, outputPath+"/"+fileList[i].substring(0, fileList[i].indexOf(".raw"))+".xml");
					
				} catch (JDOMException e) {
					e.printStackTrace();
				} catch (IOException e) {
					e.printStackTrace();
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		}
		else
		{
			System.out.println("error occurred when loading xml files!");
			System.out.println("xml file directory can not be found!");
		}
	}
}