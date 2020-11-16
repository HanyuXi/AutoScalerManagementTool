echo "Start running the application"
echo "First, source the env variables"
source /home/ubuntu/Desktop/Assignment1/MaskImageDetectionWebApp/config/ProjectEnv.sh
python3 -m pip install -r requirement.txt
python3 wsgi.py

