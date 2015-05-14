__author__ = 'dcristian'

SIGNAL_SENSOR = 'signal-from-sensor'
SIGNAL_SENSOR_DB_POST = 'signal-from-db-post'
SIGNAL_MQTT_RECEIVED = 'signal-from-mqtt-data-received'
SIGNAL_HEAT = 'signal-from-heat'
SIGNAL_GPIO = 'signal-from-GPIO'


ERROR_CONNECT_MAX_RETRY_COUNT = 2
ERROR_CONNECT_PAUSE_SECOND = 1
OS = 'not initialised'
OS_LINUX={'linux', 'posix'}
OS_WINDOWS={'windows', 'nt'}
MACHINE_TYPE_BEAGLEBONE = 'beaglebone'
MACHINE_TYPE_RASPBERRY = 'raspberry'
MACHINE_TYPE_OPENWRT = 'openwrt'
MACHINE_TYPE_INTEL_LINUX = 'intel-linux'

HOST_NAME='not initialised'
HOST_MAIN_IP='not initialised'
HOST_MACHINE_TYPE='not initialised'
HOST_PRIORITY=-1

IS_MACHINE_BEAGLEBONE = False
IS_MACHINE_RASPBERRYPI = False
IS_MACHINE_INTEL = False
IS_MACHINE_OPENWRT = False

def IS_OS_WINDOWS():
    return OS in OS_WINDOWS
def  IS_OS_LINUX():
    return OS in OS_LINUX

SCRIPT_RESPONSE_OK='RESULTOK'
SCRIPT_RESPONSE_NOTOK='RESULTNOTOK'

P_MZP_SERVER_URL='MZP_SERVER_URL'
P_MQTT_HOST_1='MQTT_HOST'
P_MQTT_PORT_1='MQTT_PORT'
P_MQTT_TOPIC='MQTT_TOPIC'
P_MQTT_HOST_2='MQTT_HOST_2'
P_MQTT_PORT_2='MQTT_PORT_2'
P_MQTT_HOST_3='MQTT_HOST_3'
P_MQTT_PORT_3='MQTT_PORT_3'
P_PLOTLY_USERNAME='PLOTLY_USERNAME'
P_PLOTLY_APIKEY='PLOTLY_APIKEY'
P_PLOTLY_ALTERNATE_CONFIG='P_PLOTLY_ALTERNATE_CONFIG'
P_OWSERVER_HOST_1='OWSERVER_HOST_1'
P_OWSERVER_PORT_1='OWSERVER_PORT_1'
P_DDNS_RACKSPACE_CONFIG_FILE='DDNS_RACKSPACE_CONFIG_FILE'
P_USESUDO_DISKTOOLS='P_USESUDO_DISKTOOLS'
P_FLASK_WEB_PORT='P_FLASK_WEB_PORT'

SMARTCTL_MODEL_FAMILY='Model Family:'
SMARTCTL_MODEL_DEVICE='Device Model:'
SMARTCTL_SERIAL_NUMBER='Serial Number:'
SMARTCTL_TEMP_ID='194 Temperature_Celsius'
SMARTCTL_STATUS='SMART overall-health self-assessment test result:'
SMARTCTL_ERROR_SECTORS='198 Offline_Uncorrectable'
SMARTCTL_START_STOP_COUNT='4 Start_Stop_Count'
SMARTCTL_LOAD_CYCLE_COUNT='193 Load_Cycle_Count'
SMARTCTL_ERROR_NO_DISK='Unable to detect device type'
SMARTCTL_DEVICE_IN_STANDBY='Device is in STANDBY mode'
HDPARM_STATUS='drive state is:'
FREE_MEM_STATUS='Mem:'

DISK_DEV_MAIN='/dev/sd'

JSON_MESSAGE_TYPE='message_type'
JSON_PUBLISH_DATE='datetime_'
JSON_PUBLISH_TABLE='table_'
#JSON_PUBLISH_RECORD_OPERATION='operation_'
JSON_PUBLISH_OPERATION_UPDATE='update'
JSON_PUBLISH_SOURCE_HOST='source_host_'
JSON_PUBLISH_TARGET_HOST='target_host_'
JSON_PUBLISH_VALUE_TARGET_HOST_ALL='*'
JSON_PUBLISH_GRAPH_X='graph_x_'
JSON_PUBLISH_GRAPH_Y='graph_y_'
JSON_PUBLISH_GRAPH_SHAPE='graph_shape_'
JSON_PUBLISH_GRAPH_ID='graph_id_'
JSON_PUBLISH_GRAPH_LEGEND='graph_legend_'
JSON_PUBLISH_SAVE_TO_GRAPH='save_to_graph'
JSON_PUBLISH_FIELDS_CHANGED='last_commit_field_changed_list'

GPIO_PIN_TYPE_BBB='bbb'
GPIO_PIN_TYPE_PI='pi'

