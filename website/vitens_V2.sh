#!/bin/bash
ENV_DIR=vitens 
DIR=/project

# password for postgresql
export PGPASSWORD='project'

echo " update and upgrade linux system...." 
sleep 2
sudo bash -c 'apt update && apt upgrade -y'

echo
echo " install pip....." 
sleep 2
sudo bash -c 'apt install python3-pip -y'

echo
echo "install tools....." 
sleep 2
sudo bash -c 'apt install build-essential libssl-dev libffi-dev python3-dev -y'
    
echo
echo 'install python enviroment.....:'
sleep 2
sudo bash -c 'apt install -y python3-venv' 


echo
echo "create directory project....:" 
sleep 2
sudo mkdir $DIR


echo
cd ..
echo "copy directory website --> /project/vitens.....:"
cp -r website $DIR

echo
echo "change directory.....:" 
sleep 2
cd $DIR

echo
echo "create python enviroment......:" 
sleep 2
sudo python3 -m venv $ENV_DIR
source $ENV_DIR/bin/activate 

echo
echo intall essential packages.......:
echo install Flask...:
sleep 2
pip install Flask
pip install psycopg2-binary
pip install psycopg2
python -c "import psycopg2"

echo install MQTT
pip install paho-mqtt 
sudo apt install mosquitto -y
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
sudo apt-get install mosquitto-clients -y

echo "Accessing and editing mosquitto.conf..."
sudo touch /etc/mosquitto/mosquitto.conf
echo "bind_address 127.0.0.1" | sudo tee -a /etc/mosquitto/mosquitto.conf
echo "allow_anonymous true" | sudo tee -a /etc/mosquitto/mosquitto.conf
echo "listener 1883" | sudo tee -a /etc/mosquitto/mosquitto.conf
# Restart Mosquitto to apply the changes
sudo systemctl restart mosquitto

echo
echo install POSTgreSQL.....:
sleep 2
sudo sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt-get -y install postgresql

sudo -u postgres psql -c "CREATE USER vitens WITH PASSWORD 'project';"
sudo -u postgres psql -c  "ALTER USER vitens CREATEDB;" 

echo
echo add databas.....:
echo start website......:
cd ../website

cd ../
cd /project/website
sudo python3 db_v2.py
sudo python3 app.py



