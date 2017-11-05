from main.logger_helper import Log
from main import thread_pool
from common import Constant
from pydispatch import dispatcher
from main.admin import models

__author__ = 'Dan Cristian<dan.cristian@gmail.com>'


initialised = False


# water utility
def __utility_update_ex(sensor_name, value):
    if value is not None:
        record = models.Utility(sensor_name=sensor_name)
        current_record = models.Utility.query.filter_by(sensor_name=sensor_name).first()
        if current_record is not None:
            record.utility_name = current_record.utility_name
            if current_record.utility_type == Constant.UTILITY_TYPE_WATER_LEVEL:
                record.units_total = value / (current_record.ticks_per_unit * 1.0)
                Log.logger.info("Saving utility water level value={} depth={}".format(value, record.units_total))
            if current_record.units_total is None:
                current_record.units_total = 0.0
            else:
                # force save
                if current_record is not None:
                    current_record.units_total = -1

            Log.logger.debug("Saving utility ex record {} name={}".format(current_record, record.utility_name))
            record.save_changed_fields(current_record=current_record, new_record=record, debug=False,
                                       notify_transport_enabled=True, save_to_graph=True, save_all_fields=True)
        else:
            Log.logger.critical("Utility ex sensor [{}] is not defined in Utility table".format(sensor_name))


def __utility_update(sensor_name, units_delta_a, units_delta_b, total_units_a, total_units_b, sampling_period_seconds):
    index = 0
    for delta in [units_delta_a, units_delta_b]:
        if delta is not None:
            record = models.Utility(sensor_name=sensor_name)
            current_record = models.Utility.query.filter_by(sensor_name=sensor_name, sensor_index=index).first()
            if current_record is not None:
                record.sensor_index = index
                record.utility_name = current_record.utility_name
                if current_record.utility_type == Constant.UTILITY_TYPE_ELECTRICITY:
                    # 1000 times count divided by 60 seconds time 60 minutes (kwh -> watt)
                    #record.units_delta = 1000 * delta / ((current_record.ticks_per_unit * 1.0) /
                    #                                     (sampling_period_seconds/(60.0*60)))
                    record.units_delta = delta / (current_record.ticks_per_unit * 1.0) # kwh
                    record.unit_name = current_record.unit_name  # Constant.UTILITY_TYPE_ELECTRICITY_MEASURE
                    record.units_2_delta = (1000 * record.units_delta) / (sampling_period_seconds / 3600.0)  # watts
                    Log.logger.info("Watts usage is {}".format(record.units_2_delta))
                    record.unit_2_name = current_record.unit_name_2
                elif current_record.utility_type == Constant.UTILITY_TYPE_WATER:
                        record.unit_name = current_record.unit_name  # Constant.UTILITY_TYPE_WATER_MEASURE
                        record.units_delta = delta / (current_record.ticks_per_unit * 1.0)
                        record.units_2_delta = 0
                        Log.logger.debug("Saving utility water delta={}".format(record.units_delta))
                elif current_record.utility_type == Constant.UTILITY_TYPE_GAS:
                    record.unit_name = current_record.unit_name  # Constant.UTILITY_TYPE_GAS_MEASURE
                    record.units_delta = delta / (current_record.ticks_per_unit * 1.0)
                    record.units_2_delta = 0
                    Log.logger.debug("Saving utility gas delta={}".format(record.units_delta))
                else:
                    Log.logger.info("Saving unknown utility type={} sensor={}".format(
                        current_record.utility_type, sensor_name))
                    if current_record.ticks_per_unit is not None:
                        record.units_delta = delta / (current_record.ticks_per_unit * 1.0)  # force float operation
                        record.units_2_delta = 0
                    else:
                        Log.logger.warning("Null ticks per unit")
                record.ticks_delta = delta
                if current_record.unit_cost is None:
                    current_record.unit_cost = 0.0
                record.cost = 1.0 * record.units_delta * current_record.unit_cost
                #todo: read previous value from history
                if current_record.units_total is None:
                    current_record.units_total = 0.0
                # force save for history recording, use negative values to enable recording 0
                if current_record is not None:
                    current_record.units_delta = -1
                    current_record.units_2_delta = -1
                    current_record.ticks_delta = -1
                    current_record.cost = -1
                    #current_record.utility_name = ""
                    current_record.sensor_index = -1
                record.units_total = 0.0 + current_record.units_total + record.units_delta
                Log.logger.debug("Saving utility record {} name={}".format(current_record, record.utility_name))
                record.save_changed_fields(current_record=current_record, new_record=record, debug=False,
                                           notify_transport_enabled=True, save_to_graph=True, save_all_fields=True)
            else:
                Log.logger.critical("Counter sensor [{}] index {} is not defined in Utility table".format(
                    sensor_name, index))
        index += 1


def unload():
    Log.logger.info('Utility module unloading')
    # ...
    # thread_pool.remove_callable(template_run.thread_run)
    global initialised
    initialised = False


def init():
    Log.logger.info('Utility module initialising')
    dispatcher.connect(__utility_update, signal=Constant.SIGNAL_UTILITY, sender=dispatcher.Any)
    dispatcher.connect(__utility_update_ex, signal=Constant.SIGNAL_UTILITY_EX, sender=dispatcher.Any)
    # thread_pool.add_interval_callable(template_run.thread_run, run_interval_second=60)
    global initialised
    initialised = True
