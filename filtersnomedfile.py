#!/usr/bin/python
# author: Rodney Summerscales
# prepare the file containing the conversion table between UMLS concept id
# and SNOMED CT codes. Ignore retired codes.

mrconsoFile = open('MRCONSO.RRF', 'r')
snomedFile = open('snomedfile.rrf', 'w')
discardedFile = open('snomed.discarded', 'w')

for line in mrconsoFile.readlines():
  if line.find('-RETIRED-') > -1:
    discardedFile.write(line)
  elif line.find('[D]') > -1:
    discardedFile.write(line)
  else:
    snomedFile.write(line)
    
snomedFile.close()
discardedFile.close()

