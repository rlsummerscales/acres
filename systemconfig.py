#!/usr/bin/python

import gc
import os
import glob
import sys

import sentencefilters
import finderfilters

import abstractlist
import findertask
import mentionfinder
import bannermentionfinder
import timefinder
import agefinder
import primaryoutcomefinder
import numberfinder
import baselinenumberfinder
import costvaluefinder
import costtermfinder

import annotatedmentionfinder
import randommentionfinder
import ensemble
import mallet
import labelingreranker
import crossvalidate
import statlist

import trueoutcomemeasurementassociator
import baselinementionquantityassociator
import groupsizegroupassociator
import outcomemeasurementassociator
import baselineoutcomemeasurementassociator
import costeffectivenessassociator

import rulebasedmentionclusterer
import baselinementionclusterer
import truementionclusterer

import summarylist

import outcomemeasurementlinker
import trueoutcomemeasurementlinker
import costvaluelinker


def deleteAllXMLFiles(path):
    """ delete all xml files in a given directory """
    if len(path) > 0 and path[-1] != '/':
        path += '/'

    filelist = glob.glob(path + '*.xml')
    for file in filelist:
        #    print 'Deleting:', file
        os.remove(file)


def deleteAllModelFiles(path):
    """ delete all model files in a given directory """
    if len(path) > 0 and path[-1] != '/':
        path = path + '/'

    filelist = glob.glob(path + '*')
    for file in filelist:
        #    print 'Deleting:', file
        os.remove(file)


