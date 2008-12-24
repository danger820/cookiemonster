#!/bin/echo You must run this by typing: . 

export LD_LIBRARY_PATH=./FC9Live-binaries/:${LD_LIBRARY_PATH}
export LIBRARY_PATH=./FC9Live-binaries/:${LIBRARY_PATH}

su -c "/sbin/rmmod rt73usb"
su -c "/sbin/rmmod rt2x00usb"
su -c "/sbin/rmmod rt2500usb"
su -c "/sbin/insmod ./FC9Live-binaries/rt73-2.6.25-14.fc9.ko"
su -c "/sbin/insmod ./FC9Live-binaries/rt2570-2.6.25-14.fc9.ko"
su -c "/sbin/insmod ./FC9Live-binaries/ipwraw-2.6.25-14.fc9.ko"

su -c "/sbin/iwpriv rausb0 forceprism 0"

su -c "/sbin/iwconfig rausb0 rate 1Mbit"

su fedora -c "firefox ./user_agent_switcher-0.6.11-ff3.xpi &"
su -c "/sbin/ifconfig rausb0 up"

su -c "/sbin/iwlist scan"

su -c "./cookiemonster.py -h"

echo
echo "You can now run ./cookiemonster.py with the the appropriate options"
echo 
echo "A good choice is probably: ./cookiemonster.py -i rausb0 -d rt73 -u -r" 
echo "You may also want to select a channel from the above list of unencrypted APs.." 

su 
