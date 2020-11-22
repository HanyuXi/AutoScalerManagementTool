from flask import render_template, redirect, url_for, request
from app import webapp

import boto3
from .tools import config
from .tools.boto_client import Client
from datetime import datetime, timedelta
from operator import itemgetter


aws_client = Client()
##List the worker pool
@webapp.route('/',methods=['GET','POST'])
def ec2_list():
    status = request.form.get('filter', "")  
    instances = aws_client.list_workers(status)
    last_30_min = aws_client.fetch_last_30_instances()
    all_status = aws_client.fetch_all_elb_status()
    print(all_status)
    instance_list = []
    for instance in instances:
        a = {}
        a["id"]=instance.id
        a["instance_type"]=instance.instance_type
        a["az"]=instance.placement['AvailabilityZone']
        a["ip_address"]=instance.public_ip_address 
        a["state"]=instance.state['Name'] 
        if instance.id in all_status:
            a["status"] = all_status[instance.id]
        else:
            a["status"] = ""
        instance_list.append(a)
    print(instance_list)
    return render_template("ec2_examples/list.html",title="Assignment 2",instances=instance_list, last_30 = last_30_min)

@webapp.route('/ec2_examples/decrease/',methods=['POST'])
# Terminate a EC2 instance
def decrease_worker():
    aws_client.delete_unused_instance()
    return redirect(url_for('ec2_list'))


@webapp.route('/ec2_examples/<id>',methods=['GET'])
#Display details about a specific instance.
def ec2_view(id):
    ec2 = aws_client.ec2
    instance = ec2.Instance(id)
    cpu_stats = aws_client.fetch_cpu(id)
    cpu_stats = sorted(cpu_stats, key=itemgetter(0))

    http_rates =  aws_client.fetch_http_rates(id)
    http_rates = sorted(http_rates, key=itemgetter(0))

    return render_template("ec2_examples/view.html",title="Instance Info",
                           instance=instance,
                           cpu_stats=cpu_stats,
                           http_rates_axis=http_rates)


@webapp.route('/ec2_examples/create',methods=['POST'])
# Start a new EC2 instance
def ec2_create():
    aws_client.create_new_instance()
    return redirect(url_for('ec2_list'))


@webapp.route('/ec2_examples/delete/<id>',methods=['POST'])
# Terminate a EC2 instance
def ec2_destroy(id):
    aws_client.destroy_instance(id)
    return redirect(url_for('ec2_list'))


@webapp.route('/ec2_examples/terminate_all',methods=['POST'])
# Start a new EC2 instance
def terminating_all():
    aws_client.terminate_all_instances()
    return redirect(url_for('ec2_list'))

@webapp.route('/ec2_examples/erasing_all',methods=['POST'])
# Start a new EC2 instance
def erase_data():
    aws_client.delete_s3_objects()
    return redirect(url_for('ec2_list'))