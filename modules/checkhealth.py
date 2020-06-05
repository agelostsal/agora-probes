#!/usr/bin/env python

import sys
import argparse
import requests
from NagiosResponse import NagiosResponse

TIMEOUT = 180


class AgoraHealthCheck:

    SERVICES = '/api/v2/services'
    EXT_SERVICES = '/api/v2/ext-services'
    LOGIN = '/api/v2/auth/login/'

    def __init__(self, args=sys.argv[1:]):
        self.args = parse_arguments(args)
        self.verify_ssl = not self.args.ignore_ssl
        self.nagios = NagiosResponse("Agora is up.")

    def check_endpoint(self, endpointExtension='', checkJSON=False):
        try:
            endpoint = self.args.url + endpointExtension
            r = requests.get(endpoint, verify=self.verify_ssl,
                             timeout=self.args.timeout)
            r.raise_for_status()
            if checkJSON and not len(r.json()):
                self.nagios.writeCriticalMessage("No services found at " + endpoint)
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code
            self.nagios.writeCriticalMessage("Invalid response code: " + str(code))
        except requests.exceptions.SSLError as e:
            self.nagios.writeCriticalMessage("SSL Error")
        except requests.exceptions.RequestException as e:
            self.nagios.writeCriticalMessage("Cannot connect to endpoint " + endpoint)
        except ValueError:
            self.nagios.writeCriticalMessage("Malformed JSON at " + endpoint)

    def login(self, loginEndpoint):
        try:
            payload = {
                        'username': self.args.username,
                        'password': self.args.password,
            }
            r = requests.post(self.args.url + loginEndpoint, data=payload,
                    verify=self.verify_ssl)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code
            if code in [400, 401]:
                self.nagios.writeCriticalMessage("Cannot login")
            else:
                self.nagios.writeCriticalMessage("Invalid response code: " + str(code))
        except requests.exceptions.RequestException as e:
            self.nagios.writeCriticalMessage("Cannot connect to endpoint " + endpoint)

    def run(self):
        self.check_endpoint()
        self.check_endpoint(self.SERVICES, checkJSON=True)
        self.check_endpoint(self.EXT_SERVICES, checkJSON=True)
        if self.args.username and self.args.password:
            self.login(self.LOGIN)
        self.nagios.printAndExit()


def parse_arguments(args):
    parser = argparse.ArgumentParser(description="Nagios Probe for Agora")
    parser.add_argument('-U', '--url', dest='url', required=True,
                        type=str, help='Agora\'s url')
    parser.add_argument('-v', '--verbose', dest='verbose',
                        action='store_true', help='verbose output')
    parser.add_argument('-t', '--timeout', dest='timeout', type=int,
                        default=TIMEOUT,
                        help='timeout for requests, default=' + str(TIMEOUT))
    parser.add_argument('-u', '--username', dest='username', type=str,
                        help='username')
    parser.add_argument('-p', '--password', dest='password', type=str,
                        help='password')
    parser.add_argument('-i', '--insecure', dest='ignore_ssl',
                        action='store_true', default=False,
                        help='ignore SSL errors')
    return parser.parse_args(args)


if __name__ == "__main__":
    check = AgoraHealthCheck()
    check.run()
