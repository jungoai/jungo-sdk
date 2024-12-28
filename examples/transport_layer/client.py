from jungo_sdk                      import RpcClient
from jungo_sdk.utils                import cfn, current_func_name
from examples.transport_layer.api   import Block, ExampleApi, EthBalance


class Client(RpcClient, ExampleApi):
    def __init__(self, url) -> None:
        super().__init__()
        self._url = url

    def url(self) -> str:
        return self._url

    def eth_getBlockByHash(self, block_hash, get_full_tx) -> Block | None:
        return self.client_request(current_func_name(), locals())

    def eth_getBlockByNumber(self, block_number, get_full_tx) -> Block | None:
        # creq and cfn are aliases for client_request and current_func_name
        return self.creq(cfn(), locals()) 

    def eth_getBalance(self, address) -> EthBalance:
        return self.creq(cfn(), locals())

def main():
    client  = Client(url="http://localhost:4000/jsonrpc")
    balance = client.eth_getBalance("0x043234")
    print("balance: " + balance)
    block   = client.eth_getBlockByHash("", False)
    print("block: " + str(block))

if __name__ == "__main__":
    main()
