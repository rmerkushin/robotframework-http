# rmerkushin@gmail.com

from .soap import SOAP
from .rest import REST
from .version import VERSION

__version__ = VERSION


class HTTP(SOAP, REST):

    """
    HTTP is REST and SOAP web-service testing library for Robot Framework (Python 3 version).

    = REST service testing example =

    | ${headers} | Create Dictionary | Content-Type | application/json |
    | Create Rest Session | session_alias | headers=${headers} | auth=${service_basic_auth} |
    | ${payload} | Set Variable | {"id": "34","doc_type": "history"} |
    | ${response} | Post | session_alias | http://localhost:8080/restService | data=${payload} |
    | Log Many | ${response['status']} | ${response['headers']} | ${response['body']} |

    = SOAP service testing example =

    | Create Soap Client | client_alias | wsdl=path_to_wsdl${/}ws_example.wsdl | endpoint=http://localhost:8080/ |
    | ${response} | Call Soap Method | client_alias | getUserName | path_to_soap_message${/}example.xml |
    | Element Should Exist | ${response} | .//{http://www.example.ru/example}requestResult |
    """

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
