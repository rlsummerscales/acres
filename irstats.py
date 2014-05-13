# compute recall, precision, fscore
# author: Rodney Summerscales

import sys

# class for keeping track of true positives, false positives, false negatives,
# and computing RPF stats
class IRstats:
  tp = 0        # true positives
  fp = 0        # false positives
  fn = 0        # false negatives
  duplicates = 0
  
  def __init__(self, tp=0, fp=0, fn=0, duplicates=0):
    self.tp = tp
    self.fp = fp
    self.fn = fn
    self.duplicates = duplicates
    
  def incTP(self):
    self.tp += 1

  def incFP(self):
    self.fp += 1

  def incFN(self):
    self.fn += 1

  def incDuplicates(self):
    self.duplicates += 1
    
  def addStats(self, irstats):
    """ add TP, FP, FN from existing IRstats object """
    self.addTP(irstats.tp)
    self.addFP(irstats.fp)
    self.addFN(irstats.fn)
    self.addDuplicates(irstats.duplicates)
    
  def addTP(self, tp):
    self.tp += tp

  def addFP(self, fp):
    self.fp += fp

  def addFN(self, fn):
    self.fn += fn
  
  def addDuplicates(self, duplicates):
    self.duplicates += duplicates
      
  def clear(self):
    """ reset all counters (TP, FP, FN) """
    self.tp = 0
    self.fp = 0
    self.fn = 0
    self.duplicates = 0
      
  def recall(self):
    """ compute recall. TP/(TP+FN)
        returns: recall value
    """  
    if self.tp == 0:
      return 0.0
    return float(self.tp) / (self.tp + self.fn)

  def precision(self):
    """ compute precision. TP/(TP+FP)
        returns: precision value
        counts duplicates as false positives
    """
    if self.tp == 0:
      return 0.0
    return float(self.tp) / (self.tp + self.fp + self.duplicates)
  
  def precisionWithoutDuplicates(self):
    """ compute precision. TP/(TP+FP)
        returns: precision value
        Ignores duplicates
    """
    if self.tp == 0:
      return 0.0
    return float(self.tp) / (self.tp + self.fp)
    

  def smoothedRecall(self):
    """ compute recall smoothed using Laplace estimate. (TP+0.5)/(TP+FN+1). 
        returns: recall value
    """  
    if self.tp == 0:
      return 0.0
    return float(self.tp+0.5) / (self.tp + self.fn+1)

  def smoothedPrecision(self):
    """ compute precision smoothed using Laplace estimate. (TP+0.5)/(TP+FP+1)
        returns: smoothed precision value
    """
    if self.tp == 0:
      return 0.0
    return (self.tp+0.5) / (self.tp + self.fp + self.duplicates+1)

  def fscore(self):
    """ compute F1-score. 2(RP)/(R+P)
        returns: f1-score value
    """ 
    r = self.recall()
    p = self.precision()
    if (r + p) == 0:
      return 0.0
    return 2 * (r * p) / (r + p)

  def smoothedFscore(self):
    """ compute F1-score. 2(RP)/(R+P)
        returns: f1-score value
    """ 
    r = self.smoothedRecall()
    p = self.smoothedPrecision()
    if (r + p) == 0:
      return 0.0
    return 2 * (r * p) / (r + p)

  def percentDuplicates(self):
    """ percentage of detected items that were counted as duplicate """
    n = self.duplicates + self.tp + self.fp
    if n == 0:
      return 0.0
    return float(self.duplicates)/(n)
    
  def displayrpf(self):
    """ output stats to std out """
    self.writerpf(sys.stdout)

  def writerpf(self, out, separator='  '):
    """ Output stats to txt file 
      parms:  out = output stream object
              separator = string used to separate numbers in output stream
    """
    r = self.recall()
    p = self.precision()
    f = self.fscore()
    out.write('%4d%s%4d%s%4d'%(self.tp,separator,self.fp,separator,self.fn))
    out.write('%s%.2f' % (separator, r))
    out.write('%s%.2f' % (separator, p))
    out.write('%s%.2f' % (separator, f))
    if self.duplicates > 0:
      # compute stats ignoring duplicates
      percentDup = self.percentDuplicates()
      out.write('%s%4d%s%.2f'% (separator, self.duplicates, separator, percentDup))
      percentNonDup = 1 - percentDup
      if percentNonDup == 0:
        pWithoutDup = 0.0
      else:
        pWithoutDup = p / percentNonDup
      out.write('%s%.2f'% (separator, pWithoutDup))
    out.write('\n')


