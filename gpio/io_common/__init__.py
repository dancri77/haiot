from common import Constant
from main.admin import models
from main.logger_helper import L


# update in db (without propagatting the change by default)
def update_custom_relay(pin_code, pin_value, notify=False, ignore_missing=False):
    gpio = models.GpioPin.query.filter_by(pin_code=pin_code, host_name=Constant.HOST_NAME).first()
    if gpio is not None:
        gpio.pin_value = int(pin_value)
        gpio.notify_transport_enabled = notify
        gpio.commit_record_to_db()
    else:
        if not ignore_missing:
            L.l.warning('Unable to find gpio pin {}'.format(pin_code))
    relay = models.ZoneCustomRelay.query.filter_by(gpio_pin_code=pin_code, gpio_host_name=Constant.HOST_NAME).first()
    if relay is not None:
        relay.relay_is_on = pin_value
        relay.notify_transport_enabled = notify
        relay.commit_record_to_db()
        L.l.info('Updated relay {} val={}'.format(pin_code, pin_value))
    else:
        if not ignore_missing:
            L.l.warning('Unable to find relay pin {}'.format(pin_code))


class Port:
    _port_list = []
    type = None
    TYPE_GPIO = 'gpio'
    TYPE_PIFACE = 'piface'
    TYPE_PCF8574 = 'pcf8574'
    _types = frozenset([TYPE_GPIO, TYPE_PIFACE, TYPE_PCF8574])

    def __init__(self):
        pass


class OutputPort(Port):

    def __init__(self):
        pass


class InputPort(Port):

    def __init__(self):
        pass


class IOPort(InputPort, OutputPort):

    def __init__(self):
        pass