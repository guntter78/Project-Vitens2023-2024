
#change echo text to green
GREEN='\033[0;32m'

update_system(){
    echo "${GREEN} update and upgrade linux system...." 
    sleep 2
    sudo bash -c 'apt update && apt upgrade -y'
}


install_py_env(){
    echo "${GREEN} install pip....." 
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
}

create_py_env(){
    echo "create directory project...." 
    sleep 2
    sudo mkdir /project

    echo
    echo "change directory....." 
    sleep 2
    cd /project

    echo
    echo "create python enviroment......" 
    sudo bash -c python3 -m venv vitens
}


create_py_env