import schedule
from app.tools import config
import aws
import json
import logging

awscli = aws.AwsClient()

def auto_scale():
    current_time = datetime.now()
    cpu_utils = average_cpu_utils()
    logging.warning(' auto_scaling in session ')
    if cpu_utils > config.cpu_grow:
        response = awscli.grow_worker_by_ratio(config.ratio_expand)
        logging.warning('{} grow workers: {}'.format(current_time, response))
    elif cpu_utils < config.cpu_shrink:
        response = awscli.shrink_worker_by_ratio(config.ratio_shrink)
        logging.warning('{} shrink workers: {}'.format(current_time, response))
    else:
        logging.warning('{} nothing change'.format(current_time))

if __name__ == '__main__':
    schedule.every().minute.do(auto_scale)
    while True:
        schedule.run_pending()
        time.sleep(1)