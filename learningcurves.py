#!/usr/bin/python

import glob
import sys
from pylab import *

def getStats(filename, type):
  stats = []
  lines = open(filename, 'r').readlines()
  for i in range(0, len(lines)):
    line = lines[i].strip()
    if line[-1] == ':':
      line = line.replace(':', '')
      line = line.strip()
      if line == type:
        while lines[i+1][0].isdigit():
          i += 1
          line = lines[i]
          numbers = line.split()
          recall = int(numbers[3])
          precision = int(numbers[4])
          fscore = int(numbers[5])
          stats.append([recall, precision, fscore])
        return array(stats)
#      else:
#        print 'line =', line, 'type =', type
  return array(stats)                 
      

path = 'output/results/'

runName = '1'
# runTypes = ['cardio', 'cardio-ischemia-a', 'cardio-bmj', 'bmj-cardio',\
#            'bmj-ischemia-a', 'bmj', 'ischemia-a-cardio', 'ischemia-a-bmj']
# linestyles = ['b-o', 'b--D', 'b:x', 'g-o', 'g--D', 'g:x', 'r-o', 'r:x']

# runName = '2'
# runTypes = ['cardio', 'cardio-ischemia-a', \
#            'bmj-a-cardio', 'bmj-a-ischemia-a', \
#            'bmj-b-cardio', 'bmj-b-ischemia-a', \
#            'ischemia-a-cardio']
# linestyles = ['b-o', 'b--D', 'g-o', 'g--D', 'r-o', 'r--D', 'k-o']

runName = 'bmjtest'
runTypes = ['bmj-cardio', 'bmj-ischemia-a', \
           'bmj-a-cardio', 'bmj-a-ischemia-a', \
           'bmj-b-cardio', 'bmj-b-ischemia-a']
linestyles = ['b-o', 'b--D', 'g-o', 'g--D', 'r-o', 'r--D']

xAxis = {}
xAxis['cardio'] = [10, 20, 30]
xAxis['cardio-bmj'] = [10, 20, 30]
xAxis['bmj'] = [10, 20, 30, 60, 90, 120]
xAxis['bmj-cardio'] = [10, 20, 30, 60, 90, 120]
xAxis['ischemia-a-cardio'] = [10, 20, 30]
xAxis['ischemia-a-bmj'] = [10, 20, 30]
xAxis['cardio-ischemia-a'] = [10, 20, 30]
xAxis['bmj-ischemia-a'] = [10, 20, 30, 60, 90, 120]
xAxis['bmj-a-ischemia-a'] = [10, 20, 30, 60]
xAxis['bmj-a-cardio'] = [10, 20, 30, 60]
xAxis['bmj-b-ischemia-a'] = [10, 20, 30, 60]
xAxis['bmj-b-cardio'] = [10, 20, 30, 60]


typeList = ['condition', 'condition entities', 'eventrate', 'group', 'group entities', \
            'gs', 'on', 'outcome', 'outcome entities', 'Summary stats']
#typeList = ['Summary stats']           
for type in typeList:
  stats = {}
  i = 0
  f = figure()
  f.set_size_inches(8,10)

  for rType in runTypes:
    statList = glob.glob(path+'stats.'+rType+'.*.txt')
    nRuns = len(xAxis[rType])
    stats[rType] = zeros((nRuns,3))
  #  print rType
    for filename in statList:
      typeStatList = getStats(filename, type)
  #    print filename, typeStatList, len(stats[rType]), len(typeStatList)
      stats[rType] += typeStatList
    stats[rType] /= len(statList)
  #  print rType, stats[rType]
    subplot(3,1,1)
  #  print stats[rType][:,0]
    plot(xAxis[rType],stats[rType][:,0], linestyles[i], markersize=7, label=rType)
    subplot(3,1,2)
    plot(xAxis[rType],stats[rType][:,1], linestyles[i], markersize=7, label=rType)
    subplot(3,1,3)
    plot(xAxis[rType],stats[rType][:,2], linestyles[i], markersize=7, label=rType)
    i += 1
  
  #suptitle(type)
  subplot(3,1,1)
  xlabel('Training size')
  ylabel('Recall')
  title(type+': Recall')
  ylim(0, 100)
  legend(loc='center left', bbox_to_anchor=(1, 0.5))
  
  subplot(3,1,2)
  xlabel('Training size')
  ylabel('Precision')
  title(type+': Precision')
  ylim(0, 100)
  legend(loc='center left', bbox_to_anchor=(1, 0.5))
  
  subplot(3,1,3)
  xlabel('Training size')
  ylabel('F-score')
  title(type+': F-score')
  ylim(0, 100)
  legend(loc='center left', bbox_to_anchor=(1, 0.5))
  
  subplots_adjust(right=0.65, top=0.95, bottom=0.05, hspace=0.4)
  plotfilename = type.replace(' ', '_')+'-'+runName
#  f = gcf()
  f.savefig(path+plotfilename)
  
  #show()    