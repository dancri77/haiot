'''
Created on Mar 9, 2015

@author: dcristian
'''
import pyownet.protocol
import time
import datetime
import socket
import threading
import logging
from pydispatch import dispatcher
import common.constant
import sys
from common import constant
from main.admin import model_helper
from main import db
from main.admin import models
from main.admin import event

def do_device (owproxy):
    sensors = owproxy.dir('/', slash=True, bus=False)
    for sensor in sensors:
        try:
            sensortype = owproxy.read(sensor+'type')
            if sensortype == 'DS2423':
                dev = get_counter(sensor, owproxy)
            elif sensortype == 'DS2413':
                dev=get_io(sensor, owproxy)
            elif sensortype == 'DS18B20':
                dev=get_temperature(sensor, owproxy)
            elif sensortype == 'DS2438':
                dev=get_temperature(sensor, owproxy)
                dev=get_voltage(sensor, owproxy)
                dev=get_humidity(sensor, owproxy)
            elif sensortype=='DS2401':
                dev=get_bus(sensor, owproxy)
            else:
                dev=get_unknown(sensor, owproxy)
            save_to_db(dev)
        except pyownet.protocol.ConnError:
            logging.warning('Connection error owserver')
    return 'Read {} sensors'.format(len(sensors))

def save_to_db(dev):
    sensor = models.Sensor()
    sensor.address = dev['address']
    sensor.type = dev['type']
    sensor.updated_on = datetime.datetime.now()
    if dev.has_key('counters_a'): sensor.counters_a = dev['counters_a']
    if dev.has_key('counters_b'): sensor.counters_b = dev['counters_b']
    if dev.has_key('temperature'): sensor.temperature = dev['temperature']
    if dev.has_key('humidity'): sensor.humidity = dev['humidity']
    if dev.has_key('iad'): sensor.iad = dev['iad']
    if dev.has_key('vad'): sensor.vad = dev['vad']
    if dev.has_key('vdd'): sensor.vdd = dev['vdd']
    if dev.has_key('pio_a'): sensor.pio_a = dev['pio_a']
    if dev.has_key('pio_b'): sensor.pio_b = dev['pio_b']
    if dev.has_key('sensed_a'): sensor.sensed_a = dev['sensed_a']
    if dev.has_key('sensed_b'): sensor.sensed_b = dev['sensed_b']
    db.session.add(sensor)
    db.session.commit
    #FIXME: Normally a db commit event should be triggered automatically, forcing the event below manually
    changes = []
    tuple = (sensor, 'update')
    changes.append(tuple)
    event.on_models_committed(sensor, changes)

def get_prefix(sensor, owproxy):
    dev = {}
    dev['address']=str(owproxy.read(sensor+'r_address'))
    dev['type']=str(owproxy.read(sensor+'type'))
    return dev

def get_bus( sensor , owproxy):
    dev = get_prefix(sensor, owproxy)
    return dev

def get_temperature( sensor , owproxy):
    dev = get_prefix(sensor, owproxy)
    dev['temperature'] = float(owproxy.read(sensor+'temperature'))
    return dev

def get_humidity( sensor , owproxy):
    dev = get_prefix(sensor, owproxy)
    dev['humidity'] = float(owproxy.read(sensor+'humidity'))
    return dev

def get_voltage(sensor, owproxy):
    dev = get_prefix(sensor, owproxy)
    dev['iad'] = float(owproxy.read(sensor+'IAD'))
    dev['vad'] = float(owproxy.read(sensor+'VAD'))
    dev['vdd'] = float(owproxy.read(sensor+'VDD'))
    return dev

def get_counter( sensor , owproxy):
    dev = get_prefix(sensor, owproxy)
    dev['counters_a'] = int(owproxy.read(sensor+'counters.A'))
    dev['counters_b'] = int(owproxy.read(sensor+'counters.B'))
    return dev

def get_io( sensor , owproxy):
    #IMPORTANT: do not use . in field names as it throws error on JSON, only use "_"
    dev = get_prefix(sensor, owproxy)
    dev['pio_a'] = str(owproxy.read(sensor+'PIO.A')).strip()
    dev['pio_b'] = str(owproxy.read(sensor+'PIO.B')).strip()
    dev['sensed_a'] = str(owproxy.read(sensor+'sensed.A')).strip()
    dev['sensed_b'] = str(owproxy.read(sensor+'sensed.B')).strip()
    return dev

def get_unknown (sensor, owproxy):
    dev = get_prefix(sensor, owproxy)
    return dev

owproxy=None
def init():
    logging.info('Initialising owssensor')
    global owproxy
    owproxy = pyownet.protocol.proxy(host=model_helper.get_param(constant.P_OWSERVER_HOST_1), port=4304)

def thread_run():
    logging.info('Processing sensors')
    return do_device(owproxy)


