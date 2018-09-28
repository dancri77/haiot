from datetime import datetime
import time
from main.logger_helper import L
from main.admin import models
from rule import rule_common


class P:
    grid_watts = None
    plug1_watts = None
    last_state_change = datetime.min
    grid_importing = None
    plug1_auto_stopped = None
    plug1_job_started = False
    PLUG1_MIN_WATTS_ON = 20  # min consumption to be considered ON
    PLUG1_MIN_WATTS_OFF = 2  # min consumption to be considered OFF
    EXPORT_MIN_WATTS = -50
    RELAY_1_NAME = 'plug_1'
    STATE_CHANGE_INTERVAL = 300  # how often can change state

    def __init__(self):
        pass


def _can_state_change():
    return (datetime.now() - P.last_state_change).total_seconds() > P.STATE_CHANGE_INTERVAL


# energy rule
def rule_energy_export(obj=models.Utility(), field_changed_list=None):
    if field_changed_list is not None:
        if 'units_2_delta' in field_changed_list:
            if obj.utility_name == 'power main mono':
                P.grid_watts = obj.units_2_delta
            elif obj.utility_name == 'power plug 1':
                P.plug1_watts = obj.units_2_delta
            # if exporting
            if P.grid_watts is not None:
                if P.grid_watts <= 0:
                    if P.grid_importing is True or P.grid_importing is None:
                        L.l.info("Exporting power {}w".format(P.grid_watts))
                        P.grid_importing = False
                    if P.grid_watts < P.EXPORT_MIN_WATTS and _can_state_change():
                        L.l.info("Starting plug 1 to reduce export, grid={}".format(P.grid_watts))
                        rule_common.update_custom_relay(relay_pin_name=P.RELAY_1_NAME, power_is_on=True)
                        P.last_state_change = datetime.now()
                        # P.plug1_auto_stopped = False
                        P.plug1_job_started = True
                else:
                    if P.grid_importing is False or P.grid_importing is None:
                        L.l.info("Importing power {}w".format(P.grid_watts))
                        P.grid_importing = True
                    if P.plug1_watts is not None and P.plug1_watts > P.PLUG1_MIN_WATTS_ON and _can_state_change():
                        power_is_on = rule_common.get_custom_relay(P.RELAY_1_NAME)
                        if P.plug1_auto_stopped is True:
                            if power_is_on:
                                L.l.info("Plug1 started, probably overriden by user, plug {}w, grid {}w".format(
                                    P.plug1_watts, P.grid_watts))
                                # to supress above info messages
                                P.last_state_change = datetime.now()
                            else:
                                # all ok, plug is stopped, power is off, saving!
                                pass
                        else:
                            L.l.info("Stopping plug1 to cut import, plug {}w, grid {}w".format(
                                P.plug1_watts, P.grid_watts))
                            time.sleep(10)
                            rule_common.update_custom_relay(relay_pin_name=P.RELAY_1_NAME, power_is_on=False)
                            P.plug1_auto_stopped = True
                            P.last_state_change = datetime.now()
            # reset user override when done to enable automatic switch
            # fixme: min watts might go below in the process, check multiple values
            if P.plug1_job_started and P.plug1_watts is not None and P.plug1_watts <= P.PLUG1_MIN_WATTS_OFF:
                P.plug1_auto_stopped = False
                L.l.info("Plug1 no more consumption, job done, plug {}w, grid {}w".format(P.plug1_watts, P.grid_watts))
                P.plug1_job_started = False
