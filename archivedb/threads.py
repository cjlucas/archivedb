import logging, time
from multiprocessing import Process
from archivedb.monitor import run_oswalk, run_inotify

def test(name):
    time.sleep(3)
    print(name)

def get_thread_info(thread):
    thread_info = {
        "inotify"    : [run_inotify, ()],
        "oswalk"    : [run_oswalk, ()],
    }
    target = thread_info[thread][0]
    args = thread_info[thread][1]

    return(target, args)

def initialize_child_processes(threads):
    threads_dict = {}
    for t in threads:
        target, args = get_thread_info(t)
        threads_dict[t] = create_child_process(target, args)
        #threads_dict[t].daemon = True

    return(threads_dict)

def create_child_process(proc_target, proc_args):
    p = Process(target=proc_target, args=proc_args)
    p.start()
    return(p)

def keep_child_processes_alive(threads_dict):
    for t in threads_dict:
        if threads_dict[t].is_alive() == False:
            log.debug("thread '{0}' was dead, recreating".format(t))
            target, args = get_thread_info(t)
            threads_dict[t] = create_child_process(target, args)
        else:
            pass
            #print("thread '{0}' is still alive".format(t))

    return(threads_dict)

if __name__ == 'archivedb.threads':
    log = logging.getLogger(__name__)
