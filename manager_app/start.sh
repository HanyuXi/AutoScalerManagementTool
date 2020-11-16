#!/bin/bash
echo "Start running the application"

source ./assignment2/bin/activate
python3 wsgi.py &> run.log