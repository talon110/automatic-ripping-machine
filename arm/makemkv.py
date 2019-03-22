#!/usr/bin/python3

import os
import logging
import subprocess
import shlex
import utils

from config import cfg


def makemkv(logfile, disc):
    """
    Rip Blurays with MakeMKV

    Parameters:
    logfile: location of logfile to redirect MakeMKV logs to
    disc: disc object

    Return value: path to ripped files or None if the operation fails
    """

    logging.info("Starting MakeMKV rip. Method is " + cfg['RIPMETHOD'])

    rawpath = utils.make_dir(os.path.join(cfg['RAWPATH'], disc.videotitle + " (" + disc.videoyear + ")"))
    logging.info("Destination is " + rawpath)

    try:
        rip_disc(disc, rawpath, logfile)
    except:
        err = "Call to makemkv failed."
        logging.error(err)
        return None

    logging.info("Exiting MakeMKV processing with return value of: " + rawpath)
    return(rawpath)

def rip_disc(disc, output_dir, logfile):
    """
    Rips disc using MakeMKV

    Parameters:
    output_dir: path to output directory
    logfile: path to intended logfile

    Return value: True on successful run or False otherwise
    """
    try:
        mdisc = get_disc_num(disc)
    except:
        return False

    if cfg['RIPMETHOD'] == "backup" and disc.disctype == "bluray":
        cmd = 'makemkvcon backup --decrypt {0} -r disc:{1} {2}>> {3}'.format(
            cfg['MKV_ARGS'],
            mdisc.strip(),
            shlex.quote(output_dir),
            logfile
        )
        logging.info("Backup disc")
        logging.debug("Backing up with the following command: " + cmd)
    elif cfg['RIPMETHOD'] == "mkv" or disc.disctype == "dvd":
        cmd = 'makemkvcon mkv {0} -r dev:{1} all {2} --minlength={3}>> {4}'.format(
            cfg['MKV_ARGS'],
            disc.devpath,
            shlex.quote(output_dir),
            cfg['MINLENGTH'],
            logfile
        )
        logging.info("Ripping disc")
        logging.debug("Ripping with the following command: " + cmd)
    else:
        logging.info("I'm confused what to do....  Passing on MakeMKV")

    try:
        mkv = subprocess.run(
            cmd,
            shell=True
        )
        logging.debug("The exit code for MakeMKV is: " + str(mkv.returncode))
    except subprocess.CalledProcessError as mkv_error:
        err = "Call to MakeMKV failed with code: " + str(mkv_error.returncode) + "(" + str(mkv_error.output) + ")"
        logging.error(err)
        return False
    return True

def get_disc_num(disc):
    """
    Gets the disc number as determined by makemkvcon

    Parameters:
    disc: disc object

    Return value: the MakeMKV disc number
    """
    logging.debug("Getting MakeMKV disc number")
    cmd = 'makemkvcon -r info disc:9999  |grep {0} |grep -oP \'(?<=:).*?(?=,)\''.format(
                disc.devpath
    )

    try:
        mdisc = subprocess.check_output(
            cmd,
            shell=True
        ).decode("utf-8")
        logging.info("MakeMKV disc number: " + mdisc.strip())
        return mdisc
    except subprocess.CalledProcessError as mdisc_error:
        err = "Call to makemkv failed with code: " + str(mdisc_error.returncode) + "(" + str(mdisc_error.output) + ")"
        logging.error(err)
