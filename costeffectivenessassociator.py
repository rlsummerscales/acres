#!/usr/bin/env python 

"""
Associate Cost effectiveness terms with their values
"""

__author__ = 'Rodney L. Summerscales'


import operator
import mentionquantityassociator
import munkres


class CostEffectivenessAssociator(mentionquantityassociator.MentionQuantityAssociator):
    """ train/test system that associates cost terms with cost values in a sentence """

    __algorithm = ''

    def __init__(self, algorithm, useLabels=True):
        """ create a new group size, group associator.
            algorithm = 'hungarian' to use Hungarian matching algorithm with classifier determined pair prob
                        'greedy'   to match value with closest term.
        """
        if algorithm in {'hungarian', 'greedy'}:
            self.__algorithm = algorithm
        else:
            raise ValueError(algorithm+" is not a valid association algorithm")

        mentionquantityassociator.MentionQuantityAssociator.__init__(self, 'cost_term', 'cost_value', useLabels)

    def linkTemplates(self, sentence):
        """ Link a cost effectiveness term with a value
        """
        if self.__algorithm == 'hungarian':
            self.linkTemplatesHungarian()
        else:
            self.linkTemplatesGreedy()


    def linkTemplatesHungarian(self, sentence):
        """ Link a cost effectiveness term with a value using Hungarian matching algorithm """
        templates = sentence.templates
        qTemplateList = templates.getList(self.quantityType)
        mTemplateList = templates.getList(self.mentionType)

        nQuantities = len(qTemplateList)
        nMentions = len(mTemplateList)
        maxSize = max(nQuantities, nMentions)

        if nQuantities == 0 or nMentions == 0:
            return

        probMatrix = []
        for qIdx in range(maxSize):
            probMatrix.append([])
            for mIdx in range(maxSize):
                probMatrix[qIdx].append(0)

        for fv in templates.featureVectors:
            probMatrix[fv.valueId][fv.mentionId] = fv.prob * 1000

        costMatrix = munkres.make_cost_matrix(probMatrix, lambda cost: 1000 - cost)
        m = munkres.Munkres()
        #    print probMatrix
        #    print costMatrix
        indices = m.compute(costMatrix)
        for qIdx, mIdx in indices:
            if qIdx < nQuantities and mIdx < nMentions:
                prob = probMatrix[qIdx][mIdx]
                if prob >= 500:
                    # this quantity and mention should be associated
                    prob = float(prob) / 1000
                    qTemplate = qTemplateList[qIdx]
                    mTemplate = mTemplateList[mIdx]
                    self.linkQuantityAndMention(qTemplate, mTemplate, prob)



    def linkTemplatesGreedy(self, sentence):
        """ Link a cost effectiveness term with the closest value
            """

        templates = sentence.templates
        sLength = len(sentence.tokens)

        # find the closest mention to each value.
        # In case of ties, use mention that appears before the quantity in sentence
        for qTemplate in templates.getList(self.quantityType):
            (mTemplate, dist) = templates.closestMention(qTemplate, self.mentionType)
            if mTemplate != None:
                # use distance between elements to estimate association probability
                prob = 1.0 - float(dist)/sLength
                if self.mentionType == 'outcome':
                    qTemplate.outcome = mTemplate
                    qTemplate.outcomeProb = prob
                elif self.mentionType == 'group':
                    qTemplate.group = mTemplate
                    qTemplate.groupProb = prob
                    if self.quantityType == 'gs':
                        mTemplate.addSize(qTemplate)


        # sort feature vectors by probability
        templates = sentence.templates
        fvList = sorted(templates.featureVectors, key=operator.attrgetter('prob'), reverse=True)

        for fv in fvList:
            # skip pairs that are classified as 'not associated'
            # this is pairs with probability < 0.5
            if fv.prob < 0.5:
                continue

            qIdx = fv.valueId
            qTemplateList = templates.getList(self.quantityType)
            qTemplate = templates.lists[self.quantityType][qIdx]

            mIdx = fv.mentionId
            mTemplate = templates.lists[self.mentionType][mIdx]

            if self.mentionType == 'outcome' and self.quantityType == 'on' \
                    and qTemplate.outcome == None:
                # outcome number not currently linked to any outcome, link it
                qTemplate.outcome = mTemplate
                qTemplate.outcomeProb = fv.prob
                mTemplate.numbers.append(qTemplate)
            elif self.mentionType == 'group' and self.quantityType == 'gs' \
                    and qTemplate.group == None \
                    and (mTemplate.getSize() == 0 or mTemplate.hasSize(qTemplate.value)):
                # group & group size both unlinked, link them to each other
                qTemplate.group = mTemplate
                qTemplate.groupProb = fv.prob
                mTemplate.addSize(qTemplate)
            elif self.mentionType == 'group' and self.quantityType == 'on' \
                    and qTemplate.group == None:
                # outcome number is not linked to any group, check if this one works
                oTemplate = qTemplate.outcome
                foundOutcome = False
                # make sure that the group does not already have a number
                # for this outcome
                if oTemplate != None:
                    for onTemplate in mTemplate.outcomeNumbers:
                        if onTemplate.outcome == oTemplate:
                            # this group already has an outcome number for this
                            # outcome number's outcome
                            foundOutcome = True
                            break
                if foundOutcome == False:
                    # no number for this outcome, link group and outcome number
                    qTemplate.group = mTemplate
                    qTemplate.groupProb = fv.prob

                    mTemplate.outcomeNumbers.append(qTemplate)
                    if qTemplate.groupSize != None:
                        gsTemplate = qTemplate.groupSize
                        gsTemplate.group = mTemplate
                        mTemplate.addSize(gsTemplate)
            elif self.mentionType == 'group' and self.quantityType == 'eventrate' \
                    and qTemplate.group == None:
                # event rate not linked to a group, link it
                qTemplate.group = mTemplate
                qTemplate.groupProb = fv.prob
                mTemplate.eventrates.append(qTemplate)
            elif self.mentionType == 'outcome' and self.quantityType == 'eventrate' \
                    and qTemplate.outcome == None:
                # event rate not currently linked to any outcome, link it
                qTemplate.outcome = mTemplate
                qTemplate.outcomeProb = fv.prob

