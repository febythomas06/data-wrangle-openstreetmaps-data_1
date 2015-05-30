'''
mapclean class is responsible for reading the OSM map xml, auditing, cleaning, generating JSON and finally to insert the Modeled Data into DB.
Created on May 30, 2015

@author: Feby Thomas
'''
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint
import codecs
import json
from OSM.dbutil import get_db

#The source XML file from OSM
OSMFILE = "milwaukee_wisconsin.osm"

#Regular expression to find the ending of street names
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

#Array with expected and correct values for street name ending
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]

#Regular expressions to check the various tag 'k' sub elements
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

#Array to check and group the child for Created tag
CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

#Mapping for correcting the street names
mapping = { "St": "Street",
            "St.": "Street",
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Rd.": "Road",
            "Blvd": "Boulevard",
            "Cir": "Circle",
            "Ct": "Court",
            "Dr": "Drive",
            "Dr.": "Drive",
            "Ln": "Lane",
            "PL": "Place",
            "Pl.": "Place",
            "Pkwy": "Parkway",
            "Rd": "Road",
            "W": "West"            
            }


def update_name(name, mapping):
    """
    Function to correct the street name using regular expression and the mapping array above.
    """
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        for key in mapping:
            if key == street_type:
                name = street_type_re.sub(mapping[key],name)
                
    return name

def isright_street_type(street_types, street_name):
    """
    Function to check the street type are correct and if not it adds to a set a set dictionary and returns True or False
    """
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
            return False
        else:
            return True

def isright_state(state_set,state_name):
    """
    Function to check if the state name is consistent and correct, returns boolean
    """
    if len(state_name) > 2 and state_name != 'WI':
        state_set.add(state_name)
        return False
    else:
        return True
        
        
def audit_city(city_set,city_name):
        city_set.add(city_name)
                
def audit_postcode(postcode):
    """
    Function to check if the post code is consistent and correct, was used to audit only
    """
    if len(postcode) != 5 and len(postcode) != 10 or not postcode.startswith('53'):
        print(postcode)

def is_street_name(elem):
    """
    Function to if XML element attribute is for street
    """
    return (elem.attrib['k'] == "addr:street")


def is_postcode(elem):
    """
    Function to if XML element attribute is for postcode
    """
    return (elem.attrib['k'] == "addr:postcode")

def is_state(elem):
    """
    Function to if XML element attribute is for state
    """
    return (elem.attrib['k'] == "addr:state")

def is_city(elem):
    """
    Function to if XML element attribute is for city
    """
    return (elem.attrib['k'] == "addr:city")


def shape_element(element):
    """
    Function to shape a XML element into data structure as expected for final JSON.
    """
    node = {}
    if element.tag == "node" or element.tag == "way" :
        
        pos = []
        created = {}
        node['type'] = element.tag
        #Looping for all the attributes to be child of 'created' node. 
        for attr in element.attrib:
            if attr in CREATED:
                created[attr] = element.attrib[attr]
                node['created'] = created
            elif attr == 'lat':
                pos.insert(0,float(element.attrib[attr]))
            elif attr == 'lon':
                pos.insert(1,float(element.attrib[attr]))
            else:
                node[attr] = element.attrib[attr]
        node['pos'] = pos
        address = {}
        nd = []
        #Looping for sub elements and attributes of 'tag' elements
        for tag in element.iter("tag"):
            tagk = tag.attrib['k']
            if problemchars.search(tagk):
                pass
            m = lower_colon.match(tagk)
            if m:
                if tagk.startswith("addr:"):
                    address[tagk.split(':')[1]] = tag.attrib['v']
                elif ':' not in tagk:
                    #print(tagk)
                    node[tagk] = tag.attrib['v']
            else:
                node[tagk] = tag.attrib['v']
        if len(address) > 0:
            node['address'] = address
        #print node
        #handling for Node References in the XML
        for tag in element.iter("nd"):
            nd.append(tag.attrib['ref'])
        if len(nd) > 0:
            node['node_refs'] = nd
        return node
    else:
        return None

def auditncleannjson(osmfile,pretty = False):
    """
    Function to audit, clean and structure the XML to the JSON like data dictionary.
    """
    street_types = defaultdict(set)
    cntry = set()
    city = set()
    data = []
    #opening file for JSON output
    file_out = "{0}.json".format(osmfile)
    with codecs.open(file_out, "w") as fo:
        # Looping through the XML Element Tree
        for event, elem in ET.iterparse(osmfile, events=("start",)):
            #Initial audit related checks happen here
            if elem.tag == "node" or elem.tag == "way":
                for tag in elem.iter("tag"):
                    if is_street_name(tag):
                        if not isright_street_type(street_types, tag.attrib['v']):
                            tag.set('v',update_name(tag.attrib['v'], mapping))
                            #print(tag.attrib['v'])
                    if is_state(tag):
                        if not isright_state(cntry, tag.attrib['v']):
                            tag.set('v','WI')
                    #Optional postcode check was used only to audit
                    #if is_postcode(tag):
                    #    audit_postcode(tag.attrib['v'])
                    if is_city(tag):
                        audit_city(city,tag.attrib['v'])
            #Handling within a  single overall loop to shape the element into the  required dictionary data structure.
            el = shape_element(elem)
            if el:
                data.append(el)
                #Writing to the JSON file
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
        
    print('City Audit List: ')
    pprint.pprint(city)
    print('Street Audit List: ')
    pprint.pprint(dict(street_types))
    #print(data[0])
    #returning the full XML converted to Data Dictionary
    return data



def process_map(file_in, pretty = False):
    """
    Starts the audit and cleanup steps.
    """
    return auditncleannjson(file_in, pretty)
    
def insert_db(osmdata):
    """
    Inserts the data dictionary into the Mongo DB
    """
    db = get_db()
    db.osmdatamke.insert(osmdata)

  
def process(file_in):
    """
    Overall processing function, which first calls the cleanup and XML to JSON conversion and alter inserts teh data into the database.
    """
    osmdata = process_map(OSMFILE,True)
    print('Process Completed Before DB insert')
    insert_db(osmdata)
    print('DB Insert completed')

if __name__ == '__main__':
    process(OSMFILE)