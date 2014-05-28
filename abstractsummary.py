#!/usr/bin/python
# author: Rodney Summerscales

"""
 EBM summary for an abstract
"""

import xmlutil
import time
import xml.dom.minidom
import StringIO

import demographicelements
import subjectlist
import outcomelist
import htmlutil


class Summary:
    """ Summary for a given abstract. All mentions, quantities should be found
        and associated. """

    abstract = None  # abstract for which this is a summary
    subjectList = None  # list of groups w/descriptions
    outcomeList = None  # list of outcomes measured in abstract
    locationList = None  # list of locations where study is performed
    summaryStatsList = None  # list of summary statistics in abstract
    randomized = False  # is the abstract describing an RCT?
    randomizedTerms = {'randomized', 'randomised', 'randomly', 'randomization',
                       'randomisation'}
    useTrialReports = False

    def __init__(self, abstract, useAnnotated=False, useTrialReports=False):
        """ build EBM related summary for a given abstract object """
        self.abstract = abstract

        self.useTrialReports = useTrialReports
        self.subjectList = subjectlist.SubjectList(abstract, useAnnotated, self.useTrialReports)
        self.outcomeList = outcomelist.OutcomeList(abstract, useAnnotated, self.useTrialReports)
        self.locationList = demographicelements.LocationList(abstract, self.useTrialReports)
        self.summaryStatList = None
        self.randomized = False
        for s in abstract.titleSentences:
            if self.containsRandomized(s):
                self.randomized = True
                break
        if self.randomized is False:
            for s in abstract.allSentences():
                if self.containsRandomized(s):
                    self.randomized = True
                    break

    def getEvaluationStrings(self, version):
        """ Return list of SQL strings containing summary element evaluations.
            These strings are part of SQL insert command into the answer table in EBM db.
            """
        eStrings = []
        tString = time.strftime("%a, %d %b %Y %H:%M:%S")
        for av in self.subjectList.ageInfo.ageValues.values():
            eStrings.append(self.sqlEvaluationString('Age', av.evaluation.id, av.evaluation.rating,
                                                     version, tString))

        for cTemplate in self.subjectList.conditionTemplates:
            eStrings.append(self.sqlEvaluationString('Condition', cTemplate.evaluation.id,
                                                     cTemplate.evaluation.rating, version, tString))

        for gTemplate in self.subjectList.groupTemplates:
            eStrings.append(self.sqlEvaluationString('Group', gTemplate.evaluation.id,
                                                     gTemplate.evaluation.rating, version, tString))
            if gTemplate.groupSizeEvaluation.isComplete():
                eStrings.append(self.sqlEvaluationString('Group_Size', gTemplate.groupSizeEvaluation.id,
                                                         gTemplate.groupSizeEvaluation.rating, version, tString))

        for oTemplate in self.outcomeList.outcomeTemplates:
            eStrings.append(self.sqlEvaluationString('Outcome', oTemplate.evaluation.id,
                                                     oTemplate.evaluation.rating, version, tString))
            if oTemplate.primaryOutcomeEvaluation.isComplete():
                eStrings.append(self.sqlEvaluationString('Primary_Outcome',
                                                         oTemplate.primaryOutcomeEvaluation.id,
                                                         oTemplate.primaryOutcomeEvaluation.rating, version, tString))
            for ssTemplate in oTemplate.summaryStats:
                eStrings.append(self.sqlEvaluationString('Endpoint', ssTemplate.evaluation.id,
                                                         ssTemplate.evaluation.rating, version, tString))

        eStrings.append(self.sqlEvaluationString('actual_Age', 'Actual_Ages_no.s',
                                                 self.subjectList.ageInfo.nTrueAgeValues, version, tString))
        eStrings.append(self.sqlEvaluationString('actual_Condition', 'Actual_Condition_no.s',
                                                 self.subjectList.nTrueConditions, version, tString))
        eStrings.append(self.sqlEvaluationString('actual_Group', 'Actual_Group_no.s',
                                                 self.subjectList.nTrueGroups, version, tString))
        eStrings.append(self.sqlEvaluationString('actual_Outcome', 'Actual_Outcomes_no.s',
                                                 self.outcomeList.nTrueOutcomes, version, tString))
        eStrings.append(self.sqlEvaluationString('actual_Endpoint', 'Actual_ARR_no.s',
                                                 len(self.abstract.trueSummaryStats.stats), version, tString))

        return eStrings

    def sqlEvaluationString(self, elementType, elementId, answerDesc, version, timeString):
        """ return SQL element evaluation string """

        eString = '(%s, \'%s\', \'%s\', \'%s\', \'%s\',\'%s\', \'%s\')' \
                  % (self.abstract.id, version, elementType, elementId, answerDesc, 'auto', timeString)
        return eString

    def getElementStrings(self):
        """ Return list of SQL strings containing evaluated summary element values.
            These strings are part of SQL insert command into the element table in EBM db.
            """
        eStrings = []
        for av in self.subjectList.ageInfo.ageValues.values():
            eStrings.append(self.sqlElementString(av.evaluation.id, av.toString(), None, False))

        for cTemplate in self.subjectList.conditionTemplates:
            eStrings.append(self.sqlElementString(cTemplate.evaluation.id,
                                                  cTemplate.toString(), cTemplate.matchedTemplate,
                                                  cTemplate.exactMatch))

        for gTemplate in self.subjectList.groupTemplates:
            eStrings.append(self.sqlElementString(gTemplate.evaluation.id,
                                                  gTemplate.toString(), gTemplate.matchedTemplate,
                                                  gTemplate.exactMatch))
            if gTemplate.groupSizeEvaluation.isComplete():
                eStrings.append(self.sqlElementString(gTemplate.groupSizeEvaluation.id,
                                                      gTemplate.getSize(maxSize=True), None, False))

        for oTemplate in self.outcomeList.outcomeTemplates:
            eStrings.append(self.sqlElementString(oTemplate.evaluation.id,
                                                  oTemplate.toString(), oTemplate.matchedTemplate,
                                                  oTemplate.exactMatch))
            if oTemplate.primaryOutcomeEvaluation.isComplete():
                eStrings.append(self.sqlElementString(oTemplate.primaryOutcomeEvaluation.id,
                                                      oTemplate.toString(), None, False))
            for ssTemplate in oTemplate.summaryStats:
                eStrings.append(self.sqlElementString(ssTemplate.evaluation.id,
                                                      ssTemplate.toString(), ssTemplate.matchingStat,
                                                      ssTemplate.correctlyMatched))

        return eStrings

    @staticmethod
    def sqlElementString(elementId, elementDescription, matchingElement, exactMatch):
        """ return SQL element description string """
        if matchingElement is None:
            eString = '(\'%s\', \'%s\', NULL, %s)' % (elementId, elementDescription, exactMatch)
        else:
            eString = '(\'%s\', \'%s\', \'%s\', %s)' \
                      % (elementId, elementDescription, matchingElement.toString(), exactMatch)
        return eString

    def containsRandomized(self, sentence):
        """ return True if given sentence contains language that implies that the study
            was randomized """
        for token in sentence:
            if token.text.lower() in self.randomizedTerms:
                return True
        return False

    def writeXML(self, path, version):
        """ Write summary to XML file in the destination directory specified
            by path. """
        idPrefix = self.abstract.id + 'v' + version
        # build XML summary
        doc = xml.dom.minidom.Document()
        articleNode = doc.createElement('Study')
        if self.randomized:
            articleNode.setAttribute('RandomizationPresent', 'true')
        else:
            articleNode.setAttribute('RandomizationPresent', 'false')

        articleNode.setAttribute('Version', version)
        gmTime = time.gmtime()
        cNode = doc.createElement('Created')
        articleNode.appendChild(cNode)
        cNode.appendChild(xmlutil.createNodeWithTextChild(doc, 'Month', str(gmTime.tm_mon)))
        cNode.appendChild(xmlutil.createNodeWithTextChild(doc, 'Day', str(gmTime.tm_mday)))
        cNode.appendChild(xmlutil.createNodeWithTextChild(doc, 'Year', str(gmTime.tm_year)))

        nameNode = xmlutil.createNodeWithTextChild(doc, 'Name', self.abstract.id)
        articleNode.appendChild(nameNode)
        titleString = ''
        for s in self.abstract.titleSentences:
            titleString += s.toString()
        titleNode = xmlutil.createNodeWithTextChild(doc, 'Title', titleString)
        articleNode.appendChild(titleNode)
        link = 'http://www.ncbi.nlm.nih.gov/pubmed/' + self.abstract.id
        linkNode = xmlutil.createNodeWithTextChild(doc, 'AbstractLink', link)
        articleNode.appendChild(linkNode)

        if self.abstract.report is not None and self.abstract.report.id[0:3] == 'NCT':
            link = 'http://clinicaltrials.gov/ct2/show/study/' + self.abstract.report.id
            linkNode = xmlutil.createNodeWithTextChild(doc, 'TrialRegistryLink', link)
            articleNode.appendChild(linkNode)

        node = self.locationList.getXML(doc, idPrefix)
        if node is not None:
            articleNode.appendChild(node)

        if self.useTrialReports and self.abstract.report is not None \
                and len(self.abstract.report.conditions) > 0:
            cListNode = doc.createElement('ConditionsOfInterest')
            articleNode.appendChild(cListNode)
            for condition in self.abstract.report.conditions:
                cNode = doc.createElement('Condition')
                cNode.appendChild(xmlutil.createNodeWithTextChild(doc, 'Name',
                                                                  condition.sentences[0].toString()))
                cNode.setAttribute('source', 'trial_registry')
                cListNode.appendChild(cNode)

        node = self.subjectList.getXML(doc, idPrefix)
        if node is not None:
            articleNode.appendChild(node)

        node = self.outcomeList.getXML(doc, idPrefix)
        if node is not None:
            articleNode.appendChild(node)

        if self.abstract.meshHeadingList is not None:
            articleNode.appendChild(self.abstract.meshHeadingList.getXML(doc))

        htmlString = StringIO.StringIO()
        self.writeHTML(htmlString, showError=False)
        htmlNode = xmlutil.createNodeWithTextChild(doc, 'HTMLData', htmlString.getvalue())
        articleNode.appendChild(htmlNode)
        htmlString.close()

        # write summary to XML file
        filename = path + self.abstract.id + '.summary.xml'
        out = open(filename, 'w')
        out.write('<?xml version="1.0" encoding="utf-8"?>\n')
        #    out.write('<?xml-stylesheet href="abstract.xsl" type="text/xsl"?>\n')
        xmlutil.writexml(articleNode, out)
        out.close()

    def writeHTML(self, out, includeReport=False, showError=True):
        """ write summary in html format to given output stream. """
        htmlutil.HTMLBeginTable(out)

        htmlutil.HTMLBeginRow(out)

        link = 'http://www.ncbi.nlm.nih.gov/pubmed/' + self.abstract.id
        out.write('<h2><a href="%s">%s:</a></h2>\n' % (link, self.abstract.id))

        htmlutil.HTMLColumnBreak(out)

        titleString = ''
        for s in self.abstract.titleSentences:
            titleString += s.toPrettyString()
        out.write('<h2>' + titleString + '</h2>')

        htmlutil.HTMLEndRow(out)
        htmlutil.HTMLBeginRow(out)

        htmlutil.HTMLBeginRow(out)
        htmlutil.HTMLWriteText(out,'Authors:', bold=True)
        htmlutil.HTMLColumnBreak(out)
        htmlutil.HTMLEndRow(out)

        htmlutil.HTMLBeginRow(out)
        htmlutil.HTMLWriteText(out,'Journal:', bold=True)
        htmlutil.HTMLColumnBreak(out)
        out.write(self.abstract.publicationInformation.getJournal())
        htmlutil.HTMLEndRow(out)

        htmlutil.HTMLBeginRow(out)
        htmlutil.HTMLWriteText(out,'Country:', bold=True)
        htmlutil.HTMLColumnBreak(out)
        country = self.abstract.publicationInformation.getCountry()
        out.write(country)
        htmlutil.HTMLEndRow(out)

        htmlutil.HTMLBeginRow(out)
        htmlutil.HTMLWriteText(out,'Date:', bold=True)
        htmlutil.HTMLColumnBreak(out)
        out.write(self.abstract.publicationInformation.getPublicationDate())
        htmlutil.HTMLEndRow(out)

        htmlutil.HTMLBeginRow(out)
        htmlutil.HTMLWriteText(out,'Publication types:', bold=True)
        htmlutil.HTMLColumnBreak(out)
        pTypeList = self.abstract.publicationInformation.getPublicationTypes()
        for pType in pTypeList:
            htmlutil.HTMLWriteText(out, pType+'<br>')
        htmlutil.HTMLEndRow(out)


        htmlutil.HTMLEndTable(out)

        out.write('<p>')
        self.abstract.writeHTML(out, ['group', 'outcome', 'condition',
                                      'eventrate', 'on', 'gs', 'cost_value'], showError)
        #    self.abstract.writeHTML(out)
        if self.useTrialReports and includeReport and self.abstract.report is not None:
            out.write('<h2>Report</h2><ul>\n')
            report = self.abstract.report
            out.write('<li>ID: ' + report.id + '</li>\n')
            if len(report.gender) > 0:
                out.write('<li>Gender: ' + report.gender + '</li>\n')
            if len(report.minAge) > 0:
                out.write('<li>Minimum Age: ' + report.minAge + '</li>\n')
            if len(report.maxAge) > 0:
                out.write('<li>Maximum Age: ' + report.maxAge + '</li>\n')
            if len(report.conditions) > 0:
                out.write('<li>Conditions<ul>\n')
                for condition in report.conditions:
                    out.write('<li>')
                    for s in condition.sentences:
                        out.write(s.toString())
                    out.write('</li>')
                out.write('</ul></li>\n')
            if len(report.eligibilityCriteria) > 0:
                out.write('<li>Eligibility Criteria<ul>\n')
                for criteria in report.eligibilityCriteria:
                    out.write('<li>')
                    for s in criteria.sentences:
                        out.write(s.toString())
                    out.write('</li>')
                out.write('</ul></li>\n')
            if len(report.inclusionCriteria) > 0:
                out.write('<li>Inclusion Criteria<ul>\n')
                for criteria in report.inclusionCriteria:
                    out.write('<li>')
                    for s in criteria.sentences:
                        out.write(s.toString())
                    out.write('</li>')
                out.write('</ul></li>\n')
            if len(report.exclusionCriteria) > 0:
                out.write('<li>Exclusion Criteria<ul>\n')
                for criteria in report.exclusionCriteria:
                    out.write('<li>')
                    for s in criteria.sentences:
                        out.write(s.toString())
                    out.write('</li>')
                out.write('</ul></li>\n')
            if len(report.interventions) > 0:
                out.write('<li>Interventions<ul>\n')
                for intervention in report.interventions:
                    out.write('<li>')
                    for s in intervention.name:
                        out.write(s.toString())
                    if len(intervention.description) > 0:
                        out.write('<ul><li>')
                        for s in intervention.description:
                            out.write(s.toString())
                        out.write('</li></ul>')
                    out.write('</li>')
                out.write('</ul></li>\n')
            if len(report.outcomes) > 0:
                out.write('<li>Outcomes<ul>\n')
                for outcome in report.outcomes:
                    out.write('<li>')
                    for s in outcome.name:
                        out.write(s.toString())
                    if len(outcome.description) > 0:
                        out.write('<ul><li>')
                        for s in outcome.description:
                            out.write(s.toString())
                        out.write('</li></ul>')
                    out.write('</li>')
                out.write('</ul></li>\n')

            out.write('</ul>\n')
        #     for sentence in self.abstract.sentences:
        #       out.write(sentence.toString() + '<br>')
        out.write('</p>')
        #    self.locationList.writeHTML(out)
        self.subjectList.writeHTML(out)
        self.outcomeList.writeHTML(out, showError)


