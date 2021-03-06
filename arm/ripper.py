import sys
import os
import subprocess
import logging
import handbrake
import makemkv
import utils

from config import cfg


class Ripper(object):
    """
    Class Ripper is an object that takes in a disc and logfile
    and rips the disc using the appropriate programs.

    Attributes:

    Methods:
        __init__(disc, logfile)
        disc_notify(disc)
        rip_dvd(disc, logfile, dest_dir)
        rip_and_transcode(disc, logfile, dest_dir)
        create_output_dirs(disc)
        makemkv_rip(disc, logfile)
        move_raw(mkvoutpath, dest_dir)
        delete_raw(mkvoutpath)
        rip_music(disc, logfile)
        rip_data(disc, datapath, logfile)
        set_permissions(dest_dir)
    """

    def __init__(self, disc, logfile=""):
        self.disc_notify(disc)

        if disc.disctype=="music":
            self.rip_music(disc, logfile)
        elif disc.disctype in ["bluray", "dvd", "data"]:
            dest_dir = self.create_output_dirs(disc)
            logging.info("Processing files to: " + dest_dir)

            if disc.disctype=="bluray" or disc.disctype=="dvd" and not cfg['MAINFEATURE']:
                self.rip_and_transcode(disc, logfile, dest_dir)
            elif disc.disctype=="dvd" and cfg['MAINFEATURE']:
                self.rip_dvd(disc, logfile, dest_dir)
            elif disc.disctype=="data":
                self.rip_data(disc, dest_dir, logfile)
            self.set_permissions(dest_dir)
        else:
            logging.info("Couldn't identify the disc type. Exiting without any action.")

        utils.notify("ARM notification", str(disc.label) + " processing complete.")

    def disc_notify(self, disc):
        """
        Send job start notifications using IFTTT

        Parameters:
        disc: disc object

        Return value: None
        """
        if disc.disctype in ["dvd", "bluray"]:
            utils.notify("ARM notification", "Found disc: " + str(disc.videotitle) + ". Video type is "
                         + str(disc.videotype) + ". Main Feature is " + str(cfg['MAINFEATURE']) + ".")
        elif disc.disctype == "music":
            utils.notify("ARM notification", "Found music CD: " + disc.label + ". Ripping all tracks.")
        elif disc.disctype == "data":
            utils.notify("ARM notification", "Found data disc.  Copying data.")
        else:
            utils.notify("ARM Notification", "Could not identify disc.  Exiting.")
            sys.exit()

    def rip_dvd(self, disc, logfile, dest_dir):
        """
        Rips and transcodes DVDs; uses Handbrake for mainfeature only, or
        MakeMKV for full disc

        Parameters:
        disc: disc object
        logfile: path of intended logfile
        dest_dir: path to directory of final video files

        Return value: None
        """
        hbinpath = str(disc.devpath)
        handbrake.handbrake_mainfeature(hbinpath, dest_dir, logfile, disc)
        disc.eject()

    def rip_and_transcode(self, disc, logfile, dest_dir):
        """
        Rips and transcodes video discs

        Parameters:
        disc: disc object
        logfile: path of intended logfile
        dest_dir: path to directory of final video files

        Return value: None
        """

        mkvoutpath = self.makemkv_rip(disc, logfile)
        disc.eject()
        if cfg['RIPMETHOD'] == "mkv" and cfg['SKIP_TRANSCODE']:
            logging.info("SKIP_TRANSCODE is true.")
            self.move_raw(mkvoutpath, dest_dir)
            self.set_permissions(dest_dir)
        elif disc.disctype == "dvd":
            logging.info("RIPMETHOD is backup.")
            handbrake.handbrake_mkv(mkvoutpath, dest_dir, logfile, disc)
        else:
            handbrake.handbrake_all(mkvoutpath, dest_dir, logfile, disc)

        # report errors if any
        if disc.errors:
            errlist = ', '.join(disc.errors)
            if cfg['NOTIFY_TRANSCODE']:
                utils.notify("ARM notification", str(disc.videotitle) + " processing completed with errors. Title(s) " + errlist + " failed to complete.")
            logging.info("Transcoding completed with errors.  Title(s) " + errlist + " failed to complete.")
        else:
            if cfg['NOTIFY_TRANSCODE']:
                utils.notify("ARM notification", str(disc.videotitle) + " processing complete.")
            logging.info("ARM processing complete")

        # remove raw files, if specified in config
        if cfg['DELRAWFILES']:
            self.delete_raw(mkvoutpath)

    def create_output_dirs(self, disc):
        """
        Creates output directories necessary for rips

        Parameters:
        disc: disc object

        Return value: created output directory
        """

        if disc.disctype in ["dvd", "bluray"]:
            output_dir = utils.make_dir(os.path.join(cfg['MEDIA_DIR'], disc.videotitle + " (" + disc.videoyear + ")"))
        elif disc.disctype == "data":
            output_dir = utils.make_dir(os.path.join(cfg['ARMPATH'], str(disc.label)))
        return output_dir

    def makemkv_rip(self, disc, logfile):
        """
        Run MakeMKV and return the output path to the files generated

        Parameters:
        disc: disc object
        logfile: path to intended logfile

        Return value: path to the directory containing the ripped files
        """

        mkvoutpath = makemkv.makemkv(logfile, disc)
        if mkvoutpath is None:
            logging.error("MakeMKV did not complete successfully.  Exiting ARM!")
            sys.exit()

        if cfg['SKIP_TRANSCODE']:
            logging.debug(str(disc.videotitle + " rip complete."))
            if cfg['NOTIFY_RIP']:
                utils.notify("ARM notification", str(disc.videotitle + " rip complete."))
        else:
            logging.debug(str(disc.videotitle + " rip complete. Starting transcode."))
            if cfg['NOTIFY_RIP']:
                utils.notify("ARM notification", str(disc.videotitle + " rip complete.  Starting transcode."))

        return mkvoutpath

    def move_raw(self, mkvoutpath, dest_dir):
        """
        Moves raw mkv files to dest_dir

        Parameters:
        mkvoutpath: path to raw ripped mkv files
        dest_dir: path to destination directory

        Return value: None
        """

        logging.info("Moving raw mkv files. NOTE: Identified main feature may not be actual main feature")
        files = os.listdir(mkvoutpath)
        if disc.videotype == "movie":
            logging.debug("Videotype: " + disc.videotype)
            # if videotype is movie, then move biggest title to media_dir
            # move the rest of the files to the extras folder

            # find largest filesize
            logging.debug("Finding largest file")
            largest_file_name = ""
            for f in files:
                # initialize largest_file_name
                if largest_file_name == "":
                    largest_file_name = f
                temp_path_f = os.path.join(mkvoutpath, f)
                temp_path_largest = os.path.join(mkvoutpath, largest_file_name)
                # os.path.join(cfg['MEDIA_DIR'] + videotitle)
                # if cur file size > largest_file size
                if(os.stat(temp_path_f).st_size > os.stat(temp_path_largest).st_size):
                    largest_file_name = f
            # largest_file should be largest file
            logging.debug("Largest file is: " + largest_file_name)
            temp_path = os.path.join(mkvoutpath, largest_file_name)
            if(os.stat(temp_path).st_size > 0):  # sanity check for filesize
                for f in files:
                    if(f == largest_file_name):
                        # move main into media_dir
                        utils.move_files(mkvoutpath, f, disc.hasnicetitle, disc.videotitle + " (" + disc.videoyear + ")", True)
                    else:
                        # move others into extras folder
                        if not str(cfg['EXTRAS_SUB']).lower() == "none":
                            utils.move_files(mkvoutpath, f, disc.hasnicetitle, disc.videotitle + " (" + disc.videoyear + ")", False)
                        else:
                            logging.info("Not moving extra: " + f)
            # Clean up
            logging.debug("Attempting to remove extra folder in ARMPATH: " + dest_dir)
            try:
                shutil.rmtree(dest_dir)
                logging.debug("Removed sucessfully: " + dest_dir)
            except Exception:
                logging.debug("Failed to remove: " + dest_dir)
        else:
            # if videotype is not movie, then move everything
            # into 'Unidentified' folder
            logging.debug("Videotype: " + disc.videotype)

            for f in files:
                mkvoutfile = os.path.join(mkvoutpath, f)
                logging.debug("Moving file: " + mkvoutfile + " to: " + mkvoutpath + f)
                shutil.move(mkvoutfile, dest_dir)

    def delete_raw(self, mkvoutpath):
        """
        Removes raw files from temporary folder

        Parameters:
        mkvoutpath: path of raw ripped mkv files

        Return value: None
        """

        try:
            shutil.rmtree(mkvoutpath)
        except UnboundLocalError:
            logging.debug("No raw files found to delete.")
        except OSError:
            logging.debug("No raw files found to delete.")

    def rip_music(self, disc, logfile):
        """
        Rips music CD using abcde with abcde config

        Parameters:
        disc: disc object
        logfile: location of intended logfile

        return value: None
        """

        cmd = 'abcde -d "{0}" >> "{1}" 2>&1'.format(
            disc.devpath,
            logfile
        )

        logging.debug("Sending command: " + cmd)
        try:
            subprocess.check_output(
                cmd,
                shell=True
            ).decode("utf-8")
            logging.info("abcde call successful")
        except subprocess.CalledProcessError as ab_error:
            err = "Call to abcde failed with code: " + str(ab_error.returncode) + "(" + str(ab_error.output) + ")"
            logging.error(err)
            logging.info("Music rip failed.  See previous errors.  Exiting.")
            # sys.exit(err)

        disc.eject()
        utils.notify("ARM notification", "Music CD: " + disc.label + " processing complete.")
        utils.scan_emby()

    def rip_data(self, disc, datapath, logfile):
        """
        Rip data disc using cat on the command line

        Parameters:
        disc: disc object
        datapath: path to copy data to
        logfile: location of intended logfile

        Return value: None
        """

        if (disc.label) == "":
            disc.label = "datadisc"

        filename = os.path.join(datapath, disc.label + ".iso")

        logging.info("Ripping data disc to: " + filename)

        cmd = 'cat "{0}" > "{1}" 2>> {2}'.format(
            disc.devpath,
            filename,
            logfile
        )

        logging.debug("Sending command: " + cmd)

        try:
            subprocess.check_output(
                cmd,
                shell=True
            ).decode("utf-8")
            logging.info("Data rip call successful")
            utils.notify("ARM notification", "Data disc: " + disc.label + " copying complete.")
            return True
        except subprocess.CalledProcessError as dd_error:
            err = "Data rip failed with code: " + str(dd_error.returncode) + "(" + str(dd_error.output) + ")"
            logging.error(err)
            logging.info("Data rip failed.  See previous errors.  Exiting.")

        disc.eject()

    def set_permissions(self, dest_dir):
        """
        Set file to default permissions '777'

        Parameters:
        dest_dir: path of directory to change permissions of

        Return value: None
        """

        if cfg['SET_MEDIA_PERMISSIONS']:
            perm_result = utils.set_permissions(dest_dir)
            logging.info("Permissions set successfully: " + str(perm_result))
