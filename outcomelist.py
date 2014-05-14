#!/usr/bin/python
# author: Rodney Summerscales

import xmlutil
from irstats import IRstats
import templates
import textevaluationform


class OutcomeList:
    """ Maintain list of outcomes measured in an abstract along with the
        summary statistics. """
    outcomeTemplates = None  # list of outcome templates for the abstract
    primaryOutcomes = None
    secondaryOutcomes = None
    abstract = None
    nTrueOutcomes = 0

    def __init__(self, abstract, useAnnotated=False, useTrialReports=True):
        """ create a list of outcomes measured and their statistics given
            an abstact object. """
        self.primaryOutcomes = []
        self.secondaryOutcomes = []
        self.nTrueOutcomes = 0
        if useAnnotated == True:
            self.outcomeTemplates = abstract.annotatedEntities.getList('outcome')
        else:
            self.outcomeTemplates = abstract.entities.getList('outcome')
        for outcome in self.outcomeTemplates:
            if outcome.isPrimary():
                self.primaryOutcomes.append(outcome)
            else:
                self.secondaryOutcomes.append(outcome)
        self.abstract = abstract

    def computeStatistics(self, errorOut):
        """ Count RPF statistics for each unique OUTCOME entity
            statOut = file stream for RPF stats for all parts of summarization system
            errorOut = file stream for TPs, FPs, FNs

            return hash of IRstats, one for each mention type, keyed by mention type
            """

        aOutcomeTemplates = self.abstract.annotatedEntities.getList('outcome')
        self.nTrueOutcomes = len(aOutcomeTemplates)
        errorOut.write('outcome:\n')
        stats = {}
        stats['outcome'] = templates.countMatches(aOutcomeTemplates, self.outcomeTemplates, errorOut)

        errorOut.write('primary outcome:\n')
        primaryOutcomeStats = IRstats()
        for oTemplate in self.outcomeTemplates:
            if oTemplate.isPrimary():
                if oTemplate.matchedTemplate != None and oTemplate.matchedTemplate.isPrimary(useAnnotated=True):
                    primaryOutcomeStats.incTP()
                    errorOut.write('  +TP: %s is PRIMARY OUTCOME\n' % oTemplate.name)
                    oTemplate.primaryOutcomeEvaluation.markCorrect()
                else:
                    primaryOutcomeStats.incFP()
                    errorOut.write('  -FP: %s is NOT known to be PRIMARY OUTCOME\n' % oTemplate.name)
                    print self.abstract.id, oTemplate.name, 'is not a primary outcome'
                    oTemplate.primaryOutcomeEvaluation.markIncorrect()
        for oTemplate in aOutcomeTemplates:
            if oTemplate.isPrimary(useAnnotated=True) and oTemplate.matchedTemplate != None \
                    and oTemplate.matchedTemplate.isPrimary() == False:
                primaryOutcomeStats.incFN()
                errorOut.write('  -FN: %s SHOULD BE PRIMARY OUTCOME\n' \
                               % oTemplate.matchedTemplate.name)

        stats['primary outcome'] = primaryOutcomeStats

        return stats

    def getGroupXML(self, doc, omTemplate, idPrefix):
        """ return XML node containing outcome results for group.
            omTemplate = outcome measurement template containing outcome info for
            the group"""
        groupNode = doc.createElement('Group')
        groupNode.setAttribute('Id', idPrefix+omTemplate.getGroup().id)
        bad = omTemplate.getOutcomes()
        if bad >= 0:
            badNode = xmlutil.createNodeWithTextChild(doc, 'Bad', str(bad))
            groupNode.appendChild(badNode)
        size = omTemplate.getGroupSize()
        if size > 0:
            gsNode = xmlutil.createNodeWithTextChild(doc, 'GroupSize', str(size))
            groupNode.appendChild(gsNode)
        er = omTemplate.eventRateString()
        if len(er) > 0:
            er = omTemplate.eventRateString()
            erNode = xmlutil.createNodeWithTextChild(doc, 'EventRate', er)
            groupNode.appendChild(erNode)
        scoreNode = xmlutil.createNodeWithTextChild(doc, 'Score', \
                                                    str(omTemplate.getConfidence()))
        groupNode.appendChild(scoreNode)
        return groupNode

    def getOutcomeXML(self, doc, oTemplate, idPrefix):
        """ write given outcome template to XML file stream """
        outcomeNode = doc.createElement('Outcome')
        if oTemplate.isPrimary():
            oType = 'primary'
        else:
            oType = 'unknown'
        poNode = xmlutil.createNodeWithTextChild(doc, 'Type', oType)
        id = idPrefix+oTemplate.id+'oType'
        poNode.setAttribute('Id', id)
        oTemplate.primaryOutcomeEvaluation.id = id
        outcomeNode.appendChild(poNode)
        id = idPrefix+oTemplate.id
        outcomeNode.setAttribute('Id', id)
        oTemplate.evaluation.id = id
        nameNode = xmlutil.createNodeWithTextChild(doc, 'Name', oTemplate.getCanonicalName())
        #      setUMLSAttribute(nameNode, oTemplate)
        outcomeNode.appendChild(nameNode)
        epCount = 0
        for ssTemplate in oTemplate.summaryStats:
            epNode = doc.createElement('Endpoint')
            id = idPrefix+oTemplate.id+'ep'+str(epCount)
            ssTemplate.evaluation.id = id
            epNode.setAttribute('id', id)
            epCount += 1
            outcomeNode.appendChild(epNode)
            epNode.appendChild(self.getGroupXML(doc, ssTemplate.lessEffective, idPrefix))
            epNode.appendChild(self.getGroupXML(doc, ssTemplate.moreEffective, idPrefix))
            if ssTemplate.time != None:
                tNode = xmlutil.createNodeWithTextChild(doc, 'time', ssTemplate.time.name)
                if len(ssTemplate.time.units) > 0:
                    tNode.setAttribute('units', ssTemplate.time.units)
                    if ssTemplate.time.value > 0:
                        tNode.setAttribute('value', str(ssTemplate.time.value))

                epNode.appendChild(tNode)
            ssNode = doc.createElement('SummaryStatistics')
            epNode.appendChild(ssNode)

            sNode = doc.createElement('Statistic')
            sNode.setAttribute('Worse', idPrefix+ssTemplate.lessEffective.getGroup().id)
            sNode.setAttribute('Better', idPrefix+ssTemplate.moreEffective.getGroup().id)
            ssNode.appendChild(sNode)

            arNode = doc.createElement('AbsoluteRisk')
            sNode.appendChild(arNode)

            arNode.setAttribute('Type', ssTemplate.riskType())
            vNode = xmlutil.createNodeWithTextChild(doc, 'Value', ssTemplate.arrString())
            arNode.appendChild(vNode)
            if ssTemplate.hasConfidenceIntervals():
                iNode = doc.createElement('Interval')
                iNode.setAttribute('lower', ssTemplate.arrLowerBound())
                iNode.setAttribute('upper', ssTemplate.arrUpperBound())
                arNode.appendChild(iNode)

            if ssTemplate.infiniteNumberNeeded() == False:
                nnNode = doc.createElement('NumberNeeded')
                sNode.appendChild(nnNode)
                nnNode.setAttribute('Type', ssTemplate.numberNeededType())
                vNode = xmlutil.createNodeWithTextChild(doc, 'Value', ssTemplate.nntString())
                nnNode.appendChild(vNode)
                if ssTemplate.hasConfidenceIntervals():
                    iNode = doc.createElement('Interval')
                    iNode.setAttribute('lower', ssTemplate.nntLowerBound())
                    iNode.setAttribute('upper', ssTemplate.nntUpperBound())
                    nnNode.appendChild(iNode)


                #     for omTemplate in oTemplate.unusedNumbers:
                #       epNode = doc.createElement('Endpoint')
                #       epNode.setAttribute('id', idPrefix+oTemplate.id+'ep'+str(epCount))
                #       epCount += 1
                #       outcomeNode.appendChild(epNode)
                #       if omTemplate.getGroup() != None:
                #         if omTemplate.getTime() != None:
                #           tNode = xmlutil.createNodeWithTextChild(doc, 'time', omTemplate.getTime().name)
                #           if len(omTemplate.getTime().units) > 0:
                #             tNode.setAttribute('units', omTemplate.getTime().units)
                #             if omTemplate.getTime().value > 0:
                #               tNode.setAttribute('value', str(omTemplate.getTime().value))
                #
                #           epNode.appendChild(tNode)
                #         outcomeNode.appendChild(epNode)
                #         epNode.appendChild(self.getGroupXML(doc, omTemplate, idPrefix))
        return outcomeNode

    def getXML(self, doc, idPrefix):
        """ return an xml node that contains information about the outcomes
            measured in the study. """
        if len(self.outcomeTemplates) == 0:
            return None

        outcomeListNode = doc.createElement('Outcomes')
        for oTemplate in self.primaryOutcomes:
            outcomeNode = self.getOutcomeXML(doc, oTemplate, idPrefix)
            outcomeListNode.appendChild(outcomeNode)
        for oTemplate in self.secondaryOutcomes:
            outcomeNode = self.getOutcomeXML(doc, oTemplate, idPrefix)
            outcomeListNode.appendChild(outcomeNode)

        return outcomeListNode

    def writeOutcomeEvaluationForm(self, template, out, primary=False):
        textevaluationform.writeEvaluationElement(template.getCanonicalName(), out)
        if primary:
            textevaluationform.writeEvaluationElement('type: primary', out, indentLevel=1)

        for ssTemplate in template.summaryStats:
            out.write(textevaluationform.bullet(1)+'Endpoint:\n')
            out.write(textevaluationform.bullet(2)+'Less effective:'+ ssTemplate.lessEffective.getGroup().name +': ')
            out.write(ssTemplate.lessEffective.statisticString())
            out.write('\n')
            out.write(textevaluationform.bullet(2)+'More effective:'+ ssTemplate.moreEffective.getGroup().name +': ')
            out.write(ssTemplate.moreEffective.statisticString())
            out.write('\n')
            rLabel = ssTemplate.riskType()
            nnLabel = ssTemplate.numberNeededType()

            out.write(textevaluationform.bullet(2)+rLabel+ ': ' + ssTemplate.arrString())
            if ssTemplate.hasConfidenceIntervals():
                out.write(',  95% confidence interval ['+ssTemplate.arrLowerBound())
                out.write(',' + ssTemplate.arrUpperBound() + ']')
            out.write('\n')

            if ssTemplate.infiniteNumberNeeded() == False:
                out.write(textevaluationform.bullet(2)+nnLabel+ ': ' + ssTemplate.nntString())
                if ssTemplate.hasConfidenceIntervals():
                    out.write(',  95% confidence interval ['+ ssTemplate.nntLowerBound())
                    out.write(ssTemplate.nntUpperBound()+']')
            out.write('\n')
            out.write(textevaluationform.evaluationPrompt(indentLevel=3))

        for omTemplate in template.unusedNumbers:
            if omTemplate.getGroup() != None:
                if omTemplate.getTime() != None:
                    time = ' ('+omTemplate.getTime().name+')'
                else:
                    time = ''
                out.write(textevaluationform.bullet(1)+'Endpoint:\n')
                out.write(textevaluationform.bullet(2)+ omTemplate.getGroup().name + ': ' )
                out.write(omTemplate.statisticString())
                out.write('\n')
                out.write(textevaluationform.evaluationPrompt(indentLevel=3))


    def writeOutcomeHTML(self, oTemplate, out, showError):
        """ write a given outcome to HTML stream """
        out.write('<li>'+oTemplate.getCanonicalName()+'<ul>\n')
        for ssTemplate in oTemplate.summaryStats:
            if ssTemplate.correctlyMatched == True or showError == False:
                color = 'black'
            else:
                color = 'red'
            out.write(' <span style=\"color:'+color+'\">')

            if ssTemplate.time != None:
                time = '('+ssTemplate.time.name+')'
            else:
                time = ''
            out.write('<li>Endpoint '+time+'<ul>')
            out.write('<li> More effective: '+ ssTemplate.moreEffective.getGroup().name + ': ' )
            out.write(ssTemplate.moreEffective.statisticString())
            out.write('</li>')
            out.write('<li> Less effective: '+ ssTemplate.lessEffective.getGroup().name+': ')
            out.write(ssTemplate.lessEffective.statisticString())
            out.write('</li>')

            rLabel = ssTemplate.riskType()
            nnLabel = ssTemplate.numberNeededType()

            out.write('<li>'+rLabel+ ': ' + ssTemplate.arrString())
            if ssTemplate.hasConfidenceIntervals():
                out.write(',  95% confidence interval ['+ssTemplate.arrLowerBound())
                out.write(',' + ssTemplate.arrUpperBound() + ']')
            if ssTemplate.infiniteNumberNeeded() == False:
                out.write('</li><li>'+nnLabel+ ': ' + ssTemplate.nntString())
                if ssTemplate.hasConfidenceIntervals():
                    out.write(',  95% confidence interval ['+ ssTemplate.nntLowerBound())
                    out.write(ssTemplate.nntUpperBound()+']')
            out.write('</li></ul></li>')
            out.write('</span>')
        for omTemplate in oTemplate.unusedNumbers:
            if omTemplate.getGroup() != None:
                if omTemplate.getTime() != None:
                    time = ' ('+omTemplate.getTime().name+')'
                else:
                    time = ''
                out.write('<li>Endpoint '+time+'<ul>')
                out.write('<li>'+ omTemplate.getGroup().name + ': ' )
                out.write(omTemplate.statisticString())
                out.write('</ul></li>')
        out.write('</ul></li>\n')

    def writeHTML(self, out, showError):
        """ write outcome list information to given output stream in html format. """
        out.write('<h3>Outcomes</h3>\n')
        out.write('<b>Primary Outcomes:</b><ul>')
        for oTemplate in self.primaryOutcomes:
            self.writeOutcomeHTML(oTemplate, out, showError)
        out.write('</ul>\n')

        out.write('<b>Secondary Outcomes:</b><ul>')
        for oTemplate in self.secondaryOutcomes:
            self.writeOutcomeHTML(oTemplate, out, showError)
        out.write('</ul>\n')


    def writeEvaluationForm(self, out):
        out.write('OUTCOMES:\n\n')
        for oTemplate in self.primaryOutcomes:
            self.writeOutcomeEvaluationForm(oTemplate, out, primary=True)

        for oTemplate in self.secondaryOutcomes:
            self.writeOutcomeEvaluationForm(oTemplate, out, primary=False)

        textevaluationform.writeElementsMissing('outcomes', out)
  

