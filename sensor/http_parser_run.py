__author__ = 'Dan Cristian <dan.cristian@gmail.com>'

import time
import serial
from main.logger_helper import Log
from common import Constant, utils, variable
import serial_common
from main.admin import models, model_helper

# APS SOLAR ECU LINK: http://192.168.0.10/cgi-bin/home
_initialised_solar_aps = False
__start_keyword = 'Lifetime generation</td><td align=center>'
__end_keyword = ' kWh</td>'


def init_solar_aps():
    global __start_keyword, __end_keyword, _initialised_solar_aps
    production = utils.parse_http(model_helper.get_param(Constant.P_SOLAR_APS_LOCAL_URL),
                                  __start_keyword, __end_keyword)
    if production is not None and production is not '':
        _initialised_solar_aps = True
    else:
        _initialised_solar_aps = False
    return _initialised_solar_aps


def thread_solar_aps_run():
    global __start_keyword, __end_keyword, _initialised_solar_aps
    if variable.NODE_THIS_IS_MASTER_OVERALL:
        production = utils.parse_http(model_helper.get_param(Constant.P_SOLAR_APS_LOCAL_URL),
                                      __start_keyword, __end_keyword)
        if production is not None:
            production = float(production)
            utility_name = model_helper.get_param(Constant.P_SOLAR_UTILITY_NAME)
            record = models.Utility()
            record.utility_name = utility_name
            current_record = models.Utility.query.filter_by(utility_name=utility_name).first()
            if current_record is not None:
                if current_record.units_total is None:
                    record.units_delta = 0
                else:
                    record.units_delta = production - current_record.units_total
                    if record.units_delta == 0:
                        # do not waste db space if no power generated
                        return
                record.units_total = production
                record.unit_name = current_record.unit_name

            else:
                record.units_delta = production
                record.units_total = production
            if current_record.unit_cost is None:
                current_record.unit_cost = 0.0
            record.cost = 1.0 * record.units_delta * current_record.unit_cost
            record.save_changed_fields(current_record=current_record, new_record=record, debug=False,
                                       notify_transport_enabled=True, save_to_graph=True, save_all_fields=True)


