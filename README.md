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
git clone https://github.com/AIRCRACK-NG/RTL8188EUS
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
sudo apt-get install -y raspberrypi-kernel-headers
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

In the second Wi-fi dongle, there is an access point enabled so you can connect to the Wi-fi.
The credentials are:
```
ssid = vitens-wifi-1
wpa_passphrase = vitensproject
```

When there needs to be a change in the credentials of the access point it is in the /etc/hostapd/hostapd.conf file. 
```
interface=wlan1
driver=nl80211
ssid=vitens-wifi-1
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=vitensproject
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```
Also, there is a net.rules where every dongle has its own set of rules to follow.
For example, wlan0 has always this mac-address "40:ed:00:b8:46:1b" and wlan1 "66:49:b5:ae:1a:08" so when the dongle is removed and put back in the wrong order is still have the same purpose instead of switching there work.
The set of rules is in  /etc/udev/rules.d/70-persistent-net.rules     
```
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="40:ed:00:b8:46:1b", NAME="wlan0"
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="66:49:b5:ae:1a:08", NAME="wlan1"
```



