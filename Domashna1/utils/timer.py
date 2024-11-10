import time

def start_timer():
    return time.time()

def end_timer(start_time):
    return time.time() - start_time
