#ami_id = 'ami-0bf618774e7879c6a'
ami_id = 'ami-0b50150c9c4291785'
subnet_id = 'subnet-04ed5d5b'
target_group_arn = 'arn:aws:elasticloadbalancing:us-east-1:290459861332:targetgroup/a2/cf3d370e735dd362'
load_balancer_arn ='arn:aws:elasticloadbalancing:us-east-1:290459861332:loadbalancer/app/test22/0a81dea572c4ab23'
security_group = ['sg-07ab8eeb13e883e5a']
monitoring_status = True
instance_type = 't2.medium'
user_data = """#cloud-config
runcmd:
- ls
"""
user_data_bk = """#cloud-config
runcmd:
- su ubuntu
- cd /home/ubuntu/Desktop/Assignment1/MaskImageDetectionWebApp
- cp -r * /home/ubuntu
- cd /home/ubuntu/
- . config/ProjectEnv.sh
- python3 -m pip install torch torchvision
- python3 -m pip install opencv-python
- python3 -m pip install -r requirement.txt
- python3 wsgi.py &> run.log &
"""
TagSpecifications= [
    {
      'ResourceType': 'instance',
      'Tags': [
        {
          'Key': 'name',
          'Value': 'ece1779'
        },
      ]
    }]
IamInstanceProfile={'Name': 'assignment2S3'}
