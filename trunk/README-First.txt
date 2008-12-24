                       CookieMonster - 20080909
                 Automated Insecure Cookie Hijacker
                            Mike Perry


I. Overview

CookieMonster is a python-based tool that actively gathers insecure
HTTPS cookies, and records these as well as normal http cookies to 
Firefox compatible cookie files.

The HTTPS cookie hijacking works as follows:

 1. Cache all DNS responses on your network to obtain a mapping
    of what host name clients are using when they connect to an IP.
 
 2. When a client IP connects to a server IP using https (port
    443), look up what hostname they resolved in the DNS cache to
    get this IP.
 
 3. Add this domain as a target for that client IP.
 
 4. When that IP then connects to ANY http website, look up
    what targets it has accumulated and inject images for each of
    these into that TCP connection.
 
 5. When the browser fetches these images, it will transmit any
    insecure cookies for that domain and path. Record the
    resulting cookies (and any others we happen to see while we're
    at it) to a Firefox-compatible cookies file.

In addition to the above dynamic method, it is also possible to
configure the tool to grab the cookies for a specific list of domains
for EVERY IP present on the local network, regardless of what sites they
actually visit. Instructions for how to configure it to do this are
provided below.

The injection mechanism is the airpwn-style TCP race condition attack.
Since CookieMonster is local, it is able to respond to arbitrary web
requests considerably faster than the actual webserver. This allows us
to hijack any connections we wish.

Currently, only open and WEPed wireless injection is supported. However,
it should not be too difficult to modify the tool to work with Ethernet
and ettercap as an auxiliary ARP poisoner, or in combination with any
other packet redirection exploit. Please submit patches if you do this,
and I will post them. Likewise if you are insane enough to try to do
WPA/WPA2 as well.


II. Build + Setup

CookieMonster depends upon pypcap, pylorcon, LORCON, and a custom
version of dpkt, all of which have been provided in this distribution as
anonymous SVN checkouts, so you can see what was changed. 

To build all of these modules, simply run:

# ./build-all.sh

The main script 'cookiemonster.py' is set to use these custom versions
in the current directory by default, so if you have system installed
versions of these libraries, you do not need to overwrite them with the
ghetto-hacked stuff here.

In fact, CookieMonster is meant not to be installed at all. After you
build the included libraries, run 

# . lorcon-env.sh

to add the LORCON library directory to your LD_LIBRARY_PATH, and then
everything should run completely out of the current directory.

You probably also want to tell your card to only transmit at 1Mbit,
so that you are able to inject frames into clients that have weak signal 
and/or are very far away from you. For most drivers, this does not 
interefere with your ability to also receive traffic at higher bitrates
from ther clients. You accomplish this setting with something like:

# /sbin/iwconfig rausb0 rate 1mbit


III. Obtaining Drivers

If you are lucky, your current wireless drivers will support monitor
mode, be supported by LORCON, and do raw 802.11 packet injection out of
the box. If so, you can skip this step.

Otherwise, you will probably need to obtain a custom driver for your
wireless card that supports raw 802.11 frame injection.

The canonical source for these drivers for popular cards is:
http://homepages.tu-darmstadt.de/~p_larbig/wlan/


IV. Configuration + Usage

usage: ./cookiemonster.py -i <device> -d <driver> [-c <channel>] 
  [-b <BSSID/Target MAC>] [-k <wep_key>] [--ff3] [-u] [--aggressive]

Supported cards are: nodriver wlan-ng hostap airjack prism54
madwifing madwifiold rtl8180 rt2570 rt2500 rt73 rt61 zd1211rw
bcm43xx d80211 ath5k iwlwifi


CookieMonster works only on one channel at a time. However, it is able
to handle injecting into one WEPed and/or any number of additional
non-WEPd APs that sit on the same channel.

If you would like to target only a specific AP or specific client to
ensure you don't interfere with others' traffic, you can specify this
BSSID (the MAC address of the AP) in colon separated hex format.

The --ff3 option causes CookieMonster to write out Firefox 3 compatible
sqlite cookie files. Without it, Firefox 2.0 cookie files are written
instead.

If you specify -u, browser user agents will get logged to
./cookies/uagent.log.  These can be used with a Firefox extension such
as "User Agent Switcher" to match a target's user agent string.

If you specify --aggressive, then CookieMonster will be more active
about injecting elements. Normally, CookieMonster will only inject
when the user manually types in a URL. This option will cause it to 
inject for link clicks and page elements as well. Since this can
increase the number of attempts needed to successfully cause the browser
to transmit cookies, you probably want to increase MAX_ATTEMPTS if you
set this as well.

Additional configuration settings are specified in config_settings.py.

By default, CookieMonster will actively grab cookies for a handful of
common domains for every IP on the network, including mail.google.com,
mail.yahoo.com, hotmail.com, facebook.com, and myspace.com, even if a
client never connects directly to these sites.  This behavior is
governed by ALWAYS_TARGET in that file, which allows you to specify a
list of domains to actively grab cookies for, regardless of whether we
see HTTPS connections for them. 

Cookies will get dumped into separate files per local client IP. You can
impersonate these IPs by copying the cookie files into directly into a
profile in your ~/.mozilla/firefox/ directory. You may want to create a
separate profile for this by running 'firefox -P'. 

A script './copycookies.py' has also been provided that provides a
text-menu based interface for copying the generated cookie files into
one of your existing Firefox profiles. If you are using Firefox 3,
you'll want to pass --ff3 to that script as well.



V. FAQ

1. My Card isn't supported. What do I do?

Go to your local computer store and purchase a Linksys WUSB54GC or one
of the other cards listed here:
http://rt2x00.serialmonkey.com/wiki/index.php/Hardware#rt73 or here:
http://www.aircrack-ng.org/doku.php?id=compatibility_drivers#usb

These are rt73-based USB cards that are supported by the above driver
set and work well with this tool. They should run you about $50 USD
or less.

Note that you may need to disable prism headers with:
# /sbin/modprobe rt73
# /sbin/iwpriv rausb0 forceprism 0

and also remove your original driver with:
# /sbin/rmmod rt73usb

prior to running cookiemonster.py, but after that it should work just
fine.


B. I'm on Windows/MacOS. What do I do?

Support for these operating systems is not planned, but may happen
automatically if LORCON adds support for them. In the meantime,
consult the README.Fedora9-LiveCD for information on using the Linksys
WUSB54GC with a Fedora 9 Live CD. If you manage to compile other
drivers for that environment and get it working, please let me know.


3. I ran into some other bug. Can you fix it?

If you have a domain name and some form of SSL website, I will fix any
bugs you encounter. I will also accept patches from anyone who cares
to submit one.


5. What should I do with this tool? Pwn n00bs?//?/

No. This tool is not for engaging in criminal activity. It is for
testing sites. I do not endorse or advocate compromising the personal
information of any human* using this software.

If it is the case that you discover other vulnerable sites while in
the course of your testing, please report them to me, so I can post
them at: http://fscked.org/blog/incomplete-list-alleged-vulnerable-sites

Likewise, if you discover some of those sites are no longer vulnerable,
please also inform me so that I can remove them.


* http://en.wikipedia.org/wiki/They_Live
