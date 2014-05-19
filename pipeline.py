#!/usr/bin/python
# apply summarization system to collection of abstracts
# author: Rodney Summerscales

import sys
import systemconfig
import statlist

learningCurve=True    # generate data for learning curves
learningCurve=False
useAnnotatedData=True  # use annotated mentions and numbers for association and clustering
useAnnotatedData=False # use DETECTED mentions and numbers for association and clustering

useTrueClustering=True  # cluster mentions using annotated ids
useTrueClustering=False # cluster mentions without annotated ids

useTrueAssociation=True # use annotated ids for associating and clustering
useTrueAssociation=False # do not use any annotated id info for associating and clustering

useReports = False     # do not use any information from trial reports
#useReports = True      # use features from trial reports

boostResults = False     
boostResults = True    # use alternate labels for ensemble to boost mention finding

randomSeed = None
randomSeed = 42
#randomSeed = 17
#randomSeed = 31
#randomSeed = 63
#randomSeed = 85

path = {}
path['test'] = '.'
path['bmj'] = 'corpora/bmj/raw'
path['cardio'] = 'corpora/cardiovascular/raw'
path['bmjcardio'] = 'corpora/combined/bmjcardio'
path['bctrain'] = 'corpora/combined/bctrain'
path['bctest'] = 'corpora/combined/bctest'
path['bctrain2'] = 'corpora/combined/bctrain2'
path['bctest2'] = 'corpora/combined/bctest2'
path['bmj0'] = 'corpora/combined/bmj0'
path['bmj1'] = 'corpora/combined/bmj1'
path['bmj2'] = 'corpora/combined/bmj2'
path['bmj3'] = 'corpora/combined/bmj3'
path['bmj4'] = 'corpora/combined/bmj4'
path['cost'] = 'corpora/bmj/costraw'

#path['ischemia-eval'] = 'corpora/ischemia/raw-eval-set1'
path['ischemia'] = 'corpora/ischemia/raw'
#path['ischemia-all'] = 'corpora/combined/ischemia-all'
path['prabhu'] = 'corpora/combined/prabhu'
path['shangda'] = 'corpora/combined/shangda'
path['smalltrain'] = 'corpora/combined/smalltrain'
path['smalltest'] = 'corpora/combined/smalltest'



label = ''

recall = 0.4
#recall = 0.5
#recall = 0.7
recall = 0.8
#recall = 0.9
#recall = 1
nFolds = 1

i = 1
while i < len(sys.argv):
  if sys.argv[i] == 'r' and i+1 < len(sys.argv):
    randomSeed = int(sys.argv[i+1])
    i += 1
  elif sys.argv[i] == 'crossval' and i+2 < len(sys.argv):
    crossvalidate = True    # perform 10-fold cross validation
    nFolds = int(sys.argv[i+1])
    train = sys.argv[i+2]
    test = train
    name = train
    i += 2
  elif i+2 == len(sys.argv):
    crossvalidate = False   # train on given set, test on another
    train = sys.argv[i]
    test = sys.argv[i+1]
    name = train+'-'+test
    i += 1
  else:
    print 'Usage:   pipeline.py [OPTIONS] crossval NFOLDS INPUTPATH'
    print '        or pipeline.py [OPTIONS] TRAINPATH TESTPATH'
    print 'OPTIONS:   r <INT>    seed random seed to given integer (default is 42)'
    sys.exit()
  i += 1
    
    
#if len(sys.argv) == 4 and sys.argv[1] == 'crossval':
#  crossvalidate = True    # perform 10-fold cross validation
#  nFolds = int(sys.argv[2])
#  train = sys.argv[3]
#  test = sys.argv[3]
#  name = train
#elif len(sys.argv) == 3:
#  crossvalidate = False   # train on given set, test on another
#  train = sys.argv[1]
#  test = sys.argv[2]
#  name = train+'-'+test
#else:
#  print 'Option not currently supported'
#  sys.exit()
  
if train not in path:
  print 'Error: training path not in list of valid paths'
  sys.exit()

if test not in path:
  print 'Error: test path not in list of valid paths'
  sys.exit()

  
if useAnnotatedData:
  nFinderType = 'annotated'
  mFinderType = 'annotated' 
  label += '.ann' 
else:
  nFinderType = 'number'
  mFinderType = 'mention'
  
  if boostResults == False:
    label += '.noboost'
  
#  mFinderType = 'random'
#  label += '.r%d'%(int(recall*100))
  
#  mFinderType = 'gimli'
#  label += '.gimli'

#  mFinderType = 'banner'
#  label += '.banner'
#   nFinderType = 'baseline'
#   label += '.basenf'
#   boostResults = False


if useTrueClustering:
  mcType = 'annotated'
  label += '.truecl'
else:
  mcType = 'classifier'
#  mcType = 'baseline'
#  label += '.basecl'
  
if useTrueAssociation:
  mqAssociatorType = 'annotated'
  label += '.trueassoc'
else:
  mqAssociatorType = 'classifier'
#  mqAssociatorType = 'baseline'
#  label += '.basemq'

  
config = systemconfig.RunConfiguration(name, numberFinderType=nFinderType, \
                       mentionFinderType=mFinderType,\
                       mentionQuantityAssociator=mqAssociatorType,\
                       mentionClusterType=mcType,\
                       randomSeed=randomSeed,\
                       desiredRecall=recall,\
                       boostResults=boostResults,\
                       useTrialReports=useReports)


abstractPath = 'corpora/ischemia/03-02-12/'

