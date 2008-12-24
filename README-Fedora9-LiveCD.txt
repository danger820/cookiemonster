           How to Use CookieMonster With a Fedora 9 LiveCD


This is probably the quickest, easiest way to go about testing your
sites, especially if you are not a Linux user.

Before performing these steps, it is strongly recommended you read the
README-First.txt file, so you understand how the tool works and the
the various options it has.


I. ITEMS NEEDED:
   1. Linksys WUSB54GC (~$50 USD)
      Or: http://rt2x00.serialmonkey.com/wiki/index.php/Hardware#rt73 
      Other drivers are supported, but this chipset is setup by default.
      Also note that you cannot use your wireless card for normal 
      Internet access while using this tool, so to test against
      yourself, a second card is needed.
   2. USB storage with this tool on it (>= 4GB recommended - ~$20 USD)
      The tool itself requires only a few megabytes of space, but I
      have discovered the Fedora 9 LiveCD works much better if transfered
      to a USB drive instead. See below for instructions.
   3. CDR with Fedora 9 Live burned on to it 
      (http://fedoraproject.org/en/get-fedora - $0)

Once you have obtained all these items, you are ready to get started.


II. Boot from your Live CD

Intel-based Mac users will need to hold down either 'C' or 'Option'
during startup to boot from the CD. Standard Intel users may similarly
need to hit 'Esc' or some other key sequence to choose their boot
device. 

You probably want to let Fedora verify your media the first time you
boot, to ensure the burn was clean. You can select this by pressing
any key on the very first splash screen. It only takes a few minutes.

Plug in your USB key and Linksys USB device once the system has booted
up. The USB key should cause an icon to appear on your desktop for the
disk.

Now, open a terminal from Applications->System Tools->Terminal. Enter
the USB disk directory by typing:

# cd /media/disk/CookieMonster-20080909

Or wherever you extracted the tool to.


III. Running the Setup Script

A setup script is provided to set up an environment so that it is
ready to go for a Linksys WUSB54GC. Run it with:

# . ./fc9-livecd-setup.sh 

from the cookiemonster directory. You can safely re-run this script as
many times as you like.


IV. Other drivers and devices

Precompiled versions of the three main drivers provided by
http://homepages.tu-darmstadt.de/~p_larbig/wlan/ can be found in the
FC9Live-binaries directory and will be loaded automatically.

As far as devices, you should have good luck with any of the cards listed
here: http://www.aircrack-ng.org/doku.php?id=compatibility_drivers#usb

However, using them may require changes to that setup script, primarily
because the other devices will have different interface names instead
of "rausb0". Typing "/sbin/iwconfig" will give you a list of your
detected wireless devices.

If your built-in wireless isn't supported at all in the LiveCD (this
seemed to be the case for Macbooks), you probably want to purchase a
second wireless card with a different, non-rt73 based chipset, or just
use your wired port for normal Internet access. Be sure to Google the
model number before purchase to make sure it is well supported.

If you do buy an additional external wireless card, it is important
that you do NOT put them next to eachother in their slots, as they can
damage eachother's antennas at such a close proximity. 

If you build additional drivers and they end up working, please let me
know and I will include them (but only if you point me at sources to
build myself :)


V. Running cookiemonster.py

Please consult README-First.txt for more infromation on cookiemonster
itself, but running the setup script above should provide you with
some further instructions for a quick start.



ADDENDUM: Creating a Bootable USB Install for Added Speed+Stability

I noticed that the temporary writable support on most LiveCDs was very
unstable. The more data I wrote to the union filesytem, the more
likely it was for the entire system to crash.

For this reason, you may want to consider installing the Fedora 9 Live
iso image to your USB key, as I've found this can make things a lot
more stable. 

Mac users may need to repartition the USB drive to have a GUID
Paritition Table (GPT) instead of the default MS-DOS table before
completing the following steps. Unfortunately, I did not perform this on
a Mac, as I simply used the wired interface, and the LiveCD itself was
sufficient for this. Additional details from someone who has done this
would be appreciated.

Assuming you either have a Windows machine, or have dealt with the MacOS
GPT reformat, the most straightforward way to do the install itself is
to copy the Fedora 9 image file to your USB key, boot into the LiveCD
you have burned (from that very same image file), and then run:

# su

# /mnt/live/LiveOS/livecd-iso-to-disk --overlay-size-mb 512 
      /media/disk/Fedora-9-i686-Live.iso /dev/<usbdevice>

You can determine your usbdevice by typing 'mount' or 'df -h'. It
should be the /dev filename that is listed as mounted on /media/disk

The install process is non-destructive, and can be performed on live,
mounted usb keys formatted with the default 'vfat' filesystem, and can
even install the .iso FROM the usb key to ITSELF. It will not reformat
or damage any existing data on the drive, so long as you have space.
The process simply creates two directories: 'syslinux' and 'LiveOS'.

After this process is done, you should be able to reboot into your USB
key and use the tools from /media/disk/CookieMonster.

If you encounter random stability issues with the beta version of 
Firefox that is installed, you can upgrade it with 
# su -c "yum upgrade firefox"

I have also noticed that problems with my normal wireless card
were resolved when I did:

# "su -c "yum upgrade wpa_supplicant NetworkManager"

and then rebooted, to upgrade the networking components of the machine.

Upgrading the entire system (su -c "yum upgrade") is also possible.
It will not actually replace your kernel (which means the custom
drivers should still work). This may also fix random bugs you have 
with various aspects of the system, as a lot of stuff has been
fixed between the time this LiveCD was mastered and the current
Fedora 9. If you go this route, you probably want to change that 512 
to at least 1024 in the livecd-iso-to-disk command and have at 
least a 4GB key.

For some reason the Fedora project does not believe in remastering 
their LiveCDs with successive updates, which is why all these steps
are necessary for a stable, working system. Still, they provided the 
most flexible usable LiveCD I was able to find (Knoppix had major X11 
font issues), so I used it.

For more information, consult:
http://fedoraproject.org/wiki/FedoraLiveCD/USBHowTo


