# set up logging

import os
import logging
import time
import re

from config import cfg

def logger(logname):
    """Basic logging function"""

    if not os.path.exists(cfg['LOGPATH']):
        os.makedirs(cfg['LOGPATH'])

    if cfg["LOGPATH"][-1:] == "/":
        logfull = cfg["LOGPATH"] + logname
    else:
        logfull = cfg["LOGPATH"] + "/" + logname

    if cfg["LOGLEVEL"] == "DEBUG":
        logging.basicConfig(filename=logfull, format='[%(asctime)s] %(levelname)s ARM: %(module)s.%(funcName)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', level=cfg["LOGLEVEL"])
    else:
        logging.basicConfig(filename=logfull, format='[%(asctime)s] %(levelname)s ARM: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', level=cfg["LOGLEVEL"])
    return logfull

def disclogging(disc, oldlog):
    """Direct logging to a disc-specific file and return the path to the logfile
    for redirection of external calls"""

    if disc.label == "":
        if disc.disctype == "music":
            logname = "music_cd.log"
        if disc.disctype == "dvd":
            logname = "dvd.log"
        if disc.disctype == "bluray":
            logname = "bluray.log"
        else:
            logname = "empty.log"
    else:
        if disc.disctype in ["dvd", "bluray"]:
            logname = slugify(disc.videotitle) + ".log"
        else:
            logname = slugify(disc.label) + ".log"

    newlog = logger(logname)
    os.rename(oldlog, newlog)

    return newlog

def slugify(s):
    """
    Simplifies ugly strings into something URL-friendly.
    >>> print slugify("[Some] _ Article's Title--")
    some-articles-title
    """

    # "[Some] _ Article's Title--"
    # "[some] _ article's title--"
    s = s.lower()

    # "[some] _ article's_title--"
    # "[some]___article's_title__"
    for c in [' ', '-', '.', '/']:
        s = s.replace(c, '_')

    # "[some]___article's_title__"
    # "some___articles_title__"
    s = re.sub('\W', '', s)

    # "some___articles_title__"
    # "some   articles title  "
    s = s.replace('_', ' ')

    # "some   articles title  "
    # "some articles title "
    s = re.sub('\s+', ' ', s)

    # "some articles title "
    # "some articles title"
    s = s.strip()

    # "some articles title"
    # "some-articles-title"
    s = s.replace(' ', '-')

    return s


def cleanuplogs(logpath, loglife):
    """Delete all log files older than x days\n
    logpath = path of log files\n
    loglife = days to let logs live\n

    """

    now = time.time()
    logging.info("Looking for log files older than " + str(loglife) + " days old.")

    for filename in os.listdir(logpath):
        fullname = os.path.join(logpath, filename)
        if fullname.endswith(".log"):
            if os.stat(fullname).st_mtime < now - loglife * 86400:
                logging.info("Deleting log file: " + filename)
                os.remove(fullname)
