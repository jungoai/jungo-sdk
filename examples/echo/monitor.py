from time                   import sleep
from jungo_sdk              import Endpoint, JNodeConfig, Monitor, Uid, WorkerWeight, RpcClient
from jungo_sdk.node         import MonitorConfig
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

def get_client(endpoint: Endpoint, cash: dict[Endpoint, RpcClientImpl]) -> RpcClientImpl:
    bt.logging.debug(f"get client: {endpoint}, cash: {cash}")
    client = cash.get(endpoint)
    if not client is None: 
        return client
    else:
        ip   = endpoint.ip_str()
        port = endpoint.port
        bt.logging.debug(f"creating rpc client: ip: {ip}, port: {port}")
        rpc_ = RpcClientImpl(url=f"http://{ip}:{port}/jsonrpc")

        cash[endpoint] = rpc_

        return rpc_

def config_from_args():
    """
    Returns the configuration object specific to this miner or validator after adding relevant arguments.
    """
    parser = argparse.ArgumentParser()
    bt.wallet.add_args(parser)
    bt.subtensor.add_args(parser)
    bt.logging.add_args(parser)
    bt.axon.add_args(parser)

    bt_conf = bt.config(parser)

    parser.add_argument("--netuid", type=int, help="netuid", required=True)
    parser.add_argument("--fast_blocks", action="store_true", help="netuid")

    args = parser.parse_args()

    inner = JNodeConfig(
        bt_conf,
        args.netuid
    )

    print("debug: fast_blocks:", args.fast_blocks)

    return MonitorConfig(inner, args.fast_blocks)

def main():
    config      = config_from_args()
    monitor     = Monitor(config)
    tempo_sec   = monitor.tempo().second()
    ccash       = {}

    def set_weight(endpoint: Endpoint, uid: Uid) -> tuple[Uid, WorkerWeight]:
        bt.logging.debug(f"endpoint: {endpoint}, uid: {uid}")
        client = get_client(endpoint, ccash)
        pong   = client.ping()

        if pong == "pong"   : return (uid, 1)
        else                : return (uid, 0)

    while True:
        monitor.set_weights_with(set_weight)
        sleep(tempo_sec)

if __name__ == "__main__":
    main()