#
# Execute all finder tasks
#
# file containing statistics for all components
statList = statlist.StatList()

if crossvalidate == True:
  print '%d-fold cross-validation'%nFolds
  config.crossvalidate(path[test], nFolds, statList)
  statFilename = 'stats.crossval.%s.%d.r%d.txt'%(config.name, nFolds, randomSeed)  
  statList.write(statFilename, separator=',', computeTotal=True)

elif learningCurve:
  path = 'corpora/bmjcardio/'
  cardioTrain = ['cardio10', 'cardio20', 'cardio30']
  bmjTrain = ['bmj10', 'bmj20', 'bmj30', 'bmj60', 'bmj90', 'bmj120']
  bmjATrain = ['bmj-a10', 'bmj-a20', 'bmj-a30', 'bmj-a60']
  bmjBTrain = ['bmj-b10', 'bmj-b20', 'bmj-b30', 'bmj-b60']
  
  setATrain = ['setA10', 'setA20', 'setA30']

  cardioTest = path+'cardiotest'
  bmjTest = path+'bmjtest'
  ischemiaTest = path+'ischemia-a'


  # test and train on separate data
  trainPath = 'corpora/bmj/raw'
#  trainPath = 'corpora/cardiovascular/raw'
#  trainPath = 'corpora/bmjcardio/all'
#  trainPath = 'corpora/ischemia/raw-set-a'

#  testPath = 'corpora/ischemia/raw-set-a'
  testPath = 'corpora/cardiovascular/raw'
#  testPath = 'corpora/bmj/raw'

  testPath = '.'
  abstractPath = 'corpora/ischemia/03-02-12/'
  
#  config.train(trainPath) 
  config.test(testPath, statList)
#  config.test(testPath, statList, abstractPath, useTrialReports=False)
#  statList.write('stats.bmj.'+config.name+'.txt', separator=',')
  statList.write('stats.bmj.'+config.name+'.txt', separator=',')


  if len(sys.argv) > 2:
    run = int(sys.argv[2])
    
    if run == 0:
      statList.clear()
      for tPath in bmjTrain:
        config.train(path+tPath)
        config.test(bmjTest, statList)
      statList.write('stats.bmj.'+config.name+'.txt')
    elif run == 1:
      statList.clear()
      for tPath in bmjTrain:
        config.train(path+tPath)
        config.test(cardioTest, statList)
      statList.write('stats.bmj-cardio.'+config.name+'.txt')
    elif run == 2:  
      statList.clear()
      for tPath in cardioTrain:
        config.train(path+tPath)
        config.test(bmjTest, statList)
      statList.write('stats.cardio-bmj.'+config.name+'.txt')
    elif run == 3:
      statList.clear()
      for tPath in cardioTrain:
        config.train(path+tPath)
        config.test(cardioTest, statList)
      statList.write('stats.cardio.'+config.name+'.txt')
    elif run == 4:
      statList.clear()
      for tPath in setATrain:
        config.train(path+tPath)
        config.test(cardioTest, statList)
      statList.write('stats.ischemia-a-cardio.'+config.name+'.txt')
    elif run == 5:
      statList.clear()
      for tPath in setATrain:
        config.train(path+tPath)
        config.test(bmjTest, statList)
      statList.write('stats.ischemia-a-bmj.'+config.name+'.txt')
    elif run == 6:
      statList.clear()
      for tPath in cardioTrain:
        config.train(path+tPath)
        config.test(ischemiaTest, statList)
      statList.write('stats.cardio-ischemia-a.'+config.name+'.txt')
    elif run == 7:
      statList.clear()
      for tPath in bmjTrain:
        config.train(path+tPath)
        config.test(ischemiaTest, statList)
      statList.write('stats.bmj-ischemia-a.'+config.name+'.txt')
    elif run == 8:
      statList.clear()
#      for tPath in ischemiaTrain:
#        config.train(path+tPath)
#        config.test(ischemiaTest, statList)
#      statList.write('stats.ischemia.'+config.name+'.txt')
    elif run == 9:
      statList.clear()
      for tPath in bmjATrain:
        config.train(path+tPath)
        config.test(ischemiaTest, statList)
      statList.write('stats.bmj-a-ischemia-a.'+config.name+'.txt')
    elif run == 10:
      statList.clear()
      for tPath in bmjATrain:
        config.train(path+tPath)
        config.test(cardioTest, statList)
      statList.write('stats.bmj-a-cardio.'+config.name+'.txt')
    elif run == 11:
      statList.clear()
      for tPath in bmjBTrain:
        config.train(path+tPath)
        config.test(ischemiaTest, statList)
      statList.write('stats.bmj-b-ischemia-a.'+config.nme+'.txt')
    elif run == 12:
      statList.clear()
      for tPath in bmjBTrain:
        config.train(path+tPath)
        config.test(cardioTest, statList)
      statList.write('stats.bmj-b-cardio.'+config.name+'.txt')

else:
  # test and train on separate data  
  config.train(path[train])
  config.test(path[test], statList)
  
  if randomSeed != None:
    randomSeedLabel = '.'+str(randomSeed)
  else:
    randomSeedLabel = ''

  statFilename = 'stats.'+train+'.'+test+label+'.txt'  
  statFilename = 'stats.'+train+'.'+test+label+randomSeedLabel+'.txt'
  statList.write(statFilename, separator=' & ')

#  config.test(testPath, statList, abstractPath, useTrialReports=False)
#  statList.write('stats.'+train+'.'+test+'.txt', separator=',')






    
    
