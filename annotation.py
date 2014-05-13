#!/usr/bin/python
# author: Rodney Summerscales
# define classes for an annotation

import xmlutil
import xml.dom
from xml.dom import minidom
from xml.dom.minidom import Document


##############################################################
# stores an annotation  
##############################################################
class Annotation:
  """ maintain information related to a token annotation or label assigned
      by a classifier """
  type = ''         # e.g. group, outcome number, etc
  attributes = {}   # e.g. id, role, etc
  
  def __init__(self, type=''):
    """ initialize a new annotation with default values 
        """
    self.attributes = {}
    self.type = type
    
  def parseXML(self, node=None):
    """ load information from an xml node """
    # parse xml element if given one
    if node != None:
       self.type = node.getAttribute('type').lower()      
       for childNode in node.childNodes:
         if childNode.nodeType == xml.dom.Node.ELEMENT_NODE:
           attribName = childNode.tagName
           value = xmlutil.getText(childNode)
           self.attributes[attribName] = value

  def copy(self, annotation):
    """ copy annotation information from a given annotation to this one """
    self.type = annotation.type
    for key, value in annotation.attributes.items():
      self.attributes[key] = value
      
  def getXML(self, doc, elementName):
    """ return an xml node that contains label information """
    node = doc.createElement(elementName)
    node.setAttribute('type',self.type)
    for attrib, value in self.attributes.items():
      node.appendChild(xmlutil.createNodeWithTextChild(doc, attrib, value))
    return node

  def getAttributeValue(self, attrib):
    """ return the value of the given attribute 
        or empty string if the annotation does not have such an attribute """
    return self.attributes.get(attrib, '')

  def setAttributeValue(self, attrib, value):
    """ set a given attribute value for this annotation 
        attrib = name of attribute
        value = value for the attribute
        """
    self.attributes[attrib] = value
        
##############################################################
# manage a list of annotations 
##############################################################
class AnnotationList:
  """ maintain a list of Annotation objects """
  __annotations = {}   # actually a hash of annotations, keyed by name
  __index = 0          # current index in list (used for iterator)
  __annotationList = []  # used in iterator
         
  def __init__(self, nodeList=[]):
    """ create new annoation list given a list of xml element nodes
        of type "annotation" """
    self.__annotations = {}
    self.__index = 0
    self.__annotationList = []
    # parse xml node if given one
    for aNode in nodeList:
      annotation = Annotation()
      annotation.parseXML(aNode)
      self.__annotations[annotation.type] = annotation 
     
  def contains(self, name):
    """ return true if an annotation with given name is in list """
    return name in self.__annotations
    
  def get(self, name):
    """ return a given annotation """
    if name in self.__annotations:
      return self.__annotations[name]
    else:
      return None
     
  def add(self, annotation):
    """ add a new annotation to the list. 
    
        annotation = Annotation object to add
        """
    self.__annotations[annotation.type] = annotation
      
  def remove(self, name):
    """ remove an annotation with a given name """
    if name in self.__annotations:
      del self.__annotations[name]
      if name in self.__annotations:
        print "ERROR: unable to remove", name
      
  def __contains__(self, name):
    """ implement the 'in' operator. return true if given name is in list
        of annotations. """
    if name in self.__annotations:
      return True
    else:
      return False
      
  def __len__(self):
    """ implement len() method """
    return len(self.__annotations)
  
  # routines needed for implementing the iterator      
  def __iter__(self):
    self.__index = 0
    self.__annotationList = self.__annotations.values()
    return self
    
  def next(self):
    if self.__index == len(self.__annotationList):
      raise StopIteration
    self.__index += 1
    return self.__annotationList[self.__index-1]
