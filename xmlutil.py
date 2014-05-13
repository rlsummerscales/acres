#!/usr/bin/env python
# author: Rodney Summerscales

"""
 various functions for working with xml elements
"""

import xml.dom
import sentence

def parseSentences(node, abstract=None):
  """ return a list of sentences elements constructed from an xml element
      that contain sentence elements """
  sList = []
  sNodes = node.getElementsByTagName('sentence')
  for i in range(0, len(sNodes)):
    s = sentence.Sentence()
    s.parseXML(sNodes[i], i, abstract)
    if len(s.tokens) > 3:
      sList.append(s)
  return sList

def createSentenceListNode(name, sentenceList, doc):
  """ given a list of sentences, create an xml node with the given name, with
      the given list of sentences """
  node = doc.createElement(name)
  for s in sentenceList:
    node.appendChild(s.getXML(doc))
  return node

def createNodeWithTextChild(doc, name, value):
  """ create simple xml node with text child """
  node = doc.createElement(name)
  tn = doc.createTextNode(value)
  node.appendChild(tn)
  return node

def nodeHasTagName(node, name):
  """ return true if a name has a given tag name """
  if node.nodeType == xml.dom.Node.ELEMENT_NODE:
    if node.tagName.lower() == name.lower():
      return True
  return False

def getNodeTagName(node):
  """ return the tag name for a given node 
     or empty string if it has no name (e.g. it is a text node) """
  if node.nodeType == xml.dom.Node.ELEMENT_NODE:
    return node.tagName.lower()
  return ''

def getText(node):
  """ return a string containing all of the text between the start and end tags
      of a given XML element. """
  s = ''
  for c in node.childNodes:
    if c.nodeType == xml.dom.Node.TEXT_NODE:
      s = s + c.data
  return s.strip()

def getTextFromNodeCalled(name, node):
  """ return the text for a child of a given node.
  
      name is the name of the node that we want the child text for
      node is the node which contains the child node
      """
  childNodes = node.getElementsByTagName(name)
  return getText(childNodes[0])

def normalizeText(text):
  """ return normalized string: 
      convert to lowercase, replace special chars with
      xml strings, replace characters created by stanford parser with 
      normal characters (e.g. replace '-lrb-' with '('. """
      
  if len(text) == 0:
    return text
    
#  text = text.lower()
  text = text.encode('ascii', 'xmlcharrefreplace')
#  text = text.replace('-lrb-', '(')
#  text = text.replace('-rrb-', ')')
  text = text.replace('\/', '/')
  return text
  
def normalizeXMLTree(rootNode):
  """ normalize all of the text children in the xml tree rooted at rootNode """
  for node in rootNode.childNodes:
    node.normalize()
    if node.nodeType == xml.dom.Node.TEXT_NODE:
      node.data = node.data.strip()
      if len(node.data) != 0:
        node.data = node.data.encode('ascii', 'xmlcharrefreplace') 
#    elif node.nodeType == xml.dom.Node.ELEMENT_NODE:
    normalizeXMLTree(node)
    
def fixed_writexml(self, writer, indent="", addindent="", newl=""):
    """ ndent = current indentation
      addindent = indentation to add to higher levels
      newl = newline string
      
     see http://ronrothman.com/public/leftbraned/
            xml-dom-minidom-toprettyxml-and-silly-whitespace/"""
    writer.write(indent+"<" + self.tagName)

    attrs = self._get_attributes()
    a_names = attrs.keys()
    a_names.sort()

    for a_name in a_names:
        writer.write(" %s=\"" % a_name)
        xml.dom.minidom._write_data(writer, attrs[a_name].value)
        writer.write("\"")
    if self.childNodes:
        if len(self.childNodes) == 1 \
          and self.childNodes[0].nodeType == xml.dom.minidom.Node.TEXT_NODE:
            writer.write(">")
            self.childNodes[0].writexml(writer, "", "", "")
            writer.write("</%s>%s" % (self.tagName, newl))
            return
        writer.write(">%s"%(newl))
        for node in self.childNodes:
            node.writexml(writer,indent+addindent,addindent,newl)
        writer.write("%s</%s>%s" % (indent,self.tagName,newl))
    else:
        writer.write("/>%s"%(newl))

def writexml(node, writer, indent='', addindent='  ', newl='\n'):
  xml.dom.minidom.Element.writexml = fixed_writexml
  node.writexml(writer, indent='', addindent='  ', newl='\n')
