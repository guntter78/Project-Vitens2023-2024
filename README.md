# Welcome to the vitens project!

## Setup website
To install the website, clone first this repository by using the command:
```
git clone https://github.com/guntter78/Project-Vitens2023-2024.git
```
After the installation, Change the directory of your Linux to the new Project-Vitens2023-2024 directory with the command:
```
cd Project-Vitens2023-2024
```
Then use the bash scrip to install all the necessary tools to run the website.
after using this script the website will run automatically. To stop your website press ctrl + c
```
sudo bash vitens-bash/vitens.sh
```

## Setup USB Wi-Fi dongle
To install the USB WiFi dongle (TL-WN725N) in the Raspberry. You have to clone the repository.
In this repository, there is a driver for the Linux systems
```
git clone https://github.com/lwfinger/rtl8188eu
```

Install some necessary packages as we will build the source firmware ourselves
```
sudo apt-get install -y build-essential git
```

There is a package for raspberry pi to add the kernel headers, so you can pick one here (if one doesn't work, use the other)
```
sudo apt-get install -y linux-headers
```
```
Sudo apt-get install -y raspberrypi-kernel-headers
```

To compile the driver, you need to have a make and a compiler installed. In addition, you must have the kernel headers installed. If you do not understand what this means, consult your distro.

Compiling:
```
make all
```

Installing:
```
sudo make install
```

Next you have to enable your WiFi dongle and add the credentials of your own Wi-fi
```
sudo nano /etc.network/interface
```

Add the following commands in the file:
```
auto wlan0
iface wlan0 inet dhcp
wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
```

Now add your credentials in the file: wpa_supplicant.conf
```
network={
   ssid="Wi-fi Name"
   psk="Wi-fi password"
}
```

If you use multiple Wi-fi spots you can also add more in the file Wpa_supplicant.conf
```
network={
   ssid="Wi-fi Name 1"
   psk="Wi-fi password"
}

network={
   ssid="Wi-fi Name 2"
   psk="Wi-fi password"
}
```





