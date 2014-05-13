#!/usr/bin/python
# author: Rodney Summerscales

import shutil
import os
import glob
import sys

if len(sys.argv) < 3:
  print "Usage: convertencoding.py <INPUT_PATH> <OUTPUT_PATH>"
  print "Convert enconding of given list of XML files to UTF-8"
  print "Write converted files to <OUTPUT_PATH>"
  sys.exit()

inputPath=sys.argv[1]
outputPath=sys.argv[2]
xslFile='bin/convertencoding.xsl'

filelist = glob.glob(inputPath+'*.xml')

for file in filelist:
  print file
  parts = file.split('/')
  filename = parts[-1]
  outputFile = outputPath+filename
  cmd = 'xsltproc ' + xslFile + ' ' + file + ' > ' + outputFile 
  os.system(cmd)
