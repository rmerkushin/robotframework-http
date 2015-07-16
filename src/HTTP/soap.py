from os import path
from requests import Session
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

from robot.api import logger
from robot.libraries.XML import XML
from robot.utils import ConnectionCache
from robot.libraries.BuiltIn import BuiltIn


class SOAPClient(object):

    def __init__(self, session, wsdl, endpoint):
        self.session = session
        self.wsdl = wsdl
        self.endpoint = endpoint


class SOAP(object):

    def __init__(self):
        self._xml = XML()
        self._builtin = BuiltIn()
        self._cache = ConnectionCache()

    def create_soap_client(self, alias, wsdl=None, endpoint=None):
        """
        Creates SOAP client with specified alias.

        Arguments:
        | alias | client alias |
        | wsdl | path or url to service wsdl |
        | endpoint | url for service under test |

        Example usage:
        | Create Soap Client | client_alias | wsdl=path_to_wsdl${/}ws_example.wsdl | endpoint=http://localhost:8080/ |
        """
        session = Session()
        session.verify = False
        if wsdl:
            wsdl = self._get_wsdl(session, wsdl)
        client = SOAPClient(session, wsdl, endpoint)
        self._cache.register(client, alias)

    def call_soap_method(self, alias, name, message, replace=None, endpoint=None, expect_fault=False, xml=True):
        """
        Call SOAP method.

        Arguments:
        | alias | client alias |
        | name | method name |
        | message | path to SOAP message or SOAP message |
        | replace | dictionary of old_value: new_value pairs for replace in message |
        | endpoint | url for service under test, rewrites client endpoint |
        | expect_fault | if True, not raise exception when receive fault |
        | xml | return type, if True - return xml object (XML library format), False - string |

        Example usage:
        | ${replace} | Create Dictionary | _id_ | 64 |
        | ${response} | Call Soap Method | client_alias | getUserName | path_to_soap_message${/}example.xml | replace=${replace} | expect_fault=False | xml=True |
        | Element Should Exist | ${response} | .//{http://www.example.ru/example}requestResult |
        """
        client = self._cache.switch(alias)
        if endpoint:
            client.endpoint = endpoint
        try:
            ET.fromstring(message)
        except ET.ParseError:
            if not path.isfile(message):
                raise IOError("File not found or message is not well-formed" % message)
            message = open(message, mode="r", encoding="utf-8").read()
        if replace:
            for k, v in replace.items():
                message = message.replace(k, v)
        status_code, response = self._call(client, name, message)
        expect_fault = self._builtin.convert_to_boolean(expect_fault)
        is_fault = self._is_fault(status_code)
        if is_fault and not expect_fault:
            raise AssertionError("The server did not raise a fault")
        elif expect_fault and not is_fault:
            raise AssertionError("The server not raise a fault")
        if self._builtin.convert_to_boolean(xml):
            return self._xml.parse_xml(response, keep_clark_notation=True)
        else:
            return response

    @staticmethod
    def _get_wsdl(session, url_or_path):
        if not urlparse(url_or_path).scheme:
            if not path.isfile(url_or_path):
                raise IOError("File '%s' not found" % url_or_path)
            wsdl = open(url_or_path, mode="r", encoding="utf-8").read()
        else:
            response = session.get(url_or_path)
            if response.status_code != 200:
                raise ConnectionError("Server not found or resource '%s' is not available" % url_or_path)
            wsdl = response.content.decode("utf-8")
        return wsdl

    @staticmethod
    def _is_fault(status_code):
        if status_code == 200:
            return False
        else:
            return True

    def _get_soap_action(self, wsdl, name):
        root = self._xml.parse_xml(wsdl)
        xpath = ".//*[@name='%s']/operation" % name
        return self._xml.get_element_attribute(root, "soapAction", xpath=xpath)

    def _call(self, client, name, message):
        if client.wsdl:
            action = self._get_soap_action(client.wsdl, name)
        else:
            action = ""
        headers = {"Accept-Encoding": "gzip,deflate", "Content-Type": "text/xml;charset=UTF-8",
                   "Connection": "Keep-Alive", "SOAPAction": action}
        logger.info("Execution '%s' soap method" % name)
        response = client.session.post(client.endpoint, headers=headers, data=message.encode("utf-8"))
        return response.status_code, response.content.decode("utf-8")
