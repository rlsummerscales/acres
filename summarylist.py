#!/usr/bin/env python 

"""
 list of summary objects
"""

import math
import sentencefilters
import abstractsummary

from irstats import IRstats
from summarystats import SummaryStats
from templates import Templates
from entities import Entities


__author__ = 'Rodney L. Summerscales'



class SummaryList:
    """ List of EBM summaries. """
    list = []       # list of summary objects

    def __init__(self, absList, statOut, useAnnotated=False, useTrialReports=False, errorFilename='summary.errors.txt',
                 summaryStatErrorFilename='summarystats.error.txt'):
        """ Create list of EBM summaries.  All mentions, quantities should be found
          and associated in the abstracts.

          useAnnotated = True if all information should come from annotated
               information in the abstracts.
          useTrialReports = True if summaries should include info from trial reports
        """
        self.list = []

        if useAnnotated == True:
            self.computeAnnotatedSummaryStats(absList, sentencefilters.allSentences)
        else:
            self.computeSummaryStats(absList, statOut, errorFilename=summaryStatErrorFilename)
        summaryErrorFile = open(errorFilename, 'w')
        elementStats = {}
        nCorrect = {}
        nIncomplete = {}
        nAllWrong = {}
        nMissing = {}
        nEmptyCorrect = {}
        nEmptyWrong = {}


        #    mTypeList = ['age', 'condition', 'population']
        mTypeList = ['age', 'condition', 'group', 'outcome', 'group size', 'primary outcome']

        for mType in mTypeList:
            elementStats[mType] = IRstats()
            nCorrect[mType] = 0
            nIncomplete[mType] = 0
            nAllWrong[mType] = 0
            nMissing[mType] = 0
            nEmptyCorrect[mType] = 0
            nEmptyWrong[mType] = 0

        nCorrect['abstract'] = 0
        nIncomplete['abstract'] = 0
        nAllWrong['abstract'] = 0
        nMissing['abstract'] = 0
        nEmptyCorrect['abstract'] = 0
        nEmptyWrong['abstract'] = 0

        #    conditionEntityStats = {'group':{'counts':[], 'good':[], 'bad':[],'nmissing':[]}, \
        #                      'outcome':{'counts':[], 'good':[], 'bad':[], 'nmissing':[]}}
        #    ceValueTypes = ['counts', 'nmissing', 'good', 'bad']
        #
        #    for mType in conditionEntityStats.keys():
        #      for i in range(0,6):
        #        conditionEntityStats[mType]['counts'].append(0)
        #        conditionEntityStats[mType]['good'].append(0)
        #        conditionEntityStats[mType]['bad'].append(0)
        #        conditionEntityStats[mType]['nmissing'].append(0)

        nAbs = len(absList)
        for abstract in absList:
            summary = abstractsummary.Summary(abstract, useAnnotated, useTrialReports)
            self.list.append(summary)

            # calculate accuracy of each piece of eligibility criteria
            summaryErrorFile.write('---- '+abstract.id+' -----\n')
            subjectStats = summary.subjectList.computeStatistics(summaryErrorFile)
            outcomeStats = summary.outcomeList.computeStatistics(summaryErrorFile)
            stats = dict(subjectStats.items() + outcomeStats.items())

            #      for mType in ['group', 'outcome']:
            #        nFound = stats[mType].fp + stats[mType].tp
            ##        print mType, nFound, stats['condition'].recall()
            #        if nFound >= (len(conditionEntityStats[mType]['counts']) - 1):
            #          nFound = -1
            #        conditionEntityStats[mType]['counts'][nFound] += 1
            #        if stats['condition'].tp+stats['condition'].fn > 0:
            #          # something to find
            #          if stats['condition'].recall() > 0.8:
            #            conditionEntityStats[mType]['good'][nFound] += 1
            #          else:
            #            conditionEntityStats[mType]['bad'][nFound] += 1
            #        else:
            #          # nothing to find
            #          conditionEntityStats[mType]['nmissing'][nFound] += 1

            allCorrect = True
            someCorrect = False
            allMissing = True
            emptyCriteria = True
            emptyAllCorrect = True
            for mType in elementStats:
                elementStats[mType].addStats(stats[mType])
                if stats[mType].tp > 0 or stats[mType].fn > 0:
                    # something to find
                    emptyCriteria = False

                    if stats[mType].fp > 0 or stats[mType].tp > 0:
                        # found something, it may be wrong, but there is something
                        allMissing = False

                    if stats[mType].fp > 0 or stats[mType].fn > 0:
                        # Criteria section contains at least one error
                        allCorrect = False

                    if stats[mType].fp == 0 and stats[mType].fn == 0:
                        # all correct (no mistakes)
                        nCorrect[mType] += 1
                        someCorrect = True
                    elif stats[mType].tp > 0:
                        # some correct (at least one right, some FPs or FNs)
                        nIncomplete[mType] += 1
                    elif stats[mType].fp == 0:
                        # did not find anything (all FNs)
                        nMissing[mType] += 1
                    else:
                        # none correct (no TPs, some FPs or FNs)
                        nAllWrong[mType] += 1

                else:
                    # nothing to find, make sure we didn't find something anyway
                    if stats[mType].fp == 0:
                        # all correct (did not find something when we should not have)
                        nEmptyCorrect[mType] += 1
                    else:
                        # wrong (found something when we should not have)
                        nEmptyWrong[mType] += 1
                        emptyAllCorrect = False

            if emptyCriteria:
                # no criteria annotated in the abstract
                if emptyAllCorrect:
                    nEmptyCorrect['abstract'] += 1
                    summaryErrorFile.write('*** No annotated criteria ***\n')
                else:
                    nEmptyWrong['abstract'] += 1
            elif allCorrect:
                nCorrect['abstract'] += 1
            elif someCorrect:
                nIncomplete['abstract'] += 1
            elif allMissing:
                nMissing['abstract'] += 1
            else:
                nAllWrong['abstract'] += 1

        for mType,stat in elementStats.items():
            statOut.addIRstats('S - '+mType, stat)

        #    statOut.write('Abstract contains: Correct\tIncomplete \tWrong\tMissing\n')
        for type in nCorrect:
            #      statOut.write(' \t\t\t\t'+type+'\t\t\t')
            nAbs = max(1, nCorrect[type]+nIncomplete[type]+nAllWrong[type]+nMissing[type])
            statOut.addStats('Abstract contains - '+type, \
                             [['Correct', nCorrect[type]], ['%', 100*nCorrect[type]/nAbs], \
                              ['Incomplete', nIncomplete[type]], ['%', 100*nIncomplete[type]/nAbs], \
                              ['Wrong', nAllWrong[type]], ['%', 100*nAllWrong[type]/nAbs], \
                              ['Missing', nMissing[type]], ['%', 100*nMissing[type]/nAbs]])
        #       statOut.write(str(nCorrect[type])+' ('+str(100*nCorrect[type]/nAbs)+'%)\t\t')
        #       statOut.write(str(nIncomplete[type])+' ('+str(100*nIncomplete[type]/nAbs)+'%)\t\t')
        #       statOut.write(str(nAllWrong[type])+' ('+str(100*nAllWrong[type]/nAbs)+'%)\t\t')
        #       statOut.write(str(nMissing[type])+' ('+str(100*nMissing[type]/nAbs)+'%)\n')

        #    statOut.write('Abstract does NOT contain: Correct\tIncorrect\n')
        for type in nCorrect:
            #      statOut.write(' \t\t\t\t\t\t\t'+type+'\t\t\t')
            nAbs = max(1, nEmptyCorrect[type] + nEmptyWrong[type])
            statOut.addStats('Abstract does NOT contain - '+type, \
                             [['Correct', nEmptyCorrect[type]], ['%', 100*nEmptyCorrect[type]/nAbs], \
                              ['Incomplete', nEmptyWrong[type]], ['%', 100*nEmptyWrong[type]/nAbs]])

        #       statOut.write(str(nEmptyCorrect[type])+' ('+str(100*nEmptyCorrect[type]/nAbs)+'%)\t\t')
        #       statOut.write(str(nEmptyWrong[type])+' ('+str(100*nEmptyWrong[type]/nAbs)+'%)\n')

        summaryErrorFile.close()
    #    conditionErrorFile = open('conditionrecallstats.txt', 'w')
    #    for mType in conditionEntityStats.keys():
    #      conditionErrorFile.write(mType.ljust(15)+'\t')
    #      list = conditionEntityStats[mType]['counts']
    #      for i in range(0, len(list)):
    #        conditionErrorFile.write('%4d \t' % i)
    #      conditionErrorFile.write('\n')
    #      for vType in ceValueTypes:
    #        list = conditionEntityStats[mType][vType]
    #        conditionErrorFile.write(vType.ljust(15)+'\t')
    #        for value in list:
    #          conditionErrorFile.write('%4d \t' % value)
    #        conditionErrorFile.write('\n')
    #      conditionErrorFile.write('\n')
    #    conditionErrorFile.close()

    def computeAnnotatedSummaryStats(self, absList, sentenceFilter):
        """ compute summary statistics using annotated entities
            for each abstract in a given list of abstracts """
        for abstract in absList:
            for sentence in abstract.sentences:
                if sentenceFilter(sentence) == True:
                    sentence.annotatedTemplates = Templates(sentence, useLabels=False)

            # check for existence of annotated entities
            # normally they should be created during clustering stage.
            # however, when building true summaries, this stage does not happen
            if abstract.annotatedEntities == None:
                abstract.annotatedEntities = Entities(abstract)
                for mType in ['group', 'condition', 'outcome']:
                    abstract.annotatedEntities.createTrueEntities(mType, sentenceFilter)

            abstract.summaryStats = SummaryStats()
            abstract.summaryStats.computeTrueStats(abstract)


    def computeSummaryStats(self, absList, statOut, errorFilename):
        """ compute summary statistics for each abstract in a given list of
            abstracts """
        errorFile = open(errorFilename, 'w')
        #    linkFile = open('links.txt', 'w')
        totalARRStats = IRstats()
        totalARRQCStats = IRstats()

        unusedStats = IRstats()
        exactAbstractARRStats = IRstats()
        moderateAbstractARRStats = IRstats()
        liberalAbstractARRStats = IRstats()

        qcExactAbstractARRStats = IRstats()
        qcModerateAbstractARRStats = IRstats()
        qcLiberalAbstractARRStats = IRstats()

        nBad = 0
        nPredictedBad = 0
        nGood = 0
        nPredictedGood = 0
        nPolarityError = 0
        totalError = 0
        matchCount = 0
        arrSignFlips = 0
        totalUnusedError = 0
        unusedMatchCount = 0
        nIncompleteOM = 0
        nDiscardedOM = 0
        nMissingGroup = 0
        nMissingOutcome = 0
        nMissingBoth = 0

        outcomePolarities = {}
        arrStats = IRstats()
        arrQCStats = IRstats()
        for abstract in absList:
            arrStats.clear()
            arrQCStats.clear()
            errorFile.write('---- '+abstract.id+' -----\n')
            #       link = 'http://www.ncbi.nlm.nih.gov/pubmed/' + abs.id
            #       linkFile.write(abs.id+'\t'+link+'\n')

            # find ground truth summary stats
            trueSummaryTemplates = SummaryStats()
            trueSummaryTemplates.computeTrueStats(abstract)
            abstract.trueSummaryStats = trueSummaryTemplates

            # find detected summary stats
            detectedSummaryTemplates = SummaryStats()
            detectedSummaryTemplates.computeDetectedStats(abstract)
            abstract.summaryStats = detectedSummaryTemplates

            # check if summary stats are correct
            detectedSummaryTemplates.matchAnnotatedStats(trueSummaryTemplates)
            for ss in detectedSummaryTemplates.stats:
                if ss.correctlyMatched == True:
                    arrStats.incTP()
                    arrQCStats.incTP()
                    ss.evaluation.markCorrect()
                elif ss.matchingStat != None and ss.sameSign(ss.matchingStat):
                    ss.evaluation.markQualitativelyCorrect()
                    arrStats.incFP()
                    arrQCStats.incTP()
                else:
                    arrStats.incFP()
                    arrQCStats.incFP()
                    ss.evaluation.markIncorrect()
                if ss.matchingStat != None:
                    matchCount += 1
                    err = ss.arrError(ss.matchingStat)
                    totalError += err**2
                    if ss.sameSign(ss.matchingStat) == False:
                        arrSignFlips += 1
                    #          else:
                    #            ss.evaluation.markQualitativelyCorrect()

            detectedSummaryTemplates.writeSummaryStats(errorFile)

            # output summary stats that were not detected
            errorFile.write('False negatives: \n')
            for ss in trueSummaryTemplates.stats:
                if ss.correctlyMatched == False:
                    # this was not correctly detected
                    arrStats.incFN()

                    if ss.matchingStat == None or ss.matchingStat.evaluation.isQualitativelyCorrect() == False:
                        arrQCStats.incFN()

                if ss.matchingStat == None:
                    errorFile.write('\n')
                    ss.write(errorFile)


                    # keep track of number of stats with good/bad outcomes
                truePolarity = ss.outcome.outcomeIsBad(useAnnotatedPolarity=True)
                if truePolarity == True:
                    nBad += 1
                else:
                    nGood += 1
                predictedPolarity = ss.outcome.outcomeIsBad(useAnnotatedPolarity=False)
                if predictedPolarity == True:
                    nPredictedBad += 1
                else:
                    nPredictedGood += 1
                if predictedPolarity != truePolarity:
                    nPolarityError += 1
                if ss.outcome in outcomePolarities and outcomePolarities[ss.outcome] != (truePolarity, predictedPolarity):
                    print 'Polarities different for:', ss.outcome
                    print outcomePolarities[ss.outcome], 'versus', (truePolarity, predictedPolarity)
                else:
                    outcomePolarities[ss.outcome] = (truePolarity, predictedPolarity)

            errorFile.write('ARR (QC=FP): ')
            arrStats.writerpf(errorFile)
            errorFile.write('ARR (QC=TP): ')
            arrQCStats.writerpf(errorFile)

            self.incExactAbstractStats(exactAbstractARRStats, arrStats)
            self.incModerateAbstractStats(moderateAbstractARRStats, arrStats)
            self.incLiberalAbstractStats(liberalAbstractARRStats, arrStats)

            self.incExactAbstractStats(qcExactAbstractARRStats, arrQCStats)
            self.incModerateAbstractStats(qcModerateAbstractARRStats, arrQCStats)
            self.incLiberalAbstractStats(qcLiberalAbstractARRStats, arrQCStats)

            errorFile.write('Exact ARR stats (QC=FP):\n')
            exactAbstractARRStats.writerpf(errorFile)
            errorFile.write('Exact ARR stats (QC=TP):\n')
            qcExactAbstractARRStats.writerpf(errorFile)

            errorFile.write('Moderate ARR stats (QC=FP):\n')
            moderateAbstractARRStats.writerpf(errorFile)
            errorFile.write('Moderate ARR stats (QC=TP):\n')
            qcModerateAbstractARRStats.writerpf(errorFile)

            errorFile.write('Liberal ARR stats (QC=FP):\n')
            liberalAbstractARRStats.writerpf(errorFile)
            errorFile.write('Liberal ARR stats (QC=TP):\n')
            qcLiberalAbstractARRStats.writerpf(errorFile)


            # count the number of unused event rates that are correct
            detectedSummaryTemplates.matchAnnotatedEventRates(trueSummaryTemplates)
            outcomeList = abstract.entities.getList('outcome')
            for oTemplate in outcomeList:
                for om in oTemplate.unusedNumbers:
                    if om.correctlyMatched:
                        unusedStats.incTP()
                    else:
                        unusedStats.incFP()
                    if om.matchingOM != None:
                        unusedMatchCount += 1
                        err = om.eventRate() - om.matchingOM.eventRate()
                        totalUnusedError += err**2

            detectedSummaryTemplates.writeUnusedNumbers(errorFile)
            if len(detectedSummaryTemplates.incompleteOutcomeMeasurements) > 0:
                nIncompleteOM += len(detectedSummaryTemplates.incompleteOutcomeMeasurements)
                errorFile.write('Incomplete OM:\n')
                for om in detectedSummaryTemplates.incompleteOutcomeMeasurements:
                    if om.getGroup() == None and om.getOutcome() == None:
                        nMissingBoth += 1
                    #            print abstract.id, 'missing outcome'
                    elif om.getGroup() == None:
                        nMissingGroup += 1
                    elif om.getOutcome() == None:
                        nMissingOutcome += 1
                    #            print abstract.id, 'missing outcome'

                    om.write(errorFile)
            if len(detectedSummaryTemplates.discardedMeasurements) > 0:
                nDiscardedOM += len(detectedSummaryTemplates.discardedMeasurements)
                errorFile.write('Discarded OM:\n')
                for om in detectedSummaryTemplates.discardedMeasurements:
                    om.write(errorFile)
            totalARRStats.addStats(arrStats)
            totalARRQCStats.addStats(arrQCStats)

        if matchCount > 0:
            meanSqError = float(totalError)/matchCount
            rmse = math.sqrt(meanSqError)
        else:
            rmse = 0
        statOut.addStats('S - ARR RMS error', [['Matches', matchCount], \
                                               ['ARR sign flips', arrSignFlips],['RMSE', rmse] ])

        if unusedMatchCount > 0:
            meanSqError = float(totalUnusedError)/unusedMatchCount
            rmse = math.sqrt(meanSqError)
        else:
            rmse = 0
        statOut.addStats('S - Unused ER RMS error', [['Matches', unusedMatchCount], \
                                                     ['RMSE', rmse] ])


        print '------------------------------------------------------------'
        print 'IR stats for correctly finding/computing summary statistics'
        print 'TP', 'FP', 'FN', 'R', 'P', 'F'
        totalARRStats.displayrpf()

        statOut.addIRstats('S - Summary stats (QC=FP)', totalARRStats)
        statOut.addIRstats('S - Summary stats (QC=TP)', totalARRQCStats)
        #    statOut.addIRstats('S - Unused event rates', unusedStats)
        statOut.addIRstats('A - (QC=FP) ARR Exact', exactAbstractARRStats)
        statOut.addIRstats('A - (QC=FP) ARR Moderate', moderateAbstractARRStats)
        statOut.addIRstats('A - (QC=FP) ARR Liberal', liberalAbstractARRStats)

        statOut.addIRstats('A - (QC=TP) ARR Exact', qcExactAbstractARRStats)
        statOut.addIRstats('A - (QC=TP) ARR Moderate', qcModerateAbstractARRStats)
        statOut.addIRstats('A - (QC=TP) ARR Liberal', qcLiberalAbstractARRStats)

        print 'nStats:', nBad+nGood, ', nBad:', nBad, ', nGood:', nGood
        if nBad+nGood == 0:
            percentBad = 0
        else:
            percentBad = float(nBad)/(nBad+nGood)

        print '% bad:', percentBad
        print 'nStats:', nPredictedBad+nPredictedGood, ', nPredictedBad:', nPredictedBad, \
            ', nPredictedGood:', nPredictedGood

        if nPredictedBad+nPredictedGood == 0:
            percentBad = 0
            percentPolarityError = 0
        else:
            percentBad = float(nPredictedBad)/(nPredictedBad+nPredictedGood)
            percentPolarityError = float(nPolarityError)/(nPredictedBad+nPredictedGood)
        print '% predicted bad:', percentBad
        print 'Polarity error: %d (%.4f)' % (nPolarityError, percentPolarityError)

        polarityStats = IRstats()
        nBad = 0
        for (trueBadPolarity, predictedBadPolarity) in outcomePolarities.values():
            if trueBadPolarity:
                nBad += 1

            if predictedBadPolarity == False:
                # system says outcome is good
                if trueBadPolarity == predictedBadPolarity:
                    polarityStats.incTP()
                else:
                    polarityStats.incFP()
            else:
                # system says outcome is bad
                if trueBadPolarity == False:
                    polarityStats.incFN()

        if len(outcomePolarities) == 0:
            percentBad = 0
        else:
            percentBad = float(nBad)/len(outcomePolarities)
        print '% outcomes bad:', percentBad
        print 'Predicted good stats:'
        polarityStats.displayrpf()
        statOut.addIRstats('S - Good outcome predictions', polarityStats)

        polarityStats.writerpf(errorFile)

        errorFile.write('Incomplete OM = %d, Discarded OM = %d\n' % (nIncompleteOM, nDiscardedOM))
        errorFile.write('Missing G only = %d, missing O only = %d, missing both = %d\n' \
                        % (nMissingGroup, nMissingOutcome, nMissingBoth))
        errorFile.close()


    def incExactAbstractStats(self, exactAbstractARRStats, arrStats):
        """ Does this summary only have correct ARR values and is it missing any?   """
        if arrStats.tp > 0 and arrStats.fp == 0 and arrStats.fn == 0:
            exactAbstractARRStats.incTP()
        else:
            if arrStats.fp > 0 or (arrStats.fn > 0 and arrStats.tp):
                # either there are FP or we have a partial list
                exactAbstractARRStats.incFP()
            if arrStats.fn > 0 or arrStats.tp > 0:
                # There should be ARR for this abstract, but list has an error
                exactAbstractARRStats.incFN()


    def incModerateAbstractStats(self, moderateAbstractARRStats, arrStats):
        """ Does this summary only have correct ARR values? Okay if some missing """
        if arrStats.tp > 0 and arrStats.fp == 0:
            moderateAbstractARRStats.incTP()
        else:
            # no correct ARR or at least one FP
            if arrStats.fp > 0:
                moderateAbstractARRStats.incFP()
            if arrStats.fn > 0 or arrStats.tp > 0:
                # There should be ARR for this abstract, but list has an error
                moderateAbstractARRStats.incFN()


    def incLiberalAbstractStats(self, liberalAbstractARRStats, arrStats):
        """ Does this summary have any correct ARR values? Okay if some missing or incorrect  """
        if arrStats.tp > 0:
            liberalAbstractARRStats.incTP()
        else:
            # no correct ARR
            if arrStats.fp > 0:
                liberalAbstractARRStats.incFP()
            if arrStats.fn > 0:
                liberalAbstractARRStats.incFN()



    def writeEvaluations(self, filename, version):
        """ Write mysql code containing automatic evaluations for summary elements """
        out = open(filename, mode='w')
        for summary in self.list:
            eStrings = summary.getEvaluationStrings(version)
            if len(eStrings) > 0:
                out.write('INSERT INTO `answer` (`Abstract_id`, `Version`, `element_type`, ')
                out.write('`element_id`, `answer_desc`, `evaluator_id`, `create_dt`) VALUES\n')
                out.write(',\n'.join(eStrings))
                out.write(';\n\n')
            eStrings = summary.getElementStrings()
            if len(eStrings) > 0:
                out.write('INSERT INTO `element_details` (`element_id`, `value`, `matched_element`, `exact_match`) VALUES\n')
                out.write(',\n'.join(eStrings))
                out.write(';\n\n')

        out.close()


    def writeXML(self, path, version):
        """ Write summaries to XML files in the destination directory specified
            by path. """
        if len(path) > 0 and path[-1] != '/':
            path = path + '/'

        for summary in self.list:
            summary.writeXML(path, version)

    def writeHTML(self, filename):
        """ write summaries to html file. """

        out = open(filename, mode='w')
        out.write("<html><head>\n")
        out.write("<title>" + filename + "</title>\n")
        out.write("<style>body{font-family:Helvetica,Arial,sans-serif;}</style>\n")

        out.write("</head>\n")
        for summary in self.list:
            summary.writeHTML(out, showError=False)
        out.write('</body></html>\n')
        out.close()

    def writeEvaluationForm(self, path, abstractPath):
        """ write evaluation summaries to given path """
        if len(path) > 0 and path[-1] != '/':
            path = path + '/'
        if len(abstractPath) > 0 and abstractPath[-1] != '/':
            abstractPath = abstractPath + '/'

        for summary in self.list:
            summary.writeEvaluationForm(path, abstractPath)

