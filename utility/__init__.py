from main.logger_helper import L
from common import Constant, utils
from pydispatch import dispatcher
from main import sqlitedb
if sqlitedb:
    from storage.sqalc import model_helper, models
    from sqlalchemy import desc
from storage.model import m
__author__ = 'Dan Cristian<dan.cristian@gmail.com>'


initialised = False


# water & electricity utility from specialised sensors
def __utility_update_ex(sensor_name, value, unit=None, index=None):
    try:
        if value is not None:
            record = m.Utility()
            record.sensor_name = sensor_name
            if index is None:
                current_record = m.Utility.find_one({m.Utility.sensor_name: sensor_name})
            else:
                current_record = m.Utility.find_one({m.Utility.sensor_name: sensor_name,
                                                     m.Utility.sensor_index: index})
            if current_record is not None:
                if current_record.units_total is None:
                    # need to get
                    if sqlitedb:
                        last_rec = models.UtilityHistory.query.filter_by(
                            utility_name=record.utility_name).order_by(desc(models.UtilityHistory.id)).first()
                    else:
                        # fixme
                        last_rec = None
                    if last_rec is not None:
                        current_record.units_total = last_rec.units_total
                    else:
                        current_record.units_total = 0.0
                # else: - should not be needed
                #    # force save
                #    if current_record is not None:
                #        current_record.units_total = -1
                record.utility_name = current_record.utility_name
                if current_record.utility_type == Constant.UTILITY_TYPE_WATER:
                    new_value = value / (current_record.ticks_per_unit * 1.0)
                    delta = max(0, new_value - current_record.units_total)
                    record.units_total = new_value
                    record.units_delta = delta
                    # record.units_2_delta = 0.0
                elif current_record.utility_type == Constant.UTILITY_TYPE_WATER_LEVEL:
                    record.units_total = value / (current_record.ticks_per_unit * 1.0)
                    L.l.info("Saving utility water level value={} depth={}".format(value, record.units_total))
                elif current_record.utility_type == Constant.UTILITY_TYPE_ELECTRICITY:
                    if unit == current_record.unit_2_name:
                        record.units_2_delta = value
                        # record.units_delta = 0.0  # needed for comparison
                    elif unit == current_record.unit_name:
                        record.units_total = value
                        record.units_delta = value - current_record.units_total
                        current_record.units_total = value
                elif current_record.utility_type == Constant.UTILITY_TYPE_GAS:
                    new_value = value / (current_record.ticks_per_unit * 1.0)
                    delta = max(0, new_value - current_record.units_total)
                    record.units_total = new_value
                    record.units_delta = delta
                    # record.units_2_delta = 0.0
                else:
                    L.l.warning("Unkown utility type not processed from sensor {}".format(sensor_name))
                # L.l.debug("Saving utility ex record {} name={}".format(current_record, record.utility_name))
                # if sensor_name == 'sonoff-basic-2':
                #    is_debug = True
                # else:
                #    is_debug = False
                record.save_changed_fields(broadcast=True, persist=True)
            else:
                L.l.info("Utility ex sensor {} index {} not defined in Utility table".format(sensor_name, index))
    except Exception as ex:
        L.l.error("Error saving utility ex update {}".format(ex), exc_info=True)
        if sqlitedb:
            if "Bind '" + Constant.DB_REPORTING_ID + "' is not specified" in str(ex):
                L.l.info('Try to connect to reporting DB, connection seems down')
                model_helper.init_reporting()


def __utility_update(sensor_name, units_delta_a, units_delta_b, total_units_a, total_units_b, sampling_period_seconds):
    try:
        index = 0
        is_debug = False
        ignore_save = False
        for delta in [units_delta_a, units_delta_b]:
            if delta is not None: # and delta != 0:
                record = m.Utility.find_one({m.Utility.sensor_name: sensor_name,  m.Utility.sensor_index: index})
                if record is not None:
                    record.sensor_index = index
                    if record.utility_type == Constant.UTILITY_TYPE_ELECTRICITY:
                        record.units_delta = delta / (record.ticks_per_unit * 1.0)  # kwh
                        record.units_2_delta = (1000 * record.units_delta) / (sampling_period_seconds / 3600.0)  # watts
                        L.l.debug("Watts usage in {} is {}".format(record.utility_name, record.units_2_delta))
                    elif record.utility_type == Constant.UTILITY_TYPE_WATER:
                        record.units_delta = delta / (record.ticks_per_unit * 1.0)
                        record.units_2_delta = 0.0  # to match comparison in field changed
                        L.l.debug("Saving utility water delta={}".format(record.units_delta))
                    elif record.utility_type == Constant.UTILITY_TYPE_GAS:
                        record.units_delta = delta / (record.ticks_per_unit * 1.0)
                        record.units_2_delta = 0.0  # to match comparison in field changed
                        L.l.debug("Saving utility gas delta={}".format(record.units_delta))
                    else:
                        L.l.debug("Saving unknown utility type={} sensor={}".format(
                            record.utility_type, sensor_name))
                        if record.ticks_per_unit is not None:
                            record.units_delta = delta / (record.ticks_per_unit * 1.0)  # force float operation
                            record.units_2_delta = 0.0
                        else:
                            L.l.warning("Null ticks per unit")
                    record.ticks_delta = delta
                    if record.unit_cost is None:
                        record.unit_cost = 0.0
                    record.cost = 1.0 * record.units_delta * record.unit_cost
                    # todo: read previous value from history
                    if record.units_total is None:
                        # get val from history db
                        # fixme:
                        last_rec = None
                        if last_rec is not None:
                            record.units_total = last_rec.units_total
                        else:
                            L.l.warning("Could not find last history record for {}".format(record.utility_name))
                            record.units_total = 0.0
                    record.units_total = 0.0 + record.units_total + record.units_delta
                    L.l.debug("Saving utility record {} name={}".format(record, record.utility_name))
                    record.save_changed_fields(broadcast=True, persist=True)
                else:
                    L.l.critical("Counter sensor [{}] index {} is not defined in Utility table".format(
                        sensor_name, index))
            index += 1
    except Exception as ex:
        L.l.error("Error saving utility update {}".format(ex), exc_info=True)


def unload():
    L.l.info('Utility module unloading')
    # ...
    # thread_pool.remove_callable(template_run.thread_run)
    global initialised
    initialised = False


def init():
    L.l.debug('Utility module initialising')
    dispatcher.connect(__utility_update, signal=Constant.SIGNAL_UTILITY, sender=dispatcher.Any)
    dispatcher.connect(__utility_update_ex, signal=Constant.SIGNAL_UTILITY_EX, sender=dispatcher.Any)
    global initialised
    initialised = True
