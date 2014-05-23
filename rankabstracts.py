#!/usr/bin/env python 

"""
 Rank abstract summaries based on their information content and quality
"""

import sys
import glob
import xml
import xmlutil
import htmlutil

__author__ = 'Rodney L. Summerscales'


class XMLSummary:
    """
    Class for reading an XML summary from a file
    """
    id=None             # pubmed id
    groupNodes=None
    outcomeListNode=None
    htmlData=None

    def __init__(self, filename):
        """Given the name of a file containing the XML summary,
         parse the file and read its contents
        """
        xmldoc = xml.dom.minidom.parse(filename)
        pmidNodes = xmldoc.getElementsByTagName('Name')
        self.id = int(xmlutil.getText(pmidNodes[0]))
        subjectNodes = xmldoc.getElementsByTagName('Subjects')

        if len(subjectNodes) == 0:
            self.groupNodes = subjectNodes.getElementsByTagName('Group')
        else:
            self.groupNodes = []

        olistNodes = xmldoc.getElementsByTagName('Outcomes')
        if len(olistNodes) == 1:
            self.outcomeListNode = olistNodes[0]
        else:
            self.outcomeListNode = None

        htmlSummaryNodes = xmldoc.getElementsByTagName('HTMLData')
        if len(htmlSummaryNodes) == 1:
            self.htmlData = xmlutil.getText(htmlSummaryNodes[0])

    def countARR(self):
        """ Return number of ARR/NNT values in summary
        """
        if self.outcomeListNode is None:
            return 0

        statisticNodes = self.outcomeListNode.getElementsByTagName('Statistic')
        return len(statisticNodes)

    def countCostValues(self):
        """
        Return number of cost values in summary
        """
        if self.outcomeListNode is None:
            return 0

        statisticNodes = self.outcomeListNode.getElementsByTagName('CostValue')
        return len(statisticNodes)

    def countGroups(self):
        """
        Return number of Groups in summary
        """
        return len(self.groupNodes)

    def countOutcomes(self):
        """
         Return number of Outcomes in summary
        """
        if self.outcomeListNode is None:
            return 0

        outcomeNodes = self.outcomeListNode.getElementsByTagName('Outcome')
        return len(outcomeNodes)




if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: rankabstracts.py <INPUT_PATH> <OUTPUT_PATH> "
        print "Read XML summaries of MEDLINE abstracts in the directory specified by <INPUT_PATH>"
        print "Create HTML summary files that contain the most relevant summaries and write these to <OUTPUT_PATH>"
        sys.exit()

    inputPath = sys.argv[1]
    if len(sys.argv) > 2:
        outputPath = sys.argv[2]
    else:
        outputPath = './'

    if inputPath[-1] != '/':
        inputPath += '/'
    if outputPath[-1] != '/':
        outputPath += '/'

    # build list of summaries
    fileList = glob.glob(inputPath+'*.xml')

    # read summaries
    summaryList = []
    for filename in fileList:
        xmlSummary = XMLSummary(filename)
        summaryList.append(xmlSummary)

    # sorting hat time.
    # sort summaries into three bins
    # 1. No detected elements          (low quality)
    # 2. Some elements, but no values  (mid grade)
    # 3. Contains values               (higher quality)

    lowQuality = []
    mediumQuality = []
    highQuality1 = []
    highQuality2 = []
    for xmlSummary in summaryList:
        nARR = xmlSummary.countARR()
        nCostValues = xmlSummary.countCostValues()
        nGroups = xmlSummary.countGroups()
        nOutcomes = xmlSummary.countOutcomes()

        if nARR > 0 and nCostValues > 0:
            highQuality1.append((xmlSummary.id, xmlSummary))
        if nARR > 0 or nCostValues > 0:
            highQuality2.append((xmlSummary.id, xmlSummary))
        elif nGroups > 0 or nOutcomes > 0:
            mediumQuality.append((xmlSummary.id, xmlSummary))
        else:
            lowQuality.append((xmlSummary.id, xmlSummary))

    lowQuality.sort(reverse=True)
    mediumQuality.sort(reverse=True)
    highQuality1.sort(reverse=True)
    highQuality2.sort(reverse=True)
    highQuality = highQuality1 + highQuality2



    # write summaries to html file
    htmlFile = htmlutil.HTMLFile(title='Least relevant EBM summaries')
    for (id, xmlSummary) in lowQuality:
        htmlFile.addBodyElement(xmlSummary.htmlData)
    htmlFile.writeFile(outputPath+'summaries.low.html')

    htmlFile = htmlutil.HTMLFile(title='Somewhat relevant EBM summaries')
    for (id, xmlSummary) in mediumQuality:
        htmlFile.addBodyElement(xmlSummary.htmlData)
    htmlFile.writeFile(outputPath+'summaries.med.html')

    htmlFile = htmlutil.HTMLFile(title='Most relevant EBM summaries')
    for (id, xmlSummary) in highQuality:
        htmlFile.addBodyElement(xmlSummary.htmlData)
    htmlFile.writeFile(outputPath+'summaries.high.html')

