#!/usr/bin/python
# author: Rodney Summerscales

"""
 class definition for object that associates mentions with quantities
"""

import operator
import mentionquantityassociator
import munkres


class GroupSizeGroupAssociator(mentionquantityassociator.MentionQuantityAssociator):
    """ train/test system that associates group sizes with groups in a sentence """

    def __init__(self, useLabels=True):
        """ create a new group size, group associator. """
        mentionquantityassociator.MentionQuantityAssociator.__init__(self, 'group', 'gs', useLabels)

    def linkTemplates(self, sentence):
        """ link group size and group templates using Hungarian matching algorithm """
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
        """ link value template to best matching mention template in the same sentence.
            It is assumed that mention clustering has not occurred yet.
            """
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


        
