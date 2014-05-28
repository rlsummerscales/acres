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

def HTMLBeginTable(out, lineWidth=0):
    """
     Begin a html table
    """
    out.write('<table>')

def HTMLEndTable(out):
    """
     Finish writing to table
    """
    out.write('</table>')

def HTMLBeginRow(out):
    """
    start a new row in the table (and begin a new column)
    """
    out.write('<tr style="vertical-align:top"><td>')

def HTMLColumnBreak(out):
    """
     End current column and begin a new one
    """
    out.write('</td><td>')

def HTMLEndRow(out):
    """
    Finish current row in table (and column)
    """
    out.write('</td></tr>')


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

    def writeFile(self, filename):
        """
        Write contents of HTML object to a given file
        :param filename: name of HTML file to create
        """
        out = self.HTMLOpenBasicFile(filename)
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
    def HTMLOpenBasicFile(filename):
        """
         Create a basic HTML file for writing. Write header information.
         Return reference to the filestream
        :param filename: Name for HTML file
        """
        out = open(filename, mode='w')
        out.write("<html><head>\n")
        out.write("<title>" + filename + "</title>\n")
        out.write("<style>body{font-family:Helvetica,Arial,sans-serif;}</style>\n")
        out.write("</head>\n")
        return out

    @staticmethod
    def HTMLClose(out):
        """
         Finish body of html file and close the file.
        :param out: Stream for writing to open HTML file
        """
        out.write('</body></html>\n')
        out.close()

