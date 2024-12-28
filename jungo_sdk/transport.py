import json
import requests

from dataclasses        import dataclass
from dataclasses        import dataclass
from abc                import ABC, abstractmethod
from typing             import Any, Callable
from jsonrpc            import JSONRPCResponseManager, dispatcher
from dataclasses        import dataclass
from werkzeug.serving   import run_simple
from werkzeug.wrappers  import Request, Response

from jungo_sdk.utils    import from_json, lmap, to_json, unOpt

#------------------------------------------------------------------------------
#-- Server

class RpcServer(ABC):
    @abstractmethod
    def rpcs(self) -> list[Callable]:
        ...

@dataclass
class JsonRpcResponse:
    json    : str
    mimetype: str

def json_result(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return to_json(result)
    return wrapper

def mk_handler(fs: list[Callable]) -> Callable[[str], JsonRpcResponse]:
    for f in fs:
        dispatcher[f.__name__] = json_result(f)

    return lambda req: JsonRpcResponse(
        json=unOpt(JSONRPCResponseManager.handle(req.data, dispatcher)).json, # type: ignore
        mimetype='application/json'
    )

def mk_handler_default(fs: list[Callable]):
    handler         = mk_handler(fs)
    into_response   = lambda resp: Response(resp.json, mimetype=resp.mimetype)
    handler_default = lambda req_str: into_response(handler(req_str))

    return Request.application(handler_default)

def serve(hostname: str, port: int, fs: list[Callable]) -> None:
    default_handler = mk_handler_default(fs)
    run_simple(hostname, port, default_handler)

#------------------------------------------------------------------------------
#-- Client

class RpcClient(ABC):
    @abstractmethod
    def url(self) -> str:
        ...

    def client_request(self, function_name: str, local_dict: dict[str, Any]) -> Any:
        return client_request_(self.url(), function_name, list(local_dict.values())[1:])

    def creq(self, function_name: str, local_dict: dict[str, Any]) -> Any:
        """
        Alias for client_request(...)
        """
        return self.client_request(function_name, local_dict)

def client_request_(url: str, method: str , params: list[Any]):
    return from_json(jsonrpc_request(url, method , params)["result"])
    
def jsonrpc_request(url: str, method: str , params: list[Any]):
    se_params   = lmap(to_json, params)
    headers     = {'content-type': 'application/json'}
    payload     = {
        "method": method,
        "params": se_params,
        "jsonrpc": "2.0",
        "id": 0,
    }
    json_payload = json.dumps(payload)
    return requests.post(url, data=json_payload, headers=headers).json()
