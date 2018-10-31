from collections import defaultdict
import process
import preferences

VERBOSE = False
DEFAULT_RESOURCE_HOG_COUNT = 3
BACKGROUND_PROCESS_MAX_CPU = 0.35
busy_count = defaultdict(int)
suspended_tasks = set()

def manage(foregroundTasks, backgroundTasks):
    for task in foregroundTasks:
        busy_count[task.pid] = 0
        resume(task.pid)

    for task in filter(lambda task: process.cpu(task.pid) > BACKGROUND_PROCESS_MAX_CPU, backgroundTasks):
        busy_count[task.pid] += 1
        max_busy_count = get_resource_hog_count(task.pid)
        if VERBOSE: print "Suspender: busy %d %d %s" % (busy_count[task.pid], max_busy_count, process.process(task.pid))
        if get_auto_preference(task.pid) and busy_count[task.pid] > max_busy_count:
            suspend(task.pid)

def suspend(pid, manual=False, auto=False):
    if manual: print "Suspender: suspend %d %d %s %s %s" % (pid, get_resource_hog_count(pid), manual, auto, process.location(pid))
    if process.suspend(pid):
        suspended_tasks.add(pid)
        if manual:
            reset_resource_hog_count(pid)
        if auto:
            set_auto_preference(pid, True)

def resume(pid, manual=False, auto=False):
    if manual: print "Resume: resume %d %d %s %s %s" % (pid, get_resource_hog_count(pid), manual, auto, process.location(pid))
    if process.resume(pid):
        if pid in suspended_tasks:
            suspended_tasks.remove(pid)
        if manual:
            busy_count[pid] = 0
            increase_resource_hog_count(pid)
        if auto:
            set_auto_preference(pid, False)

def set_auto_preference(pid, value):
    preferences.set("auto - %s" % process.location(pid), value)

def get_auto_preference(pid):
    return preferences.get("auto - %s" % process.location(pid))

def get_resource_hog_count(pid):
    return preferences.get("rhc__%s" % pid, DEFAULT_RESOURCE_HOG_COUNT)

def reset_resource_hog_count(pid):
    preferences.set("rhc__%s" % pid, DEFAULT_RESOURCE_HOG_COUNT)

def increase_resource_hog_count(pid):
    current_count = preferences.get("rhc__%s" % pid, DEFAULT_RESOURCE_HOG_COUNT)
    preferences.set("rhc__%s" % pid, 10 * current_count)

def get_suspended_tasks():
    if VERBOSE: print "Suspender: suspended tasks %s" % suspended_tasks
    return [process.process(pid) for pid in suspended_tasks]

def exit():
    for pid in suspended_tasks:
        process.resume(pid)