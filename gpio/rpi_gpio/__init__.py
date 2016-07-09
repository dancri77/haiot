from pydispatch import dispatcher
from main import thread_pool
from main.logger_helper import Log
from common import Constant

__author__ = 'Dan Cristian<dan.cristian@gmail.com>'

initialised = False
__pool_pin_codes = []

try:
    import RPi.GPIO as GPIO
    import_module_exist = True
except ImportError:
    Log.logger.info('Module RPI.GPIO is not installed, module will not be initialised')
    import_module_exist = False


# https://sourceforge.net/p/raspberry-gpio-python/wiki/Checking%20function%20of%20GPIO%20channels/
def __get_pin_function(bcm_id):
    res = GPIO.gpio_function(bcm_id)
    return res


# set gpio pin and return the actual pin state, LOW=0, HIGH=1
# https://sourceforge.net/p/raspberry-gpio-python/wiki/Outputs/
def set_pin_bcm(bcm_id=None, pin_value=None):
    Log.logger.info('Set rpi.gpio pin {} value {} function {}'.format(bcm_id, pin_value, __get_pin_function(bcm_id)))
    try:
        # if __get_pin_function(bcm_id) != GPIO.OUT:
        GPIO.setup(bcm_id, GPIO.OUT)
        if __get_pin_function(bcm_id) in {GPIO.OUT}:
            GPIO.output(bcm_id, pin_value)
            set_val = get_pin_bcm(bcm_id)
            if set_val != pin_value:
                Log.logger.critical('Rpi.gpio out value not OK, is {} but need {}'.format(bcm_id, set_val, pin_value))
            return set_val
        else:
            Log.logger.warning('Unable to setup rpi.gpio pin {} as OUT '.format(bcm_id))
    except Exception, ex:
        Log.logger.error("Error set_pin_bcm: {}".format(ex), exc_info=1)


def get_pin_bcm(bcm_id):
    try:
        res = GPIO.input(bcm_id)
    except RuntimeError, rex:
        Log.logger.warning('Error reading input rpi.gpio pin {} err={}. Setting as OUT and retry.'.format(bcm_id, rex))
        GPIO.setup(bcm_id, GPIO.OUT)
        # retry read
        res = GPIO.input(bcm_id)
    return res


#  https://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/,  LOW=0, HIGH=1
def event_detected(channel):
    try:
        global import_module_exist
        if import_module_exist:
            state = GPIO.input(channel)
            Log.logger.info('Event rpi.gpio input detected channel {} status {}'.format(channel, state))
            dispatcher.send(Constant.SIGNAL_GPIO, gpio_pin_code=channel, direction='in',
                            pin_value=state, pin_connected=(state == 0))
    except Exception, ex:
        Log.logger.warning('Error rpi.gpio event detected, err {}'.format(ex))


#  define all ports that are used as read/input, BCM format
#  https://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/
def setup_in_ports(gpio_pin_list):
    for gpio_pin in gpio_pin_list:
        if gpio_pin.pin_type == Constant.GPIO_PIN_TYPE_PI_STDGPIO:
            Log.logger.info('Set rpi.gpio pincode={} type={} index={} as input'.format(gpio_pin.pin_code,
                                                                                       gpio_pin.pin_type,
                                                                                       gpio_pin.pin_index_bcm))
            try:
                GPIO.setup(int(gpio_pin.pin_code), GPIO.IN, pull_up_down=GPIO.PUD_UP)  # PUD_DOWN:no contact detection
                GPIO.add_event_detect(int(gpio_pin.pin_code), GPIO.BOTH, callback=event_detected, bouncetime=500)
                __pool_pin_codes.append(gpio_pin.pin_code)
                Log.logger.info('OK callback on rpi.gpio'.format(gpio_pin.pin_code))
            except Exception, ex:
                Log.logger.warning('Unable to setup rpi.gpio callback pin={} err={}'.format(gpio_pin.pin_code, ex))


def thread_run():
    global initialised
    if initialised:
        Log.logger.debug('Processing RPI.GPIO')
        global import_module_exist
        if not import_module_exist:
            Log.logger.info('Simulating motion detection for test purposes')
            event_detected('P8_11')
        # else:
        #    __check_for_events()
        return 'Processed rpi.gpio'


def unload():
    GPIO.cleanup()
    thread_pool.remove_callable(thread_run)
    global initialised
    initialised = False


def init():
    Log.logger.info('RPI.GPIO module initialising')
    try:
        GPIO.setmode(GPIO.BCM)
        dispatcher.connect(setup_in_ports, signal=Constant.SIGNAL_GPIO_INPUT_PORT_LIST, sender=dispatcher.Any)
        thread_pool.add_interval_callable(thread_run, run_interval_second=10)
        global initialised
        initialised = True
    except Exception, ex:
        Log.logger.critical('Module rpi.gpio not initialised, err={}'.format(ex))
