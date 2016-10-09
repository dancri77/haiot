from main.logger_helper import Log
from pydispatch import dispatcher
from main import thread_pool
from main.admin import models
from common import Constant, utils
import presence_run

__author__ = 'Dan Cristian<dan.cristian@gmail.com>'
initialised = False


def handle_event_presence(gpio_pin_code='', direction='', pin_value='', pin_connected=None):
    Log.logger.info('Presence got event pin {}'.format(gpio_pin_code))
    zonealarm = models.ZoneAlarm().query_filter_first(
        models.ZoneAlarm.gpio_host_name.in_([Constant.HOST_NAME]), models.ZoneAlarm.gpio_pin_code.in_([gpio_pin_code]))
    zone_id = None
    # fixme: for now zonealarm holds gpio to zone mapping, should be made more generic
    if zonealarm is not None:
        zone_id = zonealarm.zone_id
    if zone_id is not None:
        current_record = models.Presence().query_filter_first(models.Presence.zone_id == zone_id)
        record = models.Presence(zone_id=zone_id)
        record.event_io_date = utils.get_base_location_now_date()
        record.sensor_name = zonealarm.alarm_pin_name
        record.save_changed_fields(current_record=current_record, new_record=record, notify_transport_enabled=True,
                                   save_to_graph=True)
    else:
        Log.logger.warning('Unable to find zone for pin {}'.format(gpio_pin_code))


def unload():
    Log.logger.info('Presence module unloading')
    # ...
    thread_pool.remove_callable(presence_run.thread_run)
    global initialised
    initialised = False


def init():
    Log.logger.info('Presence module initialising')
    thread_pool.add_interval_callable(presence_run.thread_run, run_interval_second=60)
    dispatcher.connect(handle_event_presence, signal=Constant.SIGNAL_GPIO, sender=dispatcher.Any)
    handle_event_presence(gpio_pin_code='66')
    global initialised
    initialised = True


if __name__ == '__main__':
    presence_run.thread_run()
