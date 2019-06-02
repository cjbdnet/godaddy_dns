
import os
import argparse

import sys
import logging
import time
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pprint import pformat

import traceback

from godaddypy import Client,Account

import requests
import json

def main(arguments, logger):
    """Main function of the 'Update Godaddy DNS' script"""
    try:
        
        
        record_type = 'A'
        key = arguments.key
        secret = arguments.secret
        domainname = arguments.domainname
        record_names = arguments.record_names
        
        external_ip = get_external_ip(logger)
        if not external_ip:
            logger.error("Invalid external IP Adress found: '{}'. Exiting...")
            return
        else:
            logger.info("External IP Adress found: '{}'".format(external_ip))

        logger.info("Updating domainname : '{}'".format(domainname))
        logger.info("Updating DNS records of type : '{}'".format(record_type))
        logger.info("Updating DNS records names : '{}'".format(record_names))

        records = [x.strip() for x in record_names.split(",")]
        for record_name in records:
            result = update_dns_record(domain=domainname, record_type=record_type, record_name=record_name, ip_address=external_ip, api_key=key, api_secret=secret, logger=logger)
            

        
    except Exception as e:
        logger.error("DNS record update failed with unexpected error!: {0}".format(traceback.format_exc()))

def get_external_ip(logger):

    retry_unless = [200]
    sleep_between_retries = 2
    max_retry_count = 5

    request = lambda : requests.request('GET', 'http://myip.dnsomatic.com')
    response = retry_request_unless(request, retry_unless, sleep_between_retries, max_retry_count, logger)
    if(response.status_code is requests.codes.ok):
        return response.text

    return None

def retry_request_unless(request, retry_unless, sleep_between_retries, max_retry_count, logger):
    
    for retry_count in range(max_retry_count):
        
        if(retry_count > 0):
            logger.info("Retry count : {}".format(retry_count))
            
        response = request()
        if(response.status_code in retry_unless):
            return response
        else:
            logger.info("Request returned status code : '{}' . Sleeping for {} seconds".format(response.status_code, sleep_between_retries ))
            time.sleep(sleep_between_retries)

    return response

def update_dns_record(domain, record_type, record_name, ip_address, api_key, api_secret, logger):
    
    userAccount = Account(api_key=api_key, api_secret=api_secret)
    userClient = Client(userAccount)

    records = userClient.get_records(domain, record_type=record_type, name=record_name)
    
    # dudes = [x["name"] for x in records_of_type_a]
    
    if not records:
        logger.error("No {} / {} record found to update.".format(record_type, record_name))
        return

    for record in records:
        logger.info("Updating record with name '{}'".format(record["name"]))
        result = userClient.update_record_ip(ip_address, domain, name=record["name"], record_type=record_type)
        logger.info("Updated '{}' with result : {}".format(record["name"], result))

def setupLogging(logDirectory, logfilename, verbose,loggername=__name__):
    """
    Set up the logging
    """

    logLevel = logging.DEBUG if verbose else logging.INFO

    log_dir_path = os.path.abspath(logDirectory)

    # if the logs folder does not exist, create it
    if(not os.path.exists(log_dir_path)):
        os.mkdir(log_dir_path)

    log_path = os.path.join(log_dir_path, logfilename)

    logger = logging.getLogger(loggername)
    logger.setLevel(logLevel)

    # create a formatter, to use for the handlers
    formatter = logging.Formatter('[%(asctime)s] - [%(levelname)s] - [%(name)s] - %(message)s')
    formatter.converter = time.gmtime

    #logging to console
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)

    #Logging to file, rotate at midnight
    fileHandler = TimedRotatingFileHandler(log_path, when="midnight")
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)

    return logger


if __name__  == '__main__':
    """
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--domainname", help="The domainname for which to update the records.", required=True)
    parser.add_argument("--record_names", help="A collection(comma separated string) of record names to set.", required=True)
    parser.add_argument("--key", help="The KEY to the GoDaddy account.", required=True)
    parser.add_argument("--secret", help="The SECRET to the GoDaddy account.", required=True)
    parser.add_argument("--verbose", dest='verbose', help="Specify to enable verbose logging", action='store_true')
    parser.set_defaults(verbose=False)

    args = parser.parse_args()
    filename = os.path.basename(__file__)[:-3]
    logfilename =   filename + "-" + datetime.utcnow().strftime("%Y-%m-%d-%H%M%SZ") + ".log"
    
    logger = setupLogging("logs", logfilename, args.verbose, "GoDaddy_DNS")

    main(args, logger)