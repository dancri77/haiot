__author__ = 'Dan Cristian<dan.cristian@gmail.com>'

from main.logger_helper import Log
from main.admin import thread_pool
import node_run

initialised=False

def unload():
    #...
    thread_pool.remove_callable(node_run.thread_run)
    global initialised
    initialised = False

def init():
    Log.logger.info('Node module initialising')
    #node_run.init()
    thread_pool.add_interval_callable_progress(node_run.thread_run,
                                               run_interval_second=10,progress_func=node_run.get_progress)
    global initialised
    initialised = True

if __name__ == '__main__':
    node_run.thread_run()