class RunConfiguration:
    name = None
    mentionOutputPath = None
    numberOutputPath = None
    summaryPath = None
    outputPath = None
    mentionFinderType = None
    mentionTypes = None
    numberTypes = None
    entityTypes = None
    ruleTypes = None
    version = "033"

    numberSentenceFilter = None
    groupSentenceFilter = None
    outcomeSentenceFilter = None
    conditionSentenceFilter = None
    missingOutcomeFilter = None
    groupClusterFilters = None
    outcomeClusterFilters = None

    numberFilters = [finderfilters.NumberFilter]
    groupFilter = []
    outcomeFilter = []
    conditionFilter = []

    pairTypeList = [['group', 'gs'], ['outcome', 'on'], ['outcome', 'eventrate'],
                    ['group', 'on'], ['group', 'eventrate']]

    ruleFinderTasks = []
    numberFinderTask = None
    mentionFinderTask = None
    numberFinderTasks = []
    mentionFinderTasks = []
    mentionQuantityAssociatorTasks = None
    mentionClusterTasks = None
    groupClusterTask = None
    outcomeClusterTask = None
    conditionClusterTask = None

    missingOutcomeFinderTask = None
    everythingFinderTask = None
    outcomeMeasurementLinker = None
    costValueLinker = None

    rerankLabelings = False
    postFilterResults = True
    useReport = True

    def __init__(self, name,
                 mentionTypes=['condition', 'group', 'outcome'],
                 clusterTypes=['outcome', 'condition'],
                 #                clusterTypes=['group', 'outcome', 'condition'],
                 numberTypes=['gs', 'on', 'eventrate'],
                 #                ruleTypes=['population', 'threshold', 'time', 'age'],
                 ruleTypes=['time', 'age', 'primary_outcome'],
                 mentionFinderType='mention', numberFinderType='number',
                 mentionQuantityAssociator='classifier',
                 mentionClusterType='classifier',
                 #                mentionSentenceFilter=sentencefilters.allSentences,
                 randomSeed=None,
                 desiredRecall=1,
                 boostResults=True,
                 useTrialReports=True):
        self.name = name
        self.mentionOutputPath = 'output/mentions'
        self.numberOutputPath = 'output/numbers'
        self.summaryPath = 'output/summaries'
        self.outputPath = 'output/error'
        self.mentionFinderType = mentionFinderType
        self.numberSentenceFilter = sentencefilters.numberSentencesOnly
        self.groupSentenceFilter = sentencefilters.candidateGroupSentences
        #    self.groupSentenceFilter = sentencefilters.nonTrivialSentences

        self.outcomeSentenceFilter = sentencefilters.nonTrivialSentences
        self.conditionSentenceFilter = sentencefilters.nonTrivialSentences
        self.missingOutcomeFilter = sentencefilters.outcomeNeededSentences
        self.useTrialReports = useTrialReports

        useEnsemble = True
        self.rerankType = 'any'
        #    self.rerankType = 'vote'

        self.rerankType = 'popular'
        useEnsemble = False
        # only re-rank and post-filter classifier output if using classifier for both mentions and numbers
        if numberFinderType == 'number' and mentionFinderType == 'mention':
            if useEnsemble:
                self.rerankLabelings = False
            else:
                self.rerankLabelings = True

            self.postFilterResults = True
        #      self.postFilterResults = False
        else:
            # Baseline or use annotated info
            self.rerankLabelings = False
            self.postFilterResults = False
        #      self.postFilterResults = True

        if boostResults == False:
            useEnsemble = False
            self.rerankLabelings = False

        self.mentionTypes = mentionTypes
        self.numberTypes = numberTypes
        self.entityTypes = mentionTypes
        self.ruleTypes = ruleTypes
        self.ruleFinderTasks = []
        self.ruleFinderTasks.append(findertask.FinderTask(timefinder.TimeFinder()))
        #    self.ruleFinderTasks.append(FinderTask(ThresholdFinder()))
        if mentionFinderType == 'annotated':
            ageFinder = annotatedmentionfinder.AnnotatedMentionFinder(['age'])
        else:
            ageFinder = agefinder.AgeFinder()
        self.ruleFinderTasks.append(findertask.FinderTask(ageFinder, finderFilters=[finderfilters.AgeFilter]))

        #    self.ruleFinderTasks.append(FinderTask(PopulationFinder()))
        #    self.ruleFinderTasks.append(FinderTask(LocationFinder()))
        self.ruleFinderTasks.append(findertask.FinderTask(primaryoutcomefinder.PrimaryOutcomeFinder()))

        self.ruleFinderTasks.append(findertask.FinderTask(costvaluefinder.CostValueFinder()))
        self.ruleFinderTasks.append(findertask.FinderTask(costtermfinder.CostTermFinder()))

        self.mentionQuantityAssociatorTasks = []
        self.mentionClusterTasks = []

        self.mPath = 'models/summarizer/'
        nEnsembleClassifiers = 5

        perTrain = 0.7
        self.randomSeed = randomSeed
        print 'Random seed =', self.randomSeed



        # select number finder
        if numberFinderType == 'number':
            tClassifier = mallet.MalletTokenClassifier(order=1, fullyConnected=False, nIterations=100, topK=1)
            #      tClassifier = MalletTokenClassifier(order=1, fullyConnected=True)
            #     tClassifier = MegamTokenClassifier(0.5)

            erFinder = numberfinder.NumberFinder(['eventrate'], tokenClassifier=tClassifier,
                                                 useReport=self.useTrialReports)
            numberFinder = numberfinder.NumberFinder(['on', 'gs'], tokenClassifier=tClassifier,
                                                     useReport=self.useTrialReports)
        #      erFinder = EnsembleFinder(erFinder, nClassifiers=nEnsembleClassifiers, modelPath=self.mPath, \
        #                                percentOfTraining=perTrain, duplicatesAllowed=True,\
        #                                randomSeed=self.randomSeed)
        #      numberFinder = EnsembleFinder(numberFinder, nClassifiers=nEnsembleClassifiers, modelPath=self.mPath, \
        #                                     percentOfTraining=perTrain, duplicatesAllowed=True,\
        #                                randomSeed=self.randomSeed)

        elif numberFinderType == 'annotated':
            erFinder = None
            numberFinder = annotatedmentionfinder.AnnotatedMentionFinder(self.numberTypes)
            self.numberFilters = []
        elif numberFinderType == 'baseline':
            erFinder = None
            numberFinder = baselinenumberfinder.BaselineNumberFinder(self.numberTypes)
            self.numberFilters = []
        else:
            print 'Error: unknown number finder =', numberFinderType
            sys.exit()

        tClassifier = mallet.MalletTokenClassifier(order=1, fullyConnected=True, nIterations=100, topK=15)

        #      tClassifier = MegamTokenClassifier(0.5)


        # select mention finder
        if mentionFinderType == 'mention':
            outcomeFinder = mentionfinder.MentionFinder(['outcome'], tokenClassifier=tClassifier,
                                                        labelFeatures=self.ruleTypes, useReport=self.useTrialReports,
                                                        randomSeed=self.randomSeed)
            groupFinder = mentionfinder.MentionFinder(['group'], tokenClassifier=tClassifier,
                                                      labelFeatures=self.ruleTypes, useReport=self.useTrialReports,
                                                      randomSeed=self.randomSeed)
            conditionFinder = mentionfinder.MentionFinder(['condition'], tokenClassifier=tClassifier,
                                                          labelFeatures=self.ruleTypes,
                                                          useReport=self.useTrialReports, randomSeed=self.randomSeed)

            if useEnsemble:
                oeType = 'abstract'
                #      geType='abstract'
                ##      geType='featureType'
                #      ceType = 'abstract'
                #        cOther = False
                #        cOther = True

                outcomeFinder = ensemble.EnsembleFinder(oeType, outcomeFinder, nClassifiers=nEnsembleClassifiers,
                                                        modelPath=self.mPath, rerankType=self.rerankType,
                                                        percentOfTraining=perTrain, duplicatesAllowed=True,
                                                        randomSeed=self.randomSeed)

                #      groupFinder = EnsembleFinder(geType, groupFinder,  nClassifiers=nEnsembleClassifiers, \
                #                                   modelPath=self.mPath, \
                #                                      percentOfTraining=perTrain, duplicatesAllowed=True,\
                #                                 randomSeed=self.randomSeed, countOther=cOther)

                #      conditionFinder = EnsembleFinder(ceType, conditionFinder, nClassifiers=nEnsembleClassifiers, \
                #                                       modelPath=self.mPath, \
                #                                     percentOfTraining=perTrain, duplicatesAllowed=True,\
                #                                randomSeed=self.randomSeed)
            self.groupFilters = []
            self.outcomeFilters = []
            self.groupFilters = [finderfilters.GroupFilter]
            self.outcomeFilters = [finderfilters.OutcomeFilter]
            self.conditionFilters = []
        elif mentionFinderType == 'random':
            outcomeFinder = randommentionfinder.RandomMentionFinder(['outcome'], self.randomSeed, desiredRecall)
            groupFinder = randommentionfinder.RandomMentionFinder(['group'], self.randomSeed, desiredRecall)
            conditionFinder = randommentionfinder.RandomMentionFinder(['condition'], self.randomSeed, desiredRecall)
            self.groupFilters = []
            self.outcomeFilters = []
            self.conditionFilters = []
        elif mentionFinderType == 'annotated':
            outcomeFinder = annotatedmentionfinder.AnnotatedMentionFinder(['outcome'])
            groupFinder = annotatedmentionfinder.AnnotatedMentionFinder(['group'])
            conditionFinder = annotatedmentionfinder.AnnotatedMentionFinder(['condition'])
            self.groupFilters = []
            self.outcomeFilters = []
            self.conditionFilters = []
        elif mentionFinderType == 'banner':
            outcomeFinder = bannermentionfinder.BannerMentionFinder(['outcome'])
            groupFinder = bannermentionfinder.BannerMentionFinder(['group'])
            conditionFinder = bannermentionfinder.BannerMentionFinder(['condition'])
            self.groupFilters = []
            self.outcomeFilters = []
            self.groupFilters = [finderfilters.GroupFilter]
            self.outcomeFilters = [finderfilters.OutcomeFilter]
            self.conditionFilters = []
        else:
            print 'Error: unknown mention finder =', mentionFinderType
            sys.exit()

        if self.rerankLabelings:
            labelingReRanker = labelingreranker.LabelingReRanker(groupFinder=groupFinder, outcomeFinder=outcomeFinder,
                                                                 eventrateFinder=erFinder, numberFinder=numberFinder,
                                                                 modelPath=self.mPath, jointAssignment=False,
                                                                 useRules=True, maxTopK=3, theta=0.3)
        else:
            labelingReRanker = None

        # select mention quantity associator
        mqaFinders = []
        if mentionQuantityAssociator == 'classifier':
            gsGroupAssoc = groupsizegroupassociator.GroupSizeGroupAssociator()
            on_er_associator = outcomemeasurementlinker.RuleBasedOutcomeMeasurementLinker()
            omAssoc = outcomemeasurementassociator.OutcomeMeasurementAssociator(modelPath=self.mPath,
                                                                                considerPreviousSentences=False)
            cvLinker = costvaluelinker.RuleBasedCostValueLinker()
            cvAssoc = costeffectivenessassociator.CostEffectivenessAssociator(modelPath=self.mPath, algorithm='hungarian')
            mqaFinders = [gsGroupAssoc, omAssoc, cvAssoc]
        elif mentionQuantityAssociator == 'annotated':
            on_er_associator = trueoutcomemeasurementlinker.TrueOutcomeMeasurementLinker()
            omAssoc = trueoutcomemeasurementassociator.TrueOutcomeMeasurementAssociator()
            cvLinker = costvaluelinker.RuleBasedCostValueLinker()
            mqaFinders = [omAssoc]
        elif mentionQuantityAssociator == 'baseline':
            on_er_associator = None
            #      on_er_associator = RuleBasedOutcomeMeasurementLinker()
            gsGroupAssoc = baselinementionquantityassociator.BaselineMentionQuantityAssociator('group', 'gs')
            omAssoc = baselineoutcomemeasurementassociator.BaselineOutcomeMeasurementAssociator()
            cvLinker = costvaluelinker.RuleBasedCostValueLinker()
            mqaFinders = [gsGroupAssoc, omAssoc]
        else:
            print 'Error: unknown mention quantity associator =', mentionQuantityAssociator
            sys.exit()

        # select mention clusterer
        mcFinders = []
        sFilter = {}
        sFilter['group'] = self.groupSentenceFilter
        sFilter['outcome'] = self.outcomeSentenceFilter
        sFilter['condition'] = self.conditionSentenceFilter
        if mentionClusterType == 'classifier':
            groupClusterFinder = rulebasedmentionclusterer.RuleBasedMentionClusterer('group', sFilter['group'])
            outcomeClusterFinder = rulebasedmentionclusterer.RuleBasedMentionClusterer('outcome', sFilter['outcome'])
            conditionClusterFinder = rulebasedmentionclusterer.RuleBasedMentionClusterer('condition',
                                                                                         sFilter['condition'])

            #      conditionClusterFinder = MentionClusterer('condition', sFilter['condition'], \
            #                                         threshold=0.5)
            self.groupClusterFilters = [finderfilters.groupClusterFilter]
            self.outcomeClusterFilters = [finderfilters.outcomeClusterFilter]
        elif mentionClusterType == 'annotated':
            groupClusterFinder = truementionclusterer.TrueMentionClusterer('group', sFilter['group'])
            outcomeClusterFinder = truementionclusterer.TrueMentionClusterer('outcome', sFilter['outcome'])
            conditionClusterFinder = truementionclusterer.TrueMentionClusterer('condition', sFilter['condition'])
            self.groupClusterFilters = []
            self.outcomeClusterFilters = []
        elif mentionClusterType == 'baseline':
            groupClusterFinder = baselinementionclusterer.BaselineMentionClusterer('group', sFilter['group'])
            outcomeClusterFinder = baselinementionclusterer.BaselineMentionClusterer('outcome', sFilter['outcome'])
            conditionClusterFinder = baselinementionclusterer.BaselineMentionClusterer('condition',
                                                                                       sFilter['condition'])
            self.groupClusterFilters = []
            self.outcomeClusterFilters = []
        else:
            print 'Error: unknown mention clusterer =', mentionClusterType
            sys.exit()

        # create tasks
        self.eventrateFinderTask = findertask.FinderTask(erFinder,
                                                         finderFilters=self.numberFilters,
                                                         modelFilename='erfinder.model', modelPath=self.mPath)

        self.numberFinderTask = findertask.FinderTask(numberFinder,
                                                      finderFilters=self.numberFilters,
                                                      modelFilename='numberfinder.model', modelPath=self.mPath)

        self.outcomeFinderTask = findertask.FinderTask(outcomeFinder,
                                                       finderFilters=self.outcomeFilters,
                                                       modelFilename='outcomefinder.model', modelPath=self.mPath)
        self.groupFinderTask = findertask.FinderTask(groupFinder,
                                                     finderFilters=self.groupFilters,
                                                     modelFilename='groupfinder.model', modelPath=self.mPath)

        self.conditionFinderTask = findertask.FinderTask(conditionFinder,
                                                         finderFilters=self.conditionFilters,
                                                         modelFilename='conditionfinder.model', modelPath=self.mPath)

        #    self.everythingFinderTask = FinderTask(everythingFinder, \
        #            finderFilters=self.conditionFilters+self.groupFilters+self.outcomeFilter+self.numberFilters, \
        #            modelFilename='everythingfinder.model', modelPath=self.mPath)

        self.labelingReRankerTask = findertask.FinderTask(labelingReRanker,
                                                          finderFilters=self.conditionFilters + self.groupFilters
                                                                        + self.outcomeFilter + self.numberFilters,
                                                          modelFilename='reranker.model', modelPath=self.mPath)

        self.outcomeMeasurementLinker = findertask.FinderTask(on_er_associator, modelPath=self.mPath)
        self.costValueLinker = findertask.FinderTask(cvLinker, modelPath=self.mPath)

        for finder in mqaFinders:
            finderTask = findertask.FinderTask(finder, modelPath=self.mPath)
            self.mentionQuantityAssociatorTasks.append(finderTask)

        self.groupClusterTask = findertask.FinderTask(groupClusterFinder, finderFilters=self.groupClusterFilters,
                                                      modelPath=self.mPath)
        self.outcomeClusterTask = findertask.FinderTask(outcomeClusterFinder, finderFilters=self.outcomeClusterFilters,
                                                        modelPath=self.mPath)
        self.conditionClusterTask = findertask.FinderTask(conditionClusterFinder, modelPath=self.mPath)

    #############################################################################################
    #    TRAINING
    #############################################################################################


    def train(self, trainPath, statOut=None):
        """ train models """
        #    deleteAllModelFiles(self.mPath)
        absList = abstractlist.AbstractList(trainPath, sentenceFilter=sentencefilters.allSentences,
                                            loadRegistries=False)
        self.trainOnAbstracts(absList, statOut)


    def trainOnAbstracts(self, absList, statOut=None):
        """ train models on given list of abstracts """
        print 'Training on %d abstracts' % len(absList)

        for fTask in self.ruleFinderTasks:
            fTask.test(absList, statOut)

        # train number finder and mention finder only on sentences with important numbers
        absList.applySentenceFilter(self.numberSentenceFilter)
        self.eventrateFinderTask.train(absList)
        self.numberFinderTask.train(absList)

        absList.applySentenceFilter(self.groupSentenceFilter)
        self.groupFinderTask.train(absList)

        absList.applySentenceFilter(self.outcomeSentenceFilter)
        self.outcomeFinderTask.train(absList)

        absList.applySentenceFilter(self.conditionSentenceFilter)
        self.conditionFinderTask.train(absList)

        if self.rerankLabelings:
            absList.applySentenceFilter(self.numberSentenceFilter)
            self.labelingReRankerTask.train(absList)

        absList.applySentenceFilter(sentencefilters.allSentences)
        # compute templates
        absList.createTemplates(useLabels=False)

        self.groupClusterTask.train(absList)
        self.outcomeClusterTask.train(absList)
        self.conditionClusterTask.train(absList)

        self.outcomeMeasurementLinker.train(absList)

        for finderTask in self.mentionQuantityAssociatorTasks:
            finderTask.train(absList)

        #    for finderTask in self.mentionClusterTasks:
        #      finderTask.train(absList)

        gc.collect()


    #############################################################################################
    #    TESTING
    #############################################################################################



    def test(self, testPath, statOut, abstractPath=None):
        deleteAllXMLFiles(self.summaryPath)
        # test on given files
        absList = abstractlist.AbstractList(testPath, sentenceFilter=sentencefilters.allSentences, \
                                            loadRegistries=False)

        self.testOnAbstracts(absList, statOut, abstractPath)


    def testOnAbstracts(self, absList, statOut, abstractPath=None, writeSummaries=True, foldIndex=None):
        """ apply trained model to list of abstracts """
        print 'Testing on %d abstracts' % len(absList)
        for fTask in self.ruleFinderTasks:
            fTask.test(absList, statOut, fold=foldIndex)

        # test number finder and mention finder only on sentences with important numbers
        absList.applySentenceFilter(self.numberSentenceFilter)
        self.eventrateFinderTask.test(absList, statOut, fold=foldIndex)
        self.numberFinderTask.test(absList, statOut, fold=foldIndex)

        absList.applySentenceFilter(self.groupSentenceFilter)
        self.groupFinderTask.test(absList, statOut, fold=foldIndex)

        absList.applySentenceFilter(self.outcomeSentenceFilter)
        self.outcomeFinderTask.test(absList, statOut, fold=foldIndex)

        absList.applySentenceFilter(self.conditionSentenceFilter)
        self.conditionFinderTask.test(absList, statOut)


        # re-rank alternate sentence labelings
        if self.rerankLabelings:
            #       absList.applySentenceFilter(self.numberSentenceFilter)
            # #      self.labelingReRankerTask.test(absList, statOut, fold=foldIndex)
            #       self.outcomeFinderTask.finder.rerankLabelsAndAssign(absList, rerankType='popular', topKMax=3)
            #
            #       absList.applySentenceFilter(self.groupSentenceFilter)
            #       self.groupFinderTask.computeStats(absList, statOut, fold=foldIndex)

            absList.applySentenceFilter(self.numberSentenceFilter)
            #      absList.applySentenceFilter(self.outcomeSentenceFilter)
            self.outcomeFinderTask.finder.rerankLabelsAndAssign(absList, rerankType=self.rerankType, topKMax=3,
                                                                fold=foldIndex)
            self.outcomeFinderTask.computeStats(absList, statOut, fold=foldIndex)


        # post-filter results
        if self.postFilterResults:

            absList.applySentenceFilter(self.groupSentenceFilter)
            self.groupFinderTask.filterResults(absList)

            absList.applySentenceFilter(self.outcomeSentenceFilter)
            self.outcomeFinderTask.filterResults(absList)
            self.outcomeFinderTask.computeStats(absList, statOut, fold=foldIndex)

            absList.applySentenceFilter(self.groupSentenceFilter)
            self.groupFinderTask.computeStats(absList, statOut, fold=foldIndex)

        #      absList.applySentenceFilter(self.numberSentenceFilter)
        #      self.numberFinderTask.filterResults(absList)
        #      self.numberFinderTask.computeStats(absList, statOut, fold=foldIndex)
        #      self.eventrateFinderTask.computeStats(absList, statOut, fold=foldIndex)
        else:
            absList.applySentenceFilter(self.outcomeSentenceFilter)
            self.outcomeFinderTask.computeStats(absList, statOut, fold=foldIndex)



            # test: associate mentions and quantities
        absList.applySentenceFilter(sentencefilters.allSentences)
        # compute templates
        absList.createTemplates(useLabels=True)

        self.groupClusterTask.test(absList, statOut, fold=foldIndex)
        self.outcomeClusterTask.test(absList, statOut, fold=foldIndex)
        self.conditionClusterTask.test(absList, statOut, fold=foldIndex)

        self.outcomeMeasurementLinker.test(absList, statOut, fold=foldIndex)
        self.costValueLinker.test(absList, statOut, fold=foldIndex)

        for finderTask in self.mentionQuantityAssociatorTasks:
            finderTask.test(absList, statOut, fold=foldIndex)

        self.groupClusterTask.filterResults(absList)
        self.outcomeClusterTask.filterResults(absList)

        #    for finderTask in self.mentionClusterTasks:
        #      finderTask.test(absList, statOut)

        if foldIndex != None:
            runDescription = '%s.%d' % (self.name, foldIndex)
        else:
            runDescription = self.name

        summaryFilename = 'summaries.%s.html' % runDescription
        summaryErrorFilename = 'summaries.%s.error.txt' % runDescription
        summaryStatErrorFilename = 'summarystats.%s.error.txt' % runDescription

        # Compute summary statistics
        print 'Computing summaries...'
        summaryList = summarylist.SummaryList(absList, statOut, False, self.useTrialReports,
                                              errorFilename=summaryErrorFilename, \
                                              summaryStatErrorFilename=summaryStatErrorFilename)


        # write summaries
        print 'Writing summaries...'
        summaryList.writeXML(self.summaryPath, self.version)
        print 'Writing html file...'
        summaryList.writeHTML(summaryFilename)
        #    if abstractPath != None:
        #      summaryList.writeEvaluationForm(self.summaryPath, abstractPath)

        summaryList.writeEvaluations('evaluations.' + self.name + '.sql', self.version)
        fName = 'summariesWithStats'
        if foldIndex != None:
            fName = '%s.%02d.txt' % (fName, foldIndex)
        else:
            fName = '%s.txt' % fName
        sListFile = open(fName, 'w')
        for abstract in absList:
            if abstract.summaryStats.numberOfDetectedStats() > 0:
                sListFile.write(abstract.id + '\n')
        sListFile.close()

        print 'Call garbage collection...'
        gc.collect()
        print 'GC finished'


    #############################################################################################
    #    CROSS-VALIDATE
    #############################################################################################


    def crossvalidate(self, inputPath, nFolds, statOut=None):
        deleteAllXMLFiles(self.summaryPath)
        deleteAllModelFiles(self.mPath)

        absList = abstractlist.AbstractList(inputPath, nFolds, sentenceFilter=sentencefilters.allSentences)

        svFile = open('specialvalues.txt', 'w')
        for abstract in absList:
            svFile.write('---%s---\n' % abstract.id)
            for sentence in abstract.sentences:
                svFile.write('%d: %s\n' % (sentence.index, sentence.toString()))
                for token in sentence:
                    if token.specialValueType != None:
                        svFile.write('%s\t\t%s\n' % (token.text, token.specialValueType))
        svFile.close()

        cvSets = crossvalidate.CrossValidationSets(absList, nFolds, randomSeed=self.randomSeed)

        for i, cs in enumerate(cvSets):
            #      absList.removeLabels()     # delete labels from previous round
            trainAbstracts = abstractlist.AbstractList()
            testAbstracts = abstractlist.AbstractList()
            trainAbstracts.copyList(cs.train)
            testAbstracts.copyList(cs.test)
            trainAbstracts.removeLabels()
            testAbstracts.removeLabels()

            print 'Training:', [abstract.id for abstract in trainAbstracts]
            print 'Test:', [abstract.id for abstract in testAbstracts]

            foldStats = statlist.StatList()
            self.trainOnAbstracts(trainAbstracts, foldStats)
            self.testOnAbstracts(testAbstracts, foldStats, foldIndex=i)
            foldStats.write('stats.fold%d.txt' % i, ', ')
            for name, statList in foldStats.irStats.items():
                statOut.addIRstats(name, statList[-1])  # only add final stats


    def crossvalidateEachComponent(self, inputPath, statOut):
        """ perform cross-validation """
        nFolds = 10  # 10-fold crossvalidation
        deleteAllXMLFiles(self.summaryPath)
        deleteAllModelFiles(self.mPath)

        absList = abstractlist.AbstractList(inputPath, nFolds, sentenceFilter=sentencefilters.allSentences)

        for fTask in self.ruleFinderTasks:
            fTask.test(absList, statOut)

        # train number finder and mention finder only on sentences with important numbers
        absList.applySentenceFilter(self.numberSentenceFilter)
        self.eventrateFinderTask.crossval(absList, statOut)
        self.numberFinderTask.crossval(absList, statOut)

        absList.applySentenceFilter(self.groupSentenceFilter)
        self.groupFinderTask.crossval(absList, statOut)

        # train mention clusterer on all sentences
        absList.applySentenceFilter(self.outcomeSentenceFilter)
        self.outcomeFinderTask.crossval(absList, statOut)

        absList.applySentenceFilter(self.conditionSentenceFilter)
        self.conditionFinderTask.crossval(absList, statOut)

        # associate mentions and quantities
        absList.applySentenceFilter(sentencefilters.allSentences)
        for finderTask in self.mentionQuantityAssociatorTasks:
            finderTask.crossval(absList, statOut)

        for finderTask in self.mentionClusterTasks:
            finderTask.crossval(absList, statOut)

            # Compute summary statistics
        summaryList = summarylist.SummaryList(absList, statOut)

        # write summaries
        summaryList.writeXML(self.summaryPath, self.version)
        summaryList.writeHTML('summaries.' + self.name + '.html')

