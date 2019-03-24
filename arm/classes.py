import pyudev
import os
import logging
import fcntl

class Disc(object):
    """
    A class representing an optical disc


    Attributes:
        devpath
        mountpoint
        videotitle
        videoyear
        videotype
        hasnicetitle
        label
        disctype
        errors

    Methods:
        __init__(self, devpath)
        __str__(self)
        parse_udev(self)
        eject(self)
        drive_status(self)
    """

    def __init__(self, devpath):
        """
        Constructor; returns a disc object

        Parameters:
            devpath: path to the disc

        Return value: None
        """
        self.devpath = devpath
        self.mountpoint = "/mnt" + devpath
        self.videotitle = ""
        self.videoyear = ""
        self.videotype = ""
        self.hasnicetitle = False
        self.label = ""
        self.disctype = ""
        self.errors = []
        self.parse_udev()

    def __str__(self):
        """
        Returns a string representing the disc object

        Parameters:
        None

        Return value: None
        """

        s = self.__class__.__name__ + ": "
        for attr, value in self.__dict__.items():
            s = s + "(" + str(attr) + "=" + str(value) + ") "

        return s

    def parse_udev(self):
        """
        Parse udev for properties of current disc

        Parameters:
        None

        Return Value: None
        """

        logging.debug("**** Logging udev attributes ****")
        context = pyudev.Context()
        device = pyudev.Devices.from_device_file(context, self.devpath)
        self.disctype = "unknown"

        for key, value in device.items():
            logging.debug(key + ":" + value)
            if key == "ID_FS_LABEL":
                self.label = value
                if value == "iso9660":
                    self.disctype = "data"
            elif key == "ID_CDROM_MEDIA_BD":
                self.disctype = "bluray"
            elif key == "ID_CDROM_MEDIA_DVD":
                self.disctype = "dvd"
            elif key == "ID_CDROM_MEDIA_TRACK_COUNT_AUDIO":
                self.disctype = "music"
            else:
                pass
        logging.debug("**** End udev attributes ****")

    def eject(self):
        """
        Ejects disc if tray isn't already open

        Parameters:
        None

        Return value: None
        """

        cmd = "eject " + self.devpath
        if self.drive_status() != 2:
            logging.debug("Ejecting using cmd: " + cmd)
            os.system(cmd)
        else:
            logging.debug("Tray for drive " + self.devpath + " is already open. Skipping eject.")

    def drive_status(self):
        """
        Returns the optical drive's status from ioctl

        Statuses:
        1 = no disk in tray
        2 = tray open
        3 = reading tray
        4 = disk in tray

        Parameters:
        devpath: the path to the device

        Return value: None
        """

        fd = os.open(self.devpath, os.O_RDONLY | os.O_NONBLOCK)
        rv = fcntl.ioctl(fd, 0x5326)
        os.close(fd)
        return rv
