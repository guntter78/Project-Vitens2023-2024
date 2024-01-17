# Welcome to the vitens project!

## Setup website
To install the website, clone first this repository by using the command:
```
git clone https://github.com/guntter78/Project-Vitens2023-2024.git
```
After installation, change your Linux directory to the 'Project-Vitens2023-2024' directory using the following command:
```
cd Project-Vitens2023-2024
```
Next, utilize the bash script to install all the required tools for running the website. Once you've executed this script, the website will start automatically. To stop the website, simply press Ctrl + C.
```
sudo bash vitens-bash/vitens.sh
```




  
## Setup USB Wi-Fi dongle
To install the USB WiFi dongle (TL-WN725N) on the Raspberry Pi, you need to clone the repository. Within this repository, you will find a driver designed for Linux systems
```
git clone https://github.com/AIRCRACK-NG/RTL8188EUS
```

Install the required packages since we will be building the source firmware ourselves
```
sudo apt-get install -y build-essential git
```

There is a Raspberry Pi package to add the kernel headers. You can choose one here, and if one doesn't work, try the other.
```
sudo apt-get install -y linux-headers
```
```
sudo apt-get install -y raspberrypi-kernel-headers
```
To compile the driver, you must have 'make' and a compiler installed, along with the necessary kernel headers. If you are unsure about these requirements, please refer to your Linux distribution's documentation.

Now, let's proceed with the compilation:
```
make all
```

Installing:
```
sudo make install
```

Next, enable your WiFi dongle and configure it with the credentials of your own Wi-Fi network
```
sudo nano /etc.network/interface
```
Insert the following commands into the file
```
auto wlan0
iface wlan0 inet dhcp
wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
```

Then, input your credentials into the 'wpa_supplicant.conf' file
```
network={
   ssid="Wi-fi Name"
   psk="Wi-fi password"
}
```

If you use multiple Wi-Fi networks, you can also add more of them in the 'wpa_supplicant.conf' file.
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

The second Wi-Fi dongle has an access point enabled, allowing you to connect to the Wi-Fi. The credentials for this access point are:
```
ssid = vitens-wifi-1
wpa_passphrase = vitensproject
```
When a change in the access point credentials is necessary, it should be made in the /etc/hostapd/hostapd.conf file.
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
Additionally, there is a 'net.rules' file where each dongle has its own set of rules to adhere to. For instance, 'wlan0' always has the MAC address '40:ed:00:b8:46:1b,' and 'wlan1' is assigned '66:49:b5:ae:1a:08.' This ensures that even if the dongles are removed and reinserted in a different order, they continue to serve their intended purposes. The set of rules can be found in the '/etc/udev/rules.d/70-persistent-net.rules' file.
```
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="40:ed:00:b8:46:1b", NAME="wlan0"
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="66:49:b5:ae:1a:08", NAME="wlan1"
```



