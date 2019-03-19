#!/usr/bin/python3

import sys # noqa # pylint: disable=unused-import
import argparse
import urllib
import os # noqa # pylint: disable=unused-import
import xmltodict # noqa # pylint: disable=unused-import
import logging
import json
import re

from config import cfg


def entry():
    """ Entry to program, parses arguments"""
    parser = argparse.ArgumentParser(description='Get type of dvd--movie or tv series')
    parser.add_argument('-t', '--title', help='Title', required=True)
    # parser.add_argument('-k', '--key', help='API_Key', dest='omdb_api_key', required=True)

    return parser.parse_args()


def getdvdtype(disc):
    """ Queries OMDbapi.org for title information and parses if it's a movie
        or a tv series """

    dvd_title = disc.videotitle
    # needs_new_year = False
    omdb_api_key = cfg['OMDB_API_KEY']

    logging.debug("Title: " + dvd_title)

    dvd_title_clean = cleanupstring(dvd_title)

    logging.debug("Calling webservice with title: " + dvd_title_clean)
    dvd_type, dvd_year = callwebservice(omdb_api_key, dvd_title_clean, "")
    logging.debug("dvd_type: " + dvd_type)

    # handle failures
    # this is a little kludgy, but it kind of works...
    if (dvd_type == "fail"):

        # second see if there is a hyphen and split it
        if dvd_title.find("-") > -1:
            dvd_title_slice = dvd_title[:dvd_title.find("-")]
            dvd_title_slice = cleanupstring(dvd_title_slice)
            logging.debug("Trying title: " + dvd_title_slice)
            dvd_type, dvd_year = callwebservice(omdb_api_key, dvd_title_slice)
            logging.debug("dvd_type: " + dvd_type)

        # if still failing, then try slicing off the last word in a loop
        while dvd_type == "fail" and dvd_title_clean.count('+') > 0:
            dvd_title_clean = dvd_title_clean.rsplit('+', 1)[0]
            logging.debug("Trying title: " + dvd_title_clean)
            dvd_type, dvd_year = callwebservice(omdb_api_key, dvd_title_clean)
            logging.debug("dvd_type: " + dvd_type)

    return (dvd_type, dvd_year)


def cleanupstring(string):
    # clean up title string to pass to OMDbapi.org
    string = string.strip()
    return re.sub('[_ ]', "+", string)


def callwebservice(omdb_api_key, dvd_title, year=""):
    """ Queries OMDbapi.org for title information and parses if it's a movie
        or a tv series """

    logging.debug("***Calling webservice with Title: " + dvd_title + " and Year: " + year)
    try:
        strurl = "http://www.omdbapi.com/?t={1}&y={2}&plot=short&r=json&apikey={0}".format(omdb_api_key, dvd_title, year)
        logging.debug("http://www.omdbapi.com/?t={1}&y={2}&plot=short&r=json&apikey={0}".format("key_hidden", dvd_title, year))
        dvd_title_info_json = urllib.request.urlopen(strurl).read()
    except Exception:
        logging.debug("Webservice failed")
        return "fail", None
    else:
        doc = json.loads(dvd_title_info_json.decode())
        if doc['Response'] == "False":
            logging.debug("Webservice failed with error: " + doc['Error'])
            return "fail", None
        else:
            media_type = doc['Type']
            year = re.sub(r'[^\x00-\x7f]',r'', doc['Year'])
            logging.debug("Webservice successful.  Document returned is: " + json.dumps(doc))
            return (media_type, year)


def main(disc):

    logging.debug("Entering getvideotype module")
    dvd_type, year = getdvdtype(disc)
    return(dvd_type, year)
