import schedule
from app.tools import config
import time
from app.tools import boto_client
from datetime import datetime, timedelta
import json
import logging

awscli = boto_client.Client()

def get_time_span(latest):
    end_time = datetime.now()
    start_time = end_time - timedelta(seconds=latest)
    return start_time, end_time

def average_cpu_utils():
    valid_instances_id = awscli.describe_all_instances()
    l = len(valid_instances_id)
    logging.warning('valid_instances:{}'.format(valid_instances_id))
    cpu_sum = 0
    for i in range(l):
        response = awscli.fetch_cpu(valid_instances_id[i])
        #[[time, cpu usages]]
        if not response:
            cpu = 0
        else:
            cpu = response[0][1]
        cpu_sum += cpu
    return cpu_sum / l if l else -1

def auto_scale():
    current_time = datetime.now()
    cpu_utils =  average_cpu_utils()
    logging.warning(' auto_scaling in session ')
    logging.warning('CPU Usage: {}'.format(cpu_utils))
    if cpu_utils == -1:
        logging.warning('{} no workers in the pool'.format(current_time))
    elif cpu_utils >= config.cpu_threshold:
        response = awscli.create_new_instance()
        logging.warning('{} grow one worker'.format(current_time))
    elif cpu_utils < config.cpu_threshold:
        response = awscli.delete_unused_instance()
        logging.warning('{} shrink one worker'.format(current_time))
    else:
        logging.warning('{} nothing change'.format(current_time))

if __name__ == '__main__':
    #test
    schedule.every(5).seconds.do(auto_scale)
    #schedule.every(2).minute.do(auto_scale)
    while True:
        schedule.run_pending()
        time.sleep(1)