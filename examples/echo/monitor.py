from time                   import sleep
from jungo_sdk              import Endpoint, Uid, WorkerWeight, RpcClient
from jungo_sdk.node         import mk_monitor_from_args
from jungo_sdk.utils        import cfn
from examples.echo.api      import PingApi

import bittensor as bt
import argparse


class RpcClientImpl(RpcClient, PingApi):
    def __init__(self, url) -> None:
        super().__init__()
        self._url = url

    def url(self) -> str:
        return self._url

    def ping(self) -> str:
        return self.creq(cfn(), locals())

    def echo(self, msg: str) -> str:
        return self.creq(cfn(), locals())

def get_client(endpoint: Endpoint, cache: dict[Endpoint, RpcClientImpl]) -> RpcClientImpl:
    bt.logging.debug(f"get client: {endpoint}, cache: {cache}")
    client = cache.get(endpoint)
    if not client is None: 
        return client
    else:
        ip   = endpoint.ip_str()
        port = endpoint.port
        bt.logging.debug(f"creating rpc client: ip: {ip}, port: {port}")
        rpc_ = RpcClientImpl(url=f"http://{ip}:{port}/jsonrpc")

        cache[endpoint] = rpc_

        return rpc_

def main():
    parser      = argparse.ArgumentParser()
    monitor     = mk_monitor_from_args(parser)
    tempo_sec   = monitor.tempo().second()
    ccache      = {}

    def set_weight(endpoint: Endpoint, uid: Uid) -> tuple[Uid, WorkerWeight]:
        bt.logging.debug(f"endpoint: {endpoint}, uid: {uid}")
        client = get_client(endpoint, ccache)
        pong   = client.ping()

        if pong == "pong"   : return (uid, 1)
        else                : return (uid, 0)

    while True:
        monitor.set_weights_with(set_weight)
        sleep(tempo_sec)

if __name__ == "__main__":
    main()
