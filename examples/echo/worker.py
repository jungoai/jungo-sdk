from typing             import Callable
from jungo_sdk          import NodeError, RpcServer, serve_worker
from examples.echo.api  import PingApi
from jungo_sdk.node     import mk_worker_from_args

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

def main():
    parser = argparse.ArgumentParser()

    try:
        server = RpcServerImpl()
        worker = mk_worker_from_args(parser)
        serve_worker(worker.port, server)
    except NodeError as e:
        bt.logging.error("NodeError: " + str(e))
        traceback.print_exc()
    except Exception as e:
        bt.logging.error("Internal error: " + str(e))
        traceback.print_exc()

if __name__ == '__main__':
    main()
