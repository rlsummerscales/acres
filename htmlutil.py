#!/usr/bin/env python 

"""
 This module contains functions for writing text/elements to an html file
"""

__author__ = 'Rodney L. Summerscales'


def HTMLWriteText(out, text, color='black', bold=False):
    """
     Write text to html file
    :param out: Output stream for HTML file
    :param text: Text string to write to file
    :param color: HTML color for displaying text
    :param bold:  If True, make text bold
    """
    if out is None:
        return

    if color == 'black':
        if bold is False:
            out.write(text)
        else:
            out.write('<strong>%s</strong>' % text)
    else:
        out.write(' <span style=\"color:' + color + '\">')

        if bold is True:
            out.write('<strong>')

        out.write(text)

        if bold is True:
            out.write('</strong>')

        out.write('</span> ')

def HTMLCreateSummaryFile(filename):
    """
     Open HTML file for writing and setup the CSS styles for the summary format
     Begin the body.
    """
    out = open(filename, mode='w')
    out.write("<!DOCTYPE html>\n<html>\n<head>\n")
    out.write("<title>" + filename + "</title>\n")
    out.write("<style>body{font-family:Helvetica,Arial,sans-serif;}</style>\n")
    HTMLSetBorderStyles(out)
    HTMLSetTableStyle(out, 'publicationinfotable', cellpadding='5px', borderOn=False)
    HTMLSetTableStyle(out, 'abstractsummarytable', cellpadding='20px', borderOn=False)
    out.write("</head><body>\n")
    return out


def HTMLSetTableStyle(out, stylename, width='100%', cellpadding='10px', borderOn=False, valign='top'):
    """
    Set default table settings. Must be called before the head portion of html file is finished.
    """
    out.write('<style type="text/css">\n table.%s{ width:%s; border-collapse:collapse; } \n'
              % (stylename, width))
    if borderOn:
        borderString = 'border:1px solid black;'
    else:
        borderString = ''
    out.write('table.%s th, table.%s td\n{ padding:%s; %s vertical-align:%s }\n'
              % (stylename, stylename, cellpadding, borderString, valign))
    out.write('</style>\n')

def HTMLSetBorderStyles(out):
    """
        Create border-top, border-bottom, border-left, border-right styles.
        These are used for adding borders to tables
    """
    out.write('<style> .border-top { border-top: 1px solid #000; }')
    out.write(' .border-bottom { border-bottom: 1px solid #000; }')
    out.write(' .border-left { border-left: 1px solid #000; }')
    out.write(' .border-right { border-right: 1px solid #000; }')
    out.write('</style>')

def HTMLBeginTable(out, classStyle=''):
    """
     Begin a html table
    """
    if classStyle is not '':
        classString = 'class="%s"' % classStyle
    else:
        classString = ''
    out.write('<table %s>\n' % classString)

def HTMLEndTable(out):
    """
     Finish writing to table
    """
    out.write('</table>\n')

def HTMLBeginRow(out, firstColumnWidth='', firstColumnBordersOn=False):
    """
    start a new row in the table (and begin a new column)
    """
    out.write('<tr>')
    HTMLBeginColumn(out, width=firstColumnWidth, bordersOn=firstColumnBordersOn)

def HTMLBeginColumn(out, width='', bordersOn=False):
    """
     Explicitly begin a new column. Not necessary if using HTMLBeginRow or HTMLColumnBreak
     With = % width (e.g. '50%') or width in pixels (e.g. '50')
    """
    if width is not '':
        widthAttribute = 'style="width:%s"' % width
    else:
        widthAttribute = ''

    if bordersOn:
        borderAttribute = 'class="border-top border-bottom border-left border-right"'
    else:
        borderAttribute = ''
    out.write('<td %s %s>' % (widthAttribute, borderAttribute))

def HTMLColumnBreak(out, width='', nextColumnBordersOn=False):
    """
     End current column and begin a new one
    """
    out.write('</td>')
    HTMLBeginColumn(out, width, bordersOn=nextColumnBordersOn)

def HTMLEndRow(out):
    """
    Finish current row in table (and column)
    """
    out.write('</td></tr>\n')


class HTMLFile:
    """
    Create a basic HTML file for writing
    """
    title = None
    bodyElementList = None

    def __init__(self, title):
        """
         Initialize a basic HTML file object
        """
        self.title = title
        self.bodyElementList = []

    def addBodyElement(self, bodyElement):
        """
         Add a new body element to the html file
        """
        self.bodyElementList.append(bodyElement)

    def writeFile(self, filename, useSummaryFormat=False):
        """
        Write contents of HTML object to a given file
        :param filename: name of HTML file to create
        """
        out = self.HTMLOpenBasicFile(filename, useSummaryFormat=useSummaryFormat)
        for bodyElement in self.bodyElementList:
            out.write(bodyElement)
        self.HTMLClose(out)

    def HTMLCreateFileWithBodyText(self, filename, bodyText):
        """
           Create a basic HTML file with the given text string in the body of the file
        """
        out = self.HTMLOpenBasicFile(filename)
        out.write(bodyText)
        self.HTMLClose(out)

    @staticmethod
    def HTMLOpenBasicFile(filename, useSummaryFormat=False):
        """
         Create a basic HTML file for writing. Write header information.
         Return reference to the filestream
        :param filename: Name for HTML file
        """
        if useSummaryFormat is True:
            out = HTMLCreateSummaryFile(filename)
        else:
            out = open(filename, mode='w')
            out.write("<html><head>\n")
            out.write("<title>" + filename + "</title>\n")
            out.write("<style>body{font-family:Helvetica,Arial,sans-serif;}</style>\n")
            out.write("</head><body>\n")
        return out

    @staticmethod
    def HTMLClose(out):
        """
         Finish body of html file and close the file.
        :param out: Stream for writing to open HTML file
        """
        out.write('</body></html>\n')
        out.close()

