from typing             import Callable
from jungo_sdk          import JConfig, NodeError, RpcServer, Worker, serve_worker
from examples.echo.api  import PingApi

import bittensor as bt
import traceback
import argparse


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
    return JConfig(
        bt_conf = bt.config(parser),
        netuid  = 101 # TODO
    )

def main():
    config = config_from_args()

    try:
        server = RpcServerImpl()
        # read ip:port from arg/config
        worker = Worker("192.168.55.53", 4000, config)
        serve_worker(worker, server)
    except NodeError as e:
        bt.logging.error("NodeError: " + str(e))
        traceback.print_exc()
    except Exception as e:
        bt.logging.error("Internal error: " + str(e))
        traceback.print_exc()

if __name__ == '__main__':
    main()
