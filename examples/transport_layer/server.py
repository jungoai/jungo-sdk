from typing                         import Callable
from jungo_sdk                      import RpcServer, serve
from examples.transport_layer.api   import Block, ExampleApi


class Server(RpcServer, ExampleApi):
    def rpcs(self) -> list[Callable]:
        return [
            self.eth_getBlockByHash,
            self.eth_getBlockByNumber,
            self.eth_getBalance,
        ]

    def eth_getBlockByHash(self, block_hash, get_full_tx) -> Block | None:
        print("eth_getBlockByHash called")
        return Block(
            number              = None,
            hash                = None,
            parent_hash         = "0x01",
            nonce               = "0x02",
            sha3_uncles         = "mySha",
            logs_bloom          = None,
            transactions_root   = "0x03",
            state_root          = "0x04",
            timestamp           = "0x05",
            size                = "0x06",
            transactions        = ["0x07", "0x08"]
        )

    def eth_getBlockByNumber(self, block_number, get_full_tx) -> Block | None:
        print("eth_getBlockByNumber called")
        return None

    def eth_getBalance(self, address):
        print("eth_getBalance called")
        return "0x00"

def main():
    server = Server()
    serve('localhost', 4000, server.rpcs())

if __name__ == '__main__':
    main()
