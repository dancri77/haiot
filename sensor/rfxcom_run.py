__author__ = 'Dan Cristian <dan.cristian@gmail.com>'

from main.logger_helper import L
from RFXtrx import PySerialTransport
import RFXtrx
from main.admin import models
from common import Constant, utils
import serial_common


class P:
    initialised = False
    transport = None
    last_packet_received = None
    MAX_MINUTES_SILENCE = 10


def __rfx_reading(packet):
    if packet:
        try:
            L.l.info("Received RFX packet={}".format(packet))
            if isinstance(packet, RFXtrx.SensorEvent):
                __save_sensor_db(p_id=packet.device.id_string, p_type=packet.device.type_string,
                                 value_list=packet.values)
                P.last_packet_received = utils.get_base_location_now_date()
            elif isinstance(packet, RFXtrx.LightingDevice):
                __save_relay_db(p_id=packet.device.id_string, p_type=packet.device.type_string,
                                value_list=packet.values)
        except Exception as ex:
            L.l.info('Unknown rfx packet type {} err={}'.format(packet, ex))


def __save_relay_db(p_id='', p_type='', value_list=None):
    # todo: add save to relay db
    pass


def __save_sensor_db(p_id='', p_type='', value_list=None):
    if not value_list:
        value_list = []
    record = models.Sensor(address=p_id)
    assert isinstance(record, models.Sensor)
    zone_sensor = models.ZoneSensor.query.filter_by(sensor_address=p_id).first()
    if zone_sensor:
        record.sensor_name = zone_sensor.sensor_name
    else:
        record.sensor_name = '(not defined) ' + p_id
    record.updated_on = utils.get_base_location_now_date()
    record.type = p_type
    if 'Humidity' in value_list:
        record.humidity = utils.round_sensor_value(value_list['Humidity'])
    if 'Temperature' in value_list:
        record.temperature = utils.round_sensor_value(value_list['Temperature'])
    if 'Battery numeric' in value_list:
        record.battery_level = value_list['Battery numeric']
    if 'Rssi numeric' in value_list:
        record.rssi = value_list['Rssi numeric']
    current_record = models.Sensor.query.filter_by(address=p_id).first()
    record.save_changed_fields(current_record=current_record, new_record=record, notify_transport_enabled=True,
                               save_to_graph=True, ignore_only_updated_on_change=True)


# ON COMMAND
#Packettype    = Lighting4
#subtype       = PT2262
#Sequence nbr  = 20
#Code          = 451451 decimal:4527185
#S1- S24  = 0100 0101 0001 0100 0101 0001
#Pulse         = 325 usec
#Signal level  = 6  -72dBm


# OFF COMMAND
# Code          = 451454 decimal:4527188

# CLOSE COMMAND
#Code          = 45155F decimal:4527455
#S1- S24  = 0100 0101 0001 0101 0101 1111

def elro_relay_on():
    pkt = None
    pkt.packettype = RFXtrx.lowlevel.Lighting4
    pkt.subtype = 'PT2262'
    pkt.cmd = 451451
    #pkt.type_string = 1
    #pkt.id_string = 1
    #event = RFXtrx.LightingDevice()


def unload():
    pass


# https://github.com/Danielhiversen/pyRFXtrx/
def init():
    P.initialised = False
    P.last_packet_received = utils.get_base_location_now_date()
    try:
        if Constant.OS in Constant.OS_LINUX:
            portpath = serial_common.get_portpath_linux('RFXtrx433')
        else:
            portpath = None
            # fixme windows autodetect version
        if portpath:
            L.l.info('Initialising RFXCOM on port {}'.format(portpath))
            P.transport = PySerialTransport(portpath, debug=True)
            P.transport.reset()
            P.initialised = True
        else:
            L.l.info('No RFX device detected on this system')
    except Exception as ex:
        L.l.warning('Unable to open RFX tty port, err {}'.format(ex))
    return P.initialised


def thread_run():
    try:
        L.l.debug('Waiting for RFX event')
        time_elapsed_minutes = (utils.get_base_location_now_date() - P.last_packet_received).seconds / 60
        if time_elapsed_minutes > P.MAX_MINUTES_SILENCE:
            L.l.warning('RFX event not received since {} minutes, device error?'.format(time_elapsed_minutes))
        if P.initialised:
            event = P.transport.receive_blocking()
            __rfx_reading(event)
    except Exception as ex:
        L.l.error('Error read RFX tty port, err={}'.format(ex), exc_info=True)
