#!/usr/bin/python
from irstats import IRstats

class StatList:
  """ collection of statistics from a run or series of runs """
  irStats = {}
  labeledStats = {}
  
  def __init__(self):
    self.irStats = {}
    self.labeledStats = {}
    
  def clear(self):
    """ erase all stored stats """
    self.irStats = {}
    self.labeledStats = {}
    
  def copy(self, statList):
    """ copy stats from given stat list to this one """
    for name, irStatList in statList.irStats.items():
      for irStats in irStatList:
        self.addIRstats(name, irStats)
    for name, labeledLists in statList.labeledStats.items():
      for lList in labeledLists:
        self.addStats(name, lList)
        
  def addIRstats(self, name, irStats):
    """ add IRstats from a given entity """
    if name in self.irStats:
      self.irStats[name].append(irStats)
    else:
      self.irStats[name] = [irStats]
    
  def addStats(self, name, labeledList):
    """ add labeled list of stats for a given entity. 
        List is two dimensional of the form
        [[labelString1, value2], ..., [labelStringN, valueN]]"""
    if name in self.labeledStats:
      self.labeledStats[name].append(labeledList)
    else:
      self.labeledStats[name] = [labeledList]
      
  def write(self, filename, separator='  ', computeTotal=False, computeAverage=False):
    """ write all stats to a file """
    out = open(filename, 'w')
    nameList = self.irStats.keys()
    nameList.sort()
    for name in nameList:
      out.write(name+':\n')
      list = self.irStats[name]
      for irStat in list:
        out.write(separator)
        irStat.writerpf(out, separator)
      if computeTotal:
        totalStat = IRstats()
        for irStat in list:
          totalStat.addStats(irStat)
        out.write(separator)
        totalStat.writerpf(out, separator)    
      if computeAverage:
        rSum = 0.0
        pSum = 0.0
        fSum = 0.0
        dupPSum = 0.0
        for irStat in list:
          rSum += irStat.recall()
          pSum += irStat.precision()
          fSum += irStat.fscore()
          dupPSum += irStat.precisionWithoutDuplicates()
        nStat = len(list)  
        out.write('%s%s%s%s%.2f%s%.2f%s%.2f%4s%.2f\n'%(separator.ljust(5), separator.ljust(5), separator.ljust(5), \
                                                      separator, rSum/nStat, separator, pSum/nStat, separator,\
                                                       fSum/nStat, separator, dupPSum/nStat))

    nameList = self.labeledStats.keys()
    nameList.sort()
    nameList.reverse()
    for name in nameList:
      out.write(name+':\n')
      lists = self.labeledStats[name]
      out.write(separator)
      for [label, value] in lists[0]:
        out.write(label+separator)
      out.write('\n')
      out.write(separator)

      for list in lists:
        for [label, value] in list:
          if isinstance(value, float):
            out.write('%.4f%s' % (value, separator))
          else:
            out.write('%d%s' % (value, separator))
        out.write('\n')
    out.close()