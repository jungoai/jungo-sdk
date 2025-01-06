from typing             import Callable
from jungo_sdk          import JNodeConfig, NodeError, RpcServer, Worker, serve_worker
from examples.echo.api  import PingApi
from netaddr            import IPAddress

import bittensor as bt
import traceback
import argparse

from jungo_sdk.node import WorkerConfig


class RpcServerImpl(RpcServer, PingApi):
    def rpcs(self) -> list[Callable]:
        return [
            self.ping,
            self.echo,
        ]

    def ping(self) -> str:
        return "pong"

    def echo(self, msg: str) -> str:
        return msg

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
    parser.add_argument("--ip", type=str, help="ip", required=True) # TODO: help
    parser.add_argument("--port", type=int, help="port", required=True) # TODO: help

    args = parser.parse_args()

    inner = JNodeConfig(
        bt_conf,
        args.netuid
    )

    return WorkerConfig(
        inner,
        args.ip,
        args.port # 4000
    )

def main():
    config = config_from_args()

    try:
        server = RpcServerImpl()
        worker = Worker(config)
        serve_worker(worker.port, server)
    except NodeError as e:
        bt.logging.error("NodeError: " + str(e))
        traceback.print_exc()
    except Exception as e:
        bt.logging.error("Internal error: " + str(e))
        traceback.print_exc()

if __name__ == '__main__':
    main()
