#!/usr/bin/python

import os
import sys
import getopt

IS_FC9 = False
if "2.6.25-14.fc9" in os.uname()[2]:
  IS_FC9 = True

def copy_cookies(do_chown, src, dest):
  # FIXME: Yah yah, lame. but I'm lazy and we're already tightly dependedent
  # on UNIX paths below..
  os.system("cp "+src+" "+dest)
  if do_chown:
    os.system("chown fedora "+dest)

def usage():
  print "Usage:"
  print "%s [-P <FirefoxProfile>] [-I <ImpersonateIP>] [--ff3]" % sys.argv[0]

def main():
  try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "P:I:", ["ff3"])
  except getopt.GetoptError:
    usage()
    return

  use_ff3 = False
  use_profile = use_ip = None

  for o, a in opts:
    if o == "--ff3":
      use_ff3 = True
    if o == "-P":
      use_profile = a
    if o == "-I":
      use_ip = a
 
  do_chown = False
  if os.getuid() == 0:
    if not IS_FC9:
      print "You must run this as your normal user"
      return
    else:
      do_chown = True
 
  if do_chown and IS_FC9:
    root_dir = "/home/fedora/.mozilla/firefox/"
  else:
    root_dir = os.getenv("HOME") + "/.mozilla/firefox/"
    
  subdirs = os.listdir(root_dir)

  subdirs = filter(lambda x: x not in ["Crash Reports", "pluginreg.dat", "profiles.ini"], subdirs)
  
  if not subdirs:
    print "You need to create a Firefox profile. Run firefox first."
    return

  cookies = os.listdir("./cookies")

  if use_ff3:
    cookies = filter(lambda x: ".sqlite" in x, cookies)
  else:
    cookies = filter(lambda x: ".txt" in x, cookies)

  if not cookies:
    print "No cookies stored for your Firefox version (do you need --ff3?)"
    return

  if use_profile:
    for dr in subdirs:
      if use_profile in dr:
        print "Using profile: "+dr
        break
    else:
      print "No Firefox profile found matching '"+use_profile+"'"
      return

  if use_ip:
    for ip in cookies:
      if use_ip in ip:
        print "Using cookie file: "+ip
        break
    else:
      print "No cookies available for IP '"+use_ip+"'"
      return

  if not use_profile: 
    print "Choose a Firefox profile to copy to (will destroy current cookies): "
    while True:
      d = 0
      for dr in subdirs:
        print str(d+1)+") "+dr.split(".")[1]
        d = d+1
      try:
        d = int(raw_input("> "))
        if d < 0:
          print "Invalid choice.\n"
          continue
        dr = subdirs[d-1]
        break
      except KeyboardInterrupt:
        return
      except: pass
      print "Invalid choice.\n"
    
  if not use_ip:
    print "\nChoose IP to impersonate: "
    while True:
      i = 0
      for ip in cookies:
        if i % 3 == 2:
          print (str(i+1)+") ").rjust(5)+ip.split("-")[0].ljust(15)
        else:
          print (str(i+1)+") ").rjust(5)+ip.split("-")[0].ljust(15),
        i = i+1
      try:
        print
        i = int(raw_input("> "))
        if i < 0:
          print "Invalid choice.\n"
          continue
        ip = cookies[i-1]
        break
      except KeyboardInterrupt:
        return
      except: pass
      print "Invalid choice.\n"
 
  if use_ff3:
    copy_cookies(do_chown, "./cookies/"+ip, root_dir+dr+"/cookies.sqlite")
  else:
    copy_cookies(do_chown, "./cookies/"+ip, root_dir+dr+"/cookies.txt")

  print
  y = raw_input("Would you like to launch firefox with this profile now? [Y/N]: ")
  if y[0].lower() == "y":
    if do_chown and IS_FC9:
      os.system('su fedora -c "killall firefox"')
      os.system('su fedora -c "firefox -no-remote -P '+dr.split(".")[1]+'"')
    else:
      os.system("firefox -no-remote -P "+dr.split(".")[1])

if __name__ == '__main__':
  main()
