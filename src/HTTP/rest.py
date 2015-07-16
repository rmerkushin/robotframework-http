from os import path
from requests import Session

from robot.api import logger
from robot.utils import ConnectionCache
from robot.libraries.BuiltIn import BuiltIn


class REST(object):

    def __init__(self):
        self._builtin = BuiltIn()
        self._cache = ConnectionCache()

    def create_rest_session(self, alias, headers=None, auth=None, verify=False, cert=None):
        """
        Creates REST session with specified alias.

        Arguments:
        | alias | session alias |
        | headers | custom headers for all requests |
        | auth | basic auth |
        | verify | SSL verification |
        | cert | path to SSL certificate file |

        Example usage:
        | ${headers} | Create Dictionary | Content-Type | application/json |
        | @{service_basic_auth} | Set Variable | username | password |
        | Create Rest Session | session_alias | headers=${headers} | auth=${service_basic_auth} | verify=False |
        """
        session = Session()
        if headers:
            session.headers.update(headers)
        if auth:
            session.auth = tuple(auth)
        session.verify = self._builtin.convert_to_boolean(verify)
        session.cert = cert
        self._cache.register(session, alias)

    def head(self, alias, url, params=None, headers=None, cookies=None, timeout=10):
        """
        Sends HEAD request.

        Arguments:
        | alias | session alias |
        | url | service url |
        | params | request parameters |
        | headers | custom headers for request, rewrites session headers |
        | cookies | custom request cookies |
        | timeout | response timeout in seconds, raise exception on request timeout |

        Example usage:
        | ${payload} | Create Dictionary | param1 | value1 | param2 | value2 |
        | ${cookies} | Create Dictionary | sessionid | session12345 |
        | ${response} | Head | session_alias | http://localhost/service | params=${payload} | cookies=${cookies} | timeout=5 |
        """
        logger.info("Sending HEAD request to: '%s', session: '%s'" % (url, alias))
        session = self._cache.switch(alias)
        response = session.head(url, params=params, headers=headers, cookies=cookies, timeout=int(timeout))
        return {"status": response.status_code, "headers": response.headers}

    def get(self, alias, url, params=None, headers=None, cookies=None, timeout=10):
        """
        Sends GET request. See arguments description in `Head` keyword.
        """
        logger.info("Sending GET request to: '%s', session: '%s'" % (url, alias))
        session = self._cache.switch(alias)
        response = session.get(url, params=params, headers=headers, cookies=cookies, timeout=int(timeout))
        try:
            return {"status": response.status_code, "headers": response.headers, "body": response.json()}
        except ValueError:
            return {"status": response.status_code, "headers": response.headers, "body": response.content}

    def post(self, alias, url, headers=None, cookies=None, data=None, files=None, timeout=10):
        """
        Sends POST request.

        Arguments:
        | alias | session alias |
        | url | service url |
        | headers | custom headers for request, rewrites session headers |
        | cookies | custom request cookies |
        | data | dictionary, bytes, or file-like object to send in the body of the request |
        | files | dictionary of 'name': file-like-objects (or {'name': ('filename', fileobj)}) for multipart encoding upload |
        | timeout | response timeout in seconds, raise exception on request timeout |

        Example usage:
        | @{files} | Set Variable | path_to_file_1 | path_to_file_2 |
        | ${mpe_files} | Convert To Multipart Encoded Files | ${files} |
        | ${payload} | Set Variable | {"id": "34","doc_type": "history"} |
        | ${response} | Post | service_alias | http://localhost/service | data=${payload} |
        | ${response} | Post | service_alias | http://localhost/service | files=${mpe_files} |
        """
        logger.info("Sending POST request to: '%s', session: '%s'" % (url, alias))
        session = self._cache.switch(alias)
        response = session.post(url, headers=headers, cookies=cookies, data=data.encode("utf-8"), files=files,
                                timeout=int(timeout))
        try:
            return {"status": response.status_code, "headers": response.headers, "body": response.json()}
        except ValueError:
            return {"status": response.status_code, "headers": response.headers, "body": response.content}

    def put(self, alias, url, headers=None, data=None, cookies=None, timeout=10):
        """
        Sends PUT request. See arguments description in `Post` keyword.
        """
        logger.info("Sending PUT request to: '%s', session: '%s'" % (url, alias))
        session = self._cache.switch(alias)
        response = session.put(url, headers=headers, cookies=cookies, data=data.encode("utf-8"), timeout=int(timeout))
        try:
            return {"status": response.status_code, "headers": response.headers, "body": response.json()}
        except ValueError:
            return {"status": response.status_code, "headers": response.headers, "body": response.content}

    def delete(self, alias, url, headers=None, data=None, cookies=None, timeout=10):
        """
        Sends DELETE request. See arguments description in `Post` keyword.
        """
        logger.info("Sending DELETE request to: '%s', session: '%s'" % (url, alias))
        session = self._cache.switch(alias)
        response = session.delete(url, headers=headers, cookies=cookies, data=data.encode("utf-8"),
                                  timeout=int(timeout))
        try:
            return {"status": response.status_code, "headers": response.headers, "body": response.json()}
        except ValueError:
            return {"status": response.status_code, "headers": response.headers, "body": response.content}

    def close_all_sessions(self):
        """
        Closes all created sessions.
        """
        self._cache.empty_cache()

    @staticmethod
    def convert_to_multipart_encoded_files(files):
        """
        Converts list of files to multipart encoded files.

        Example usage:
        | @{files} | Set Variable | path_to_file_1 | path_to_file_2 |
        | ${mpe_files} | Convert To Multipart Encoded Files | ${files} |
        """
        mpe_files = []
        for f in files:
            form_field_name = f[0]
            file_name = path.basename(f[1])
            file_path = f[1]
            mime_type = f[2]
            mpe_files.append((form_field_name, (file_name, open(file_path, "rb"), mime_type)))
        return mpe_files
