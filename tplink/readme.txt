2.1. Compilation tool and kernel sources
Before you compile the driver, please make sure you have the correct compile tool and 
kernel sources.
We can install compile tool gcc by command “apt-get install gcc”
Note : We recommend you use a suitable compile tool to compile our driver.
For example:

According to the command “cat /proc/version”, we could see your linux system is compiled 
by gcc4.8.2. So we recommend you use gcc4.8.2 to compile our driver if possible.

2.2. Compile and install the Driver

1. Access the directory of driver.
2. Before compile, make sure the parameters in “makefile.c” is suitable for your 
compile environment of your Linux system.
ifeq ($(CONFIG_PLATFORM_I386_PC), y)
EXTRA_CFLAGS += -DCONFIG_LITTLE_ENDIAN
SUBARCH := $(shell uname -m | sed -e s/i.86/i386/)
ARCH ?= $(SUBARCH)
CROSS_COMPILE ?=
KVER := $(shell uname -r)
KSRC := /lib/modules/$(KVER)/build
MODDESTDIR := /lib/modules/$(KVER)/kernel/drivers/net/wireless/
INSTALL_PREFIX :=
endif
Explanation:
· KSRC is used to specify the kernel source path for driver compilation.
· CROSS_COMPILE is used to specify the toolchain.
· ARCH is used to specify the target platform's CPU architectures such as arm, mips, 
i386 and so on.
1
If your Linux kernel does not support 802.11, please annotate macro 
“CONFIG_IOCTL_CFG80211” in “makefile.c”.
CONFIG_IOCTL_CFG80211=n
ifeq ($(strip &(CONFIG_IOCTL_CFG80211)),y)
EXTRA_CFLAGS + = -DCONFIG_IOCTL_CFG80211 = 1
EXTRA_CFLAGS + = -DRTW_USE_CFG80211_STA_EVENT = 1
endif 

3. Type “sudo make” to compile the driver file.
4. Type “sudo make install” to install the driver file