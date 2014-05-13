#!/usr/bin/python
# author: Rodney Summerscales

import sys
from irstats import IRstats 

class AverageStat:
  r = 0.0
  p = 0.0
  d = 0.0
  
  def __init__(self, r, p, dp):
    self.r = r
    self.p = p
    self.dp = dp
  
  def recall(self):
    return self.r
  
  def precision(self):
    return self.p

  def precisionWithoutDuplicates(self):
    return self.dp
  
  def fscore(self):
    """ compute F1-score. 2(RP)/(R+P)
        returns: f1-score value
    """ 
    r = self.recall()
    p = self.precision()
    if (r + p) == 0:
      return 0.0
    return 2 * (r * p) / (r + p)

  def writerpf(self, out, separator='  '):
    """ Output stats to txt file 
      parms:  out = output stream object
              separator = string used to separate numbers in output stream
    """
    out.write('    %s    %s    %s %.2f %s %.2f %s %.2f %s  %.2f\n' \
            % (separator, separator, separator,\
               self.recall(), separator, \
               self.precision(), separator, self.fscore(), separator, self.dp))

    

class StatsItem:
  """ statistics for an element in the stats file """
  heading = None
  stats = None
  separator = None
  
  def __init__(self, heading, separator):
    self.heading = heading
    self.stats = []
    self.separator = separator
      
  def addStatLine(self, statLine):
    parsedLine = statLine.strip().split(self.separator)
    if len(parsedLine) == 8 and parsedLine[0][0:2] == 'av':
      self.stats.append(AverageStat(r=float(parsedLine[4]), \
                                    p=float(parsedLine[5]), dp=float(parsedLine[7])))
    elif len(parsedLine) == 7 \
       or (len(parsedLine) == 10 and parsedLine[1].isalpha() == False \
           and len(parsedLine[9].strip()) > 0):
      if len(parsedLine) == 10:
        dup = int(parsedLine[7])
        
      else:
        dup = 0
      
      stat = IRstats(tp=int(parsedLine[1]), fp=int(parsedLine[2]),\
                     fn=int(parsedLine[3]), duplicates=dup)
      
#      self.stats.append(stat)
      # only keep track of most recent stat
      self.stats = [stat]
  
  def hasStats(self):
    return len(self.stats) > 0
      
  def write(self, out, rowHeading=None, displayHeading=True, firstColumnWidth=0):
    if firstColumnWidth == 0:
      firstColumnWidth = len(rowHeading)+2 

    if displayHeading:
      if rowHeading != None:
        out.write(' '.rjust(firstColumnWidth))
      out.write(self.heading)
      
    for stat in self.stats:
      if rowHeading != None:
        out.write(rowHeading.ljust(firstColumnWidth)+self.separator)
      stat.writerpf(out, separator=' '+self.separator+' ')
    
  def display(self):
    self.write(sys.stdout)
    
class StatsFile:
  """ File containing statistics from one or more summarization system runs """
  contents = None
  name = None
  separator = None
  
  def __init__(self, filename, separator):
    self.contents = {}
    self.separator = separator
    self.name = filename.replace('stats.','')
    self.name = self.name.replace('.txt','')
    self.read(filename)
    
  def read(self, filename):
    """ read a stats file and store its contents """
    sFile = open(filename, 'r')
    curStat = None
    for line in sFile.readlines():
      if self.separator in line:
        if curStat != None:
          curStat.addStatLine(line)
        else:
          print 'Error: missing heading for line:', line
      else:
        heading = line.strip()+'\n'
        curStat = StatsItem(heading, separator=self.separator) 
        if heading not in self.contents:
          self.contents[heading] = curStat
        else:
          self.contents[heading].append(curStat)
    sFile.close()
    
  def write(self, out):
    nameList = self.contents.keys()
    nameList.sort()
#    nameList.reverse()
    for name in nameList:
      if self.contents[name].hasStats():
        self.contents[name].write(out, rowHeading=self.name) 
  
  def display(self):
    self.write(sys.stdout)       

class StatsFileList(list):
  separator=None
  
  def __init__(self, separator):
    self.separator = separator
    
  def readList(self, filelist):
    for filename in filelist:
      statsFile = StatsFile(filename, separator=self.separator) 
      self.append(statsFile)
      
  def write(self, out, displayIndividual=True, computeAverage=False):
    nameList = self[0].contents.keys()
    nameList.sort()
    for name in nameList:
      if name in self[0].contents and self[0].contents[name].hasStats():  
        longestName = ''
        for statFile in self:
          if len(statFile.name) > len(longestName):
            longestName = statFile.name
        out.write(' '.rjust(len(longestName)+2))
        out.write(name)
        if displayIndividual:
          for statsFile in self:
            if name in statsFile.contents:
              statsFile.contents[name].write(out, rowHeading=statsFile.name, displayHeading=False,\
                                            firstColumnWidth=len(longestName))
        if computeAverage:
          avgP = 0.0
          avgR = 0.0
          avgDP = 0.0      
          for statsFile in self:
            stats = statsFile.contents[name].stats[-1]
            avgP += stats.precision()
            avgR += stats.recall()
            avgDP += stats.precisionWithoutDuplicates()
          avgP /= len(self)
          avgR /= len(self)
          avgDP /= len(self)
          avgStat = AverageStat(r=avgR, p=avgP, dp=avgDP)
          avgString = 'average' + self.separator
          out.write(avgString.rjust(len(longestName)+2))
          avgStat.writerpf(out, separator=self.separator)

#      elif name not in self[0].contents:
#        print name, 'not in contents of', self[0].name
#      elif self[0].contents[name].hasStats() == False:
#        print self[0].name, 'has no valid stats of type =', name
            
  def display(self, displayIndividual=True, computeAverage=False):
    self.write(sys.stdout, displayIndividual, computeAverage) 
          
#########################################################################

if len(sys.argv) < 3:
  print "Usage: statsfile.py OPTIONS <STAT_FILES>"
  print "OPTIONS:"
  print " --display            Read list of files and display combined contents"
  print " --average            compute average"
  print " --output <FILENAME>  write results to given file"
  sys.exit()

filelist = []

displayMode = False
displayIndividual=False
computeAverage=False
outputFilename = None

i = 1
while i < len(sys.argv):
  if sys.argv[i] == '--display':
    displayIndividual = True
  elif sys.argv[i] == '--average':
    computeAverage=True 
  elif sys.argv[i] == '--output':
    outputFilename = sys.argv[i+1]
    i += 1
  else:
    filelist.append(sys.argv[i])
  i += 1

statsFileList = StatsFileList(separator='&')
statsFileList.readList(filelist)
statsFileList.display(True, computeAverage)

if outputFilename != None:
  out = open(outputFilename, 'w')
  statsFileList.write(out, displayIndividual, computeAverage)
  out.close() 
 
 
      