#!/bin/bash
ENV_DIR=vitens 
DIR=/project

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
echo 'install python enviroment'
sleep 2
sudo bash -c 'apt install -y python3-venv' 


echo
echo "create directory project....:" 
sleep 2
sudo mkdir $DIR

echo
echo "change directory.....:" 
sleep 2
cd $DIR

echo
echo "copy directory website --> /project/vitens.....:" 
cp -r /home/ubuntu/Documents/Vitens/website $DIR

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

cd website
python app.py



