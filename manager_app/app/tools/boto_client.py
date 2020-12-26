from flask import render_template, redirect, url_for, request
from app import webapp
import time, os
import boto3
from ..tools import config
from datetime import datetime, timedelta, date
from operator import itemgetter


###############Running in the instance############
#import requests
#r = requests.get('http://169.254.169.254/latest/meta-data/iam/security-credentials/assignment2S3')
#json_obj = r.json()
#print(json_obj)
#TOKEN = json_obj["Token"]
#AccessKeyId = json_obj["AccessKeyId"]
#SecretAccessKey=json_obj["SecretAccessKey"]
class Client:
    def __init__(self):
        #self.session = boto3.Session(region_name = 'us-east-1', aws_access_key_id= AccessKeyId, aws_secret_access_key=SecretAccessKey, aws_session_token=TOKEN)
        #self.ec2 = self.session.resource('ec2')
        #self.ec2_client = boto3.client('ec2', aws_access_key_id= AccessKeyId, aws_secret_access_key=SecretAccessKey, aws_session_token=TOKEN)
        #self.s3 = boto3.client('s3', aws_access_key_id= AccessKeyId, aws_secret_access_key=SecretAccessKey, aws_session_token=TOKEN)
        #self.cloudwatch_client = boto3.client('cloudwatch', aws_access_key_id= AccessKeyId, aws_secret_access_key=SecretAccessKey, aws_session_token=TOKEN)
        #load balancer
        #self.elb = boto3.client('elbv2', aws_access_key_id= AccessKeyId, aws_secret_access_key=SecretAccessKey, aws_session_token=TOKEN)
        ###############Running locally############
        self.ec2 = boto3.resource('ec2')
        self.ec2_client = boto3.client('ec2')
        self.s3 = boto3.client('s3')
        self.cloudwatch_client = boto3.client('cloudwatch')
        #load balancer
        self.elb = boto3.client('elbv2')
    def list_workers(self, status):
        if status == "" or status == "all":
            instances = self.ec2.instances.all()
        else: 
            instances = []
            instances = self.ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': [status]}])
        return instances

    def create_new_instance(self):
        # define userdata to be run at instance launch
        userdata = config.user_data
        instance = self.ec2.create_instances(ImageId=config.ami_id, MinCount=1, MaxCount=1, 
                         InstanceType=config.instance_type, SubnetId=config.subnet_id, UserData=config.user_data, IamInstanceProfile=config.IamInstanceProfile,
                         TagSpecifications=config.TagSpecifications)
        instance = instance[0]
        instance_Id = instance.id
       
        while (instance.state['Name'] != "running"):
            time.sleep(1)
            instance = self.ec2.Instance(instance_Id)
            instance_Id = instance.id

        instance_ip = instance.public_ip_address
        print("instance ip address")
        print(instance_ip)
        self.elb.register_targets(
            TargetGroupArn=config.target_group_arn,
            Targets=[{'Id': instance_Id, 'Port': 5000}])

        self.elb.create_listener(
            DefaultActions=[
                    {
                        'TargetGroupArn': config.target_group_arn,
                        'Type': 'forward',
                    },
                ],
                LoadBalancerArn=config.load_balancer_arn,
                Port=5000,
                Protocol='HTTP',
            )
        import paramiko
        key = paramiko.RSAKey.from_private_key_file('/Users/hanyuxi/.ssh/ECE1779A1.pem')
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        cmd="cd /home/ubuntu/Desktop/Assignment1/MaskImageDetectionWebApp && . config/ProjectEnv.sh && python3 wsgi.py &> run.log &"
        # Connect/ssh to an instance
        try:
            # Here 'ubuntu' is user name and 'instance_ip' is public IP of EC2
            client.connect(hostname=instance_ip, username="ubuntu", pkey=key)
            # Execute a command(cmd) after connecting/ssh to an instance
            stdin, stdout, stderr = client.exec_command(cmd)
            print(stdout.read())
            # close the client connection once the job is done
            client.close()
        except Exception as e:
            print(e)
    
    ### Fetch the status of each instance: healthy, draining, unused, ...
    def describe_all_instances(self):
        res =  []
        response = self.elb.describe_target_health(TargetGroupArn=config.target_group_arn)
        for x in response["TargetHealthDescriptions"]:
            #print(x)
            if x["TargetHealth"]["State"] in ["healthy", "unhealthy"]:
                res.append(x["Target"]["Id"])
        print(res)
        return res
    
    ### Fetch the status of each instance: healthy, draining, unused, ...
    def fetch_all_elb_status(self):
        res =  {}
        response = self.elb.describe_target_health(TargetGroupArn=config.target_group_arn)
        for x in response["TargetHealthDescriptions"]:
            res[x["Target"]["Id"]] = x["TargetHealth"]["State"]
        #print(res)
        return res

    ###Chart to show the http rates of ELB
    def fetch_http_rates(self, id):
        response = self.cloudwatch_client.get_metric_statistics(
            Namespace="AWS/ApplicationELB",
            MetricName="RequestCount",
            Dimensions=[
                {
                    "Name": "LoadBalancer",
                    "Value": "app/ece1779-a2/c556a59511a7b3b6"
                },
            ],
            StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
            Period=60,
            Statistics=["Sum"])   

        http_rates_axis = []
        for point in response['Datapoints']:
            hour = point['Timestamp'].hour
            minute = point['Timestamp'].minute
            time = hour + minute/60
            http_rates_axis.append([time,point['Sum']])
        return http_rates_axis

    ###Chart to show the CPU of instance
    def fetch_cpu(self, id):
        metric_name = 'CPUUtilization'
        namespace = 'AWS/EC2'
        statistic = 'Average'                  
        cpu = self.cloudwatch_client.get_metric_statistics(
            Period=1 * 60,
            StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
            MetricName=metric_name,
            Namespace=namespace,  # Unit='Percent',
            Statistics=[statistic],
            Dimensions=[{'Name': 'InstanceId', 'Value': id}]
        )
        cpu_stats = []
        for point in cpu['Datapoints']:
            hour = point['Timestamp'].hour
            minute = point['Timestamp'].minute
            time = hour + minute/60
            cpu_stats.append([time,point['Average']])
        cpu_stats = sorted(cpu_stats, key=itemgetter(0))
        return cpu_stats

    ###Chart to show the CPU of instance
    def fetch_last_30_instances(self):
        date_filter = date.isoformat(date.today()) + '*'
        cnt = 0
        instances = self.ec2.instances.filter(Filters=[{'Name':'launch-time', 'Values':[date_filter]}])
        for _ in instances:
            cnt+=1
        return cnt

    ### Terminate all running workers
    def terminate_all_instances(self):
        instances = self.ec2.instances.filter(Filters=[{'Name':'tag:name', 'Values': ['ece1779']}])
        #print(instances)
        for instance in instances:
            #print(instance)
            instance.terminate()
        return 

    def delete_s3_objects(self):
        BUCKET = 'ece1779a2hanyu'
        PREFIX = '/home/ubuntu/Desktop/Assignment1/MaskImageDetectionWebApp/app/static/images/test/work/'

        response = self.s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)

        for object in response['Contents']:
            #print('Deleting', object['Key'])
            self.s3.delete_object(Bucket=BUCKET, Key=object['Key'])
        return 
    def destroy_instance(self, id):
        self.ec2.instances.filter(InstanceIds=[id]).terminate()
        return

    def delete_unused_instance(self):
        list_of_instances = self.describe_all_instances()
        if len(list_of_instances) >=1:
            #print(list_of_instances)
            self.ec2.instances.filter(InstanceIds=[list_of_instances[0]]).terminate()
        return
