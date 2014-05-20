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
        out.write(text)
    else:
        out.write(' <span style=\"color:' + color +'\">')

        if bold is True:
            out.write('<strong>')

        out.write(text)

        if bold is True:
            out.write('</strong>')

        out.write('</span> ')
