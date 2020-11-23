#!/bin/bash
echo "Start sourcing V ENV"
source ./assignment2/bin/activate
echo "Finish sourcing V Env"
echo "Start manager app"
python3 wsgi.py &> run.log &

