from pydispatch import dispatcher
import threading
import prctl
from main.logger_helper import L
from main import thread_pool, persistence, db
from common import Constant, variable, utils
import transport
import models
import main
import model_helper
import node
import sensor
import heat
import gpio
import utility
import health_monitor
#import rule
import presence
import main.persistence


class P:
    mqtt_event_list = []
    mqtt_lock = threading.Lock()

    def __init__(self):
        pass


# executed on local db changes done via web ui only, including API calls
def handle_local_event_db_post(model, row, last_commit_field_changed_list=None):
    processed = False
    L.l.debug('Local DB change sent by model {} row {}'.format(model, row))
    if str(models.Parameter) in str(model):
        # fixme: update app if params are changing to avoid need for restart
        processed = True
    # no need to propagate changes to other nodes
    elif str(models.Module) in str(model):
        if row.host_name == Constant.HOST_NAME:
            main.init_module(row.name, row.active)
            processed = True

    # propagate changes to all nodes as each must execute db sync or other commands locally
    # add here tables you are sure are safe to be propagated to all nodes
    elif str(models.Node) in str(model) or str(models.GpioPin) in str(model) \
            or str(models.ZoneCustomRelay) in str(model) \
            or str(models.Rule) in str(model) \
            or str(models.ZoneThermostat) in str(model)\
            or str(models.Pwm) in str(model):
            # or str(models.Area) in str(model) :
        txt = model_helper.model_row_to_json(row, operation='update')
        # execute all events directly first, then broadcast, as local events are not handled by remote mqtt queue
        obj_json = utils.json2obj(txt)
        obj_json[Constant.JSON_PUBLISH_FIELDS_CHANGED] = last_commit_field_changed_list
        # handle_event_mqtt_received(None, None, 'direct-event', obj_json)
        #_handle_internal_event(obj_json)
        _process_obj(obj_json)
        # mqtt_thread_run()
        transport.send_message_json(json=txt)
        processed = True

    # if processed:
    #    L.l.debug('Detected {} record change, row={}, trigger executed'.format(model, row))
    # else:
    #    L.l.debug('Detected {} record change, row={}, but change processing ignored'.format(model, row))


def _handle_internal_event(obj):
    obj['is_event_external'] = False
    P.mqtt_event_list.append(obj)


# executed on every mqqt message received (except those sent by this host)
def handle_event_mqtt_received(obj):
    # global __mqtt_lock
    # __mqtt_lock.acquire()
    try:
        P.mqtt_event_list.append(obj)
    finally:
        # __mqtt_lock.release()
        pass


def before_models_committed(sender, changes):
    on_models_committed(sender, changes)


# executed on all db commits. commits generated by UI/API are handled above.
def on_models_committed(sender, changes):
    try:
        for obj, change in changes:
            # avoid recursion
            if isinstance(obj, models.Pwm):
                L.l.info("Commit change PWM={}".format(obj))
            if hasattr(obj, Constant.JSON_PUBLISH_NOTIFY_TRANSPORT):
                # only send mqtt message once for db saves intended to be distributed
                if obj.notify_transport_enabled:
                    if hasattr(obj, Constant.JSON_PUBLISH_NOTIFY_DB_COMMIT):
                        if not obj.notified_on_db_commit:
                            obj.notified_on_db_commit = True
                            txt = model_helper.model_row_to_json(obj, operation=change)
                            if txt is None:
                                txt = model_helper.model_row_to_json(obj, operation=change)
                                pass
                            # execute all events directly first,
                            # then broadcast, local events not handled by remote mqtt queue
                            _handle_internal_event(utils.json2obj(txt))
                            # _process_obj(utils.json2obj(txt))
                            transport.send_message_json(json=txt)
                else:
                    pass
            # send object to rule parser, if connected
            dispatcher.send(Constant.SIGNAL_DB_CHANGE_FOR_RULES, obj=obj, change=change)
    except Exception as ex:
        L.l.exception('Error in DB commit hook, {}'.format(ex))


