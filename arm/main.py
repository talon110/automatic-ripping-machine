#!/usr/bin/python3

import sys
import argparse
import os
import logging
import time
import datetime
import shutil
import pyudev
import logger
import utils
import makemkv
import handbrake
import identify
import ripper

from config import cfg
from classes import Disc
from getkeys import grabkeys


def entry():
    """ Entry to program, parses arguments"""
    parser = argparse.ArgumentParser(description='Process disc using ARM')
    parser.add_argument('-d', '--devpath', help='Devpath', required=True)

    return parser.parse_args()


def main(disc, logfile):

    """main dvd processing function"""
    logging.info("Entering main function")

    identify.identify(disc, logfile)

    log_arm_params(disc)

    if cfg['HASHEDKEYS']:
        logging.info("Getting MakeMKV hashed keys for UHD rips")
        grabkeys()

    ripper = Ripper(disc, logfile)
    #rip(disc, logfile)
    logging.info("ARM processing complete")


def log_arm_params(disc):
    """log all entry parameters"""

    # log arm parameters
    logging.info("**** Logging ARM variables ****")
    logging.info("devpath: " + str(disc.devpath))
    logging.info("mountpoint: " + str(disc.mountpoint))
    logging.info("videotitle: " + str(disc.videotitle))
    logging.info("videoyear: " + str(disc.videoyear))
    logging.info("videotype: " + str(disc.videotype))
    logging.info("hasnicetitle: " + str(disc.hasnicetitle))
    logging.info("label: " + str(disc.label))
    logging.info("disctype: " + str(disc.disctype))
    logging.info("**** End of ARM variables ****")
    logging.info("**** Logging config parameters ****")
    logging.info("skip_transcode: " + str(cfg['SKIP_TRANSCODE']))
    logging.info("mainfeature: " + str(cfg['MAINFEATURE']))
    logging.info("minlength: " + cfg['MINLENGTH'])
    logging.info("maxlength: " + cfg['MAXLENGTH'])
    logging.info("videotype: " + cfg['VIDEOTYPE'])
    logging.info("ripmethod: " + cfg['RIPMETHOD'])
    logging.info("mkv_args: " + cfg['MKV_ARGS'])
    logging.info("delrawfile: " + str(cfg['DELRAWFILES']))
    logging.info("hb_preset_dvd: " + cfg['HB_PRESET_DVD'])
    logging.info("hb_preset_bd: " + cfg['HB_PRESET_BD'])
    logging.info("hb_args_dvd: " + cfg['HB_ARGS_DVD'])
    logging.info("hb_args_bd: " + cfg['HB_ARGS_BD'])
    logging.info("logfile: " + logfile)
    logging.info("armpath: " + cfg['ARMPATH'])
    logging.info("rawpath: " + cfg['RAWPATH'])
    logging.info("media_dir: " + cfg['MEDIA_DIR'])
    logging.info("extras_sub: " + cfg['EXTRAS_SUB'])
    logging.info("emby_refresh: " + str(cfg['EMBY_REFRESH']))
    logging.info("emby_server: " + cfg['EMBY_SERVER'])
    logging.info("emby_port: " + cfg['EMBY_PORT'])
    logging.info("notify_rip: " + str(cfg['NOTIFY_RIP']))
    logging.info("notify_transcode " + str(cfg['NOTIFY_TRANSCODE']))
    logging.info("**** End of config parameters ****")

if __name__ == "__main__":
    # Start logging immediately to new_disc.log
    logfile = logger.logger("new_disc.log")
    logging.info("Starting ARM processing at " + str(datetime.datetime.now()))

    # Log version number
    with open(os.path.join(cfg['INSTALLPATH'], 'VERSION')) as version_file:
        version = version_file.read().strip()
    logging.info("ARM version: " + version)
    logging.info(("Python version: " + sys.version).replace('\n', ""))

    logger.cleanuplogs(cfg['LOGPATH'], cfg['LOGLIFE'])

    args = entry()
    devpath = args.devpath
    logging.info("DEVPATH provided: " + devpath)

    disc = Disc(devpath)
    logging.info("Disc label: " + disc.label)

    # Move logging to a disc-specific log file and rename the old file
    logfile = logger.disclogging(disc, logfile)
    logging.info("Log file: " + logfile)

    if utils.get_cdrom_status(devpath) != 4:
        logging.info("Drive appears to be empty or is not ready.  Exiting ARM.")
        sys.exit()

    try:
        main(disc, logfile)
    except Exception:
        logging.exception("A fatal error has occured and ARM is exiting.  See traceback below for details.")
        utils.notify("ARM notification", "ARM encountered a fatal error processing " + str(disc.videotitle) + ". Check the logs for more details")
