__author__ = 'dcristian'
import sys
import os
import json
import re
import datetime
from main import logger
import math

from collections import namedtuple

#http://stackoverflow.com/questions/6578986/how-to-convert-json-data-into-a-python-object
def _json_object_hook(d):
    return namedtuple('X', d.keys())(*d.values())
def date_deserialiser(json):
    if re.search("....-..-..T..:..:..\.......", json):
        return datetime.datetime.strptime(json, "%Y-%m-%d %H:%M:%S.%f")
    else:
        return json
def date_serialised(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj
def json2obj(data):
    #return json.loads(data, object_pairs_hook=date_deserialiser)
    return json.loads(data)

#this function takes objects that can be safely serialised
def safeobj2json(obj):
    return json.dumps(obj, default=date_serialised)
def unsafeobj2json(obj):
    safe_obj = {}
    for attr in dir(obj):
        if not attr.startswith('_') and not '(' in attr \
                and attr != 'query' and not callable(getattr(obj, attr))\
                and attr != 'metadata':
            value=getattr(obj, attr)
            #only convert to json simple primitives
            if value is not None and not hasattr(value,'_sa_class_manager'):
                safe_obj[attr] = value
    return safeobj2json(safe_obj)

def get_object_name(obj):
    str(obj._sa_class_manager.itervalues().next()).split('.')[0]
def get_object_field_value(obj={}, field_name=None):
    #field_name = str(field_obj).split('.')[1]
    if obj.has_key(field_name):
        return obj[field_name]
    else:
        return None

#
def get_model_field_name(field_obj):
    val = str(property(field_obj).fget)
    words=val.split('.')
    if len(words) >1:
        return words[1]
    else:
        logger.critical('Unexpected words count in get_model_field_name={}'.format(field_obj))
        return None

def parse_to_date(strdate):
    if  re.search("....-..-..T..:..:..\.......",  strdate) or \
        re.search("....-..-.. ..:..:..\.......",  strdate):
        strdate= strdate.replace('T',' ')
        strdate = datetime.datetime.strptime(strdate, "%Y-%m-%d %H:%M:%S.%f")
    else:
        logger.warning('Warning, unexpected date format in parse []'.format(strdate))
    return strdate

def get_table_name(model_obj):
    parts = str(model_obj).split('.')
    table = parts[len(parts)-1].split('\'')
    return table[0]

def round_sensor_value(val):
    return math.ceil(float(val)*10)/10