#!/usr/bin/python
# author: Rodney Summerscales

import shutil
import os
import glob
import random

def deleteAllXMLFiles(path):
  """ delete all xml files in a given directory """
  if len(path) > 0 and path[-1] != '/':
    path = path + '/'

  filelist = glob.glob(path+'*.xml')
  for file in filelist:
#    print 'Deleting:', file
    os.remove(file)

def copyList(filelist, directory):
  """ copy list of files to given directory """
  for i in range(0, len(filelist)):
    parts = filelist[i].split('/')
    dir = parts[0]
    if os.path.isdir(directory) == False:
      os.makedirs(directory)
    filename = parts[-1]
    shutil.copy(filelist[i], directory+'/'+filename)

#############################################
cardioPath = 'corpora/cardiovascular/raw/'
bmjPath = 'corpora/bmj/raw/'
#bmjAPath = 'bmj-a/'
#bmjBPath = 'bmj-b/'
#setAPath = 'corpora/ischemia/raw/'
#setBPath = 'corpora/ischemia/raw-eval-set1/'
#autoPath = 'corpora/ischemia/auto/raw/'

combinedPath = 'corpora/combined/'
#ischemiaPath = combinedPath + 'ischemia-all'
bmjcardioPath = combinedPath + 'bmjcardio'
bcTrainPath = combinedPath + 'bctrain'
bcTestPath = combinedPath + 'bctest'
bcAutoPath = combinedPath + 'bcauto'
#bcTrainPath2 = combinedPath + 'bctrain2'
#bcTestPath2 = combinedPath + 'bctest2'
smallTrainPath = combinedPath + 'smalltrain'
smallTestPath = combinedPath + 'smalltest'


cardioList = glob.glob(cardioPath+'*.xml')
bmjList = glob.glob(bmjPath+'*.xml')
#setAList = glob.glob(setAPath+'*.xml')
#setBList = glob.glob(setBPath+'*.xml')
#autoList = glob.glob(autoPath+'*.auto.xml')

nCardio = len(cardioList)
nBMJ = len(bmjList)

#bmjSmallPath = []
#nBmjSmall = 5
#for i in range(nBmjSmall):
#  bmjSmallPath.append('%sbmj%d'%(combinedPath, i))
#  deleteAllXMLFiles(bmjSmallPath[i])

#absOccurrences = {}
#for i in range(nBmjSmall):
#  random.seed(i)
#  random.shuffle(bmjList)
#  bmjSmall = bmjList[:nCardio]
#  copyList(bmjSmall, bmjSmallPath[i])
#  for abstract in bmjSmall:
#    if abstract in absOccurrences:
#      absOccurrences[abstract] += 1
#    else:
#      absOccurrences[abstract] = 1
#      
#for abstract in absOccurrences:
#  if absOccurrences[abstract] > 1:
#    print abstract, ':', absOccurrences[abstract] 

  
#extraPath = 'unannotated/'
#boosted20 = ['20', '20b20', '20b40', '20b80']
#boosted40 = ['40', '40b20', '40b40', '40b80']
targetDirectories = [bmjcardioPath, bcTrainPath, bcTestPath, \
                     smallTrainPath, smallTestPath]
                    
for dir in targetDirectories:
#  print 'deleting all files in', dir
  deleteAllXMLFiles(dir)

copyList(cardioList, bmjcardioPath)
copyList(bmjList, bmjcardioPath)

    

#copyList(cardioList, bcAutoPath)
#copyList(bmjList, bcAutoPath)
#copyList(autoList, bcAutoPath)

#copyList(setAList, ischemiaPath)
#copyList(setBList, ischemiaPath)

#random.seed(42)
#random.seed(21)
#random.seed(50)
#random.seed(11)
random.seed(17)

random.shuffle(cardioList)
random.shuffle(bmjList)
#random.shuffle(setAList)

nCardioTrain = int(0.7*nCardio)
nBMJTrain = int(0.7*nBMJ)

print nCardio, nCardioTrain
print nBMJ, nBMJTrain  
  
trainCardio = cardioList[:nCardioTrain]
testCardio = cardioList[nCardioTrain:]
trainBMJ = bmjList[:nBMJTrain]
testBMJ = bmjList[nBMJTrain:]

copyList(trainCardio, bcTrainPath)
copyList(trainBMJ, bcTrainPath)
copyList(testCardio, bcTestPath)
copyList(testBMJ, bcTestPath)

random.seed(11)
random.shuffle(cardioList)
random.shuffle(bmjList)

trainCardio = cardioList[:nCardioTrain]
testCardio = cardioList[nCardioTrain:]
trainBMJ = bmjList[:nBMJTrain]
testBMJ = bmjList[nBMJTrain:]

#copyList(trainCardio, bcTrainPath2)
#copyList(trainBMJ, bcTrainPath2)
#copyList(testCardio, bcTestPath2)
#copyList(testBMJ, bcTestPath2)

nCardioTrain = 10
nCardioTest = 5
trainCardio = cardioList[:nCardioTrain]
testCardio = cardioList[nCardioTrain:(nCardioTrain+nCardioTest)]

copyList(trainCardio, smallTrainPath)
copyList(testCardio, smallTestPath)

  