# runs periodically and executes received mqqt messages from queue
def _process_obj(obj):
    try:
        prctl.set_name("event_thread_run")
        threading.current_thread().name = "event_thread_run"
        # events received via mqtt transport
        # fixme: make it generic to work with any transport
        source_host = obj[Constant.JSON_PUBLISH_SOURCE_HOST]
        if Constant.JSON_PUBLISH_TABLE in obj:
            table = str(obj[Constant.JSON_PUBLISH_TABLE])
            if table == utils.get_table_name(models.Node):
                node.node_run.node_update(obj)
                # fixme: remove hardcoded strings
                if 'execute_command' in obj:
                    execute_command = obj['execute_command']
                    host_name = obj['name']
                    # execute command on target host or on current host
                    # (usefull when target is down - e.g. wake cmd
                    if (host_name == Constant.HOST_NAME or source_host == Constant.HOST_NAME) \
                            and execute_command != '':
                        server_node = models.Node.query.filter_by(name=host_name).first()
                        main.execute_command(execute_command, node=server_node)
            elif table == utils.get_table_name(models.ZoneHeatRelay):
                # if heat.initialised:
                heat.record_update(obj)
            elif table == utils.get_table_name(models.Sensor):
                # sensor.not_used_record_update(obj)
                pass
            elif table == utils.get_table_name(models.DustSensor):
                pass
            elif table == utils.get_table_name(models.ZoneCustomRelay):
                gpio.zone_custom_relay_record_update(obj)
            elif table == utils.get_table_name(models.GpioPin):
                gpio.not_used_gpio_record_update(obj)
            # elif table == utils.get_table_name(models.Rule):
            #    rule.record_update(obj)
            elif table == utils.get_table_name(models.Presence):
                presence.not_used_record_update(obj)
            # elif table == utils.get_table_name(models.PlotlyCache):
            #    graph_plotly.record_update(obj)
            elif table == utils.get_table_name(models.ZoneAlarm):
                # no processing (no local save)
                pass
            elif table == utils.get_table_name(models.Utility):
                utility.not_used_record_update(obj, source_host)
            elif table == utils.get_table_name(models.Ups):
                # no additional processing
                pass
            elif table == utils.get_table_name(models.SystemDisk):
                # no additional processing
                pass
            elif table == utils.get_table_name(models.Music):
                # no additional processing
                pass
            elif table == utils.get_table_name(models.MusicLoved):
                # no additional processing
                pass
            elif table == utils.get_table_name(models.PowerMonitor):
                health_monitor.not_used_powermonitor_record_update(obj)
            elif table == utils.get_table_name(models.ZoneThermostat):
                heat.zone_thermo_record_update(obj)
            elif table == utils.get_table_name(models.Pwm):
                gpio.pigpio_gpio.not_used_pwm_record_update(obj)
            else:
                L.l.warning('Table %s content from %s is not mqtt processed' % (table, source_host))

        if Constant.JSON_MESSAGE_TYPE in obj:
            if variable.NODE_THIS_IS_MASTER_LOGGING:
                if source_host != Constant.HOST_NAME:
                    levelname = obj['level']
                    msg = obj['message']
                    msgdatetime = obj['datetime']
                    message = '{}, {}, {}'.format(source_host, msgdatetime, msg)
                    if levelname == 'INFO':
                        L.remote_logger.info(message)
                    elif levelname == 'WARNING':
                        L.remote_logger.warning(message)
                    elif levelname == 'CRITICAL':
                        L.remote_logger.critical(message)
                    elif levelname == 'ERROR':
                        L.remote_logger.error(message)
                    elif levelname == 'DEBUG':
                        L.remote_logger.debug(message)
                # else:
                    # Log.logger.warning('This node is master logging but emits remote logs, is a circular reference')

        # if record has fields that enables persistence (in cloud or local)
        # if variable.NODE_THIS_IS_MASTER_OVERALL:
        if source_host == Constant.HOST_NAME:
            if Constant.JSON_PUBLISH_SAVE_TO_HISTORY in obj:
                # if record must be saved to local db
                if obj[Constant.JSON_PUBLISH_SAVE_TO_HISTORY] and Constant.HAS_LOCAL_DB_REPORTING_CAPABILITY:
                    persistence.save_to_history_db(obj)
                else:
                    # L.l.info("Not saving to db, json publish={} has db={}, obj={}".format(
                    #    obj[Constant.JSON_PUBLISH_SAVE_TO_HISTORY], Constant.HAS_LOCAL_DB_REPORTING_CAPABILITY,
                    #    obj))
                    pass
            else:
                L.l.info("Received mqtt object without history save tag: {}".format(obj))
        # else:
        #    L.l.info("Dropping message from {}, not matching {}".format(source_host, Constant.HOST_NAME))
    except Exception as ex:
        L.l.error("Error processing event err={}, mqtt={}".format(ex, obj), exc_info=True)


def mqtt_thread_run():
    P.mqtt_lock.acquire()
    # from cloud import graph_plotly
    try:
        last_count = len(P.mqtt_event_list)
        for obj in list(P.mqtt_event_list):
            P.mqtt_event_list.remove(obj)
            _process_obj(obj)
            if len(P.mqtt_event_list) > last_count:
                L.l.debug('Not keeping up with {} mqtt events'.format(len(P.mqtt_event_list)))
    except Exception as ex:
        L.l.error("General error processing mqtt: {}".format(ex), exc_info=True)
    finally:
        P.mqtt_lock.release()
        prctl.set_name("idle")
        threading.current_thread().name = "idle"


# http://pydispatcher.sourceforge.net/
def init():
    dispatcher.connect(handle_local_event_db_post, signal=Constant.SIGNAL_UI_DB_POST, sender=dispatcher.Any)
    dispatcher.connect(handle_event_mqtt_received, signal=Constant.SIGNAL_MQTT_RECEIVED, sender=dispatcher.Any)
    thread_pool.add_interval_callable(mqtt_thread_run, run_interval_second=0.5)
