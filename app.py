
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
        
        key = arguments.key
        secret = arguments.secret
        hostname = arguments.hostname
        
        external_ip = get_external_ip(logger)
        if not external_ip:
            logger.error("Invalid external IP Adress found: '{}'. Exiting...")
            return
        else:
            logger.info("External IP Adress found: '{}'".format(external_ip))

        result = update_dns_a_record(domain=hostname, ip_address=external_ip, api_key=key, api_secret=secret, logger=logger)
        logger.info('Update DNS record result: {}'.format(result))
        
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

def update_dns_a_record(domain, ip_address, api_key, api_secret, logger):
    
    userAccount = Account(api_key=api_key, api_secret=api_secret)
    userClient = Client(userAccount)

    record_type = 'A'
    records_of_type_a = userClient.get_records(domain, record_type=record_type)
    
    # dudes = [x["name"] for x in records_of_type_a]
    
    if not records_of_type_a:
        logger.error("No {} record found to update".format(record_type))
        return

    for a_record in records_of_type_a:
        logger.info("Updating record with name '{}'".format(a_record["name"]))
        result = userClient.update_record_ip(ip_address, domain, name=a_record["name"], record_type=record_type)

        logger.info("Updated with result : {}".format(result))

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
    parser.add_argument("--hostname", help="The hostname for wich to set the 'A' value.", required=False)
    parser.add_argument("--key", help="The KEY to the GoDaddy account.", required=False)
    parser.add_argument("--secret", help="The SECRET to the GoDaddy account.", required=False)
    parser.add_argument("--verbose", dest='verbose', help="Specify to enable verbose logging", action='store_true')
    parser.set_defaults(verbose=False)

    args = parser.parse_args()
    filename = os.path.basename(__file__)[:-3]
    logfilename =   filename + "-" + datetime.utcnow().strftime("%Y-%m-%d-%H%M%SZ") + ".log"
    
    logger = setupLogging("logs", logfilename, args.verbose, "GoDaddy_DNS")

    main(args, logger)