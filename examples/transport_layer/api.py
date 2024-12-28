from abc            import ABC, abstractmethod
from pydantic       import BaseModel

#------------------------------------------------------------------------------
#-- Types

Hex         = str
Hash        = Hex
BlockHash   = Hash
Address     = Hex
EthBalance  = Hash

class Block(BaseModel):
    number              : int | None
    hash                : BlockHash | None
    parent_hash         : BlockHash
    nonce               : Hash
    sha3_uncles         : str
    logs_bloom          : str | None
    transactions_root   : Hex
    state_root          : Hex
    timestamp           : Hex
    size                : Hex
    transactions        : list[Hex]

#------------------------------------------------------------------------------
#-- RPC

class ExampleApi(ABC):
    @abstractmethod
    def eth_getBlockByHash(self, block_hash: BlockHash, get_full_tx: bool) -> Block | None:
        ...
    @abstractmethod
    def eth_getBlockByNumber(self, block_number: Hex, get_full_tx: bool) -> Block | None:
        ...
    @abstractmethod
    def eth_getBalance(self, address: Address) -> EthBalance:
        ...
