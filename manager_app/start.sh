#!/bin/bash
echo "Start sourcing virtual environment"
source ./assignment2/bin/activate
echo "Finish sourcing virtual environment"

python3 wsgi.py &> manager_app.log &
#Checking the status of running manager app
if [ $? == 0 ]
then
    echo "Manager App started successfully"
else
    echo "Something is wrong with the running manager app"

python3 auto_scaler.py &> auto_scaler.log &
if [ $? == 0 ]
then
    echo "Manager App started successfully"
else
    echo "Something is wrong with the running manager app"
    