from main.admin.model_helper import get_param
from common import Constant
from main.logger_helper import Log
from music import ser2net


def zone_set(on, zone_index):
    return ser2net.amp_zone_power(on, int(zone_index))

