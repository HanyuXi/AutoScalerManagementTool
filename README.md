# EC2 auto scaler and manager application
This project is an assignment for cloud computing courses. The app is written in Python Flask and AWS tech suites. 
<br>
### worker tool
The worker application is a web application used to detect faces and faces with masks in the picture. It has log in panel and stores the history of uploaded pictures. The admin users can also create/delete user accounts. The main application can be accessed through load-balancer URL.
<br>
### management tool
This project has managementuser interface to manually scale the number of running instances and users can control the worker pool. The user guide can be found in doc/A2-documentation.pdf and the requirement of manager application is in doc/a2.pdf . The individual worker applcation is used to detect if the faces in the pictures wearing masks.
The manager app has a user interface where users can see the list of workers, a chart showing the number of workers for past 30mins, create/terminate user instances.
<img src="https://github.com/HanyuXi/Assignment2/blob/main/doc/manager_app1.png" height="400px" width="400px">
For each working instance, the chart of CPU utilization and HTTP requests number information are displayed 
<img src="https://github.com/HanyuXi/Assignment2/blob/main/doc/manager_app2.png" height="400px" width="400px">
<br>
The management application also has two additional components load balancer and auto-scaler
<img src="https://github.com/HanyuXi/Assignment2/blob/main/doc/auto-scaler1.png" height="400px" width="400px">
<br>
In the test directory, the gen.py is a test script to test the auto-scaling feature in manager application.
From the config.py file in manager app directory, you can change the information to your instances setup configuration and run the following command to test the auto-scaler functionality. 
```bash
#!/bin/bash
python3 gen.py <your-load-balancer-url>/api/upload admin admin 4 ./your-photo-dir/ 100
```
