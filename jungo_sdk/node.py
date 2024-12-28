from typing                                 import Callable
from bittensor.core.extrinsics.serving      import serve_extrinsic
from bittensor.core.extrinsics.set_weights  import do_set_weights
from dataclasses                            import dataclass
from netaddr                                import IPAddress
from jungo_sdk.transport                    import RpcServer, serve
from jungo_sdk.utils                        import guard, lmap, unOpt

import bittensor        as bt
import bittensor_wallet as btwallet

#------------------------------------------------------------------------------
#-- Types/Constants

# TODO: get it from args or config
# MILLISECS_PER_BLOCK = 12000 # normal
MILLISECS_PER_BLOCK = 5000 # fast-block

@dataclass
class Endpoint:
    ip  : IPAddress
    port: int

    def __init__(self, ip, port: int):
        self.ip   = IPAddress(ip)
        self.port = port

    def ip_str(self) -> str:
        return str(self.ip)

    def version(self) -> int:
        return int(self.ip.version)

    def __hash__(self) -> int:
        return hash((self.ip, self.port))

@dataclass
class Tempo:
    block_number: int

    def millisecs(self) -> int:
        return self.block_number * MILLISECS_PER_BLOCK

    def second(self) -> float:
        return self.block_number * MILLISECS_PER_BLOCK / 1000

Uid             = int
WorkerWeight    = int
WorkerEndpoint  = Endpoint

#------------------------------------------------------------------------------
#-- Errors

class NodeError(Exception): pass

@dataclass
class HotkeyNotRegistered(NodeError):
    hotkey: str
    netuid: int
    def __str__(self) -> str: 
        return f"Wallet: {self.hotkey} is not registered on netuid {self.netuid}."

# TODO: provide __str__ for each
class SubnetNotRegistered           (NodeError): pass
class SetWeightsFailed              (NodeError): pass
class WorkerEndpointRegisterFailed  (NodeError): pass

#------------------------------------------------------------------------------
#-- Jungo Node

@dataclass
class JConfig:
    bt_conf: bt.Config
    netuid : int

@dataclass
class JNode:
    netuid      : int
    uid         : int
    wallet      : btwallet.Wallet
    subtensor   : bt.Subtensor

    def __init__(self, conf: JConfig):
        """ ! NodeError 
        """
        bt_conf     = conf.bt_conf
        netuid      = conf.netuid
        wallet      = bt.wallet(config=bt_conf)
        subtensor   = bt.subtensor(config=bt_conf)
        hotkey_addr = wallet.hotkey.ss58_address

        guard(
            subtensor.is_hotkey_registered(hotkey_addr, netuid), 
            HotkeyNotRegistered(str(hotkey_addr), netuid)
        )

        self.netuid       = netuid
        self.uid          = subtensor.metagraph(netuid).hotkeys.index(hotkey_addr)
        self.wallet       = wallet
        self.subtensor    = subtensor

    def hotkey(self):
        return self.wallet.hotkey.ss58_address

#------------------------------------------------------------------------------
#-- Monitor

@dataclass
class Monitor:
    node: JNode

    def __init__(self, conf: JConfig):
        """ ! NodeError 
        """
        self.node   = JNode(conf)

    def set_weights_with(
        self,
        set_weight: Callable[
            [WorkerEndpoint, Uid],
            tuple[Uid, WorkerWeight]
        ]):
        """ ! NodeError 
        """
        bt.logging.debug(f"guard hotkey registred")
        self.guard_hotkey_registred()

        n       = self.node
        s       = n.subtensor
        bt.logging.debug(f"query axons")
        axons   = s.query_map_subtensor("Axons")

        bt.logging.debug(f"query uids")
        uids = s.query_map_subtensor("Uids")

        def get_uid(net, hot) -> Uid | None:
            bt.logging.debug(f"get uid of netuid: {net}, hotkey: {hot}")
            for (net_, hot_), uid in uids:
                if net_ == net and hot_ == hot:
                    return uid
            return None

        workers = [
            (Endpoint(v.value["ip"], v.value["port"]), get_uid(net, hot)) 

            for (net, hot), v in axons 
            if  net == n.netuid
        ]

        # TODO: using threads
        weights     = lmap(lambda t: set_weight(t[0], unOpt(t[1])), workers)
        bt.logging.debug(f"weights: {weights}")

        uids, vals  = map(list, zip(*weights))
        succ, err   = do_set_weights(n.subtensor, n.wallet, uids, vals, n.netuid)

        if not succ : raise SetWeightsFailed(err)
        else        : bt.logging.info(f"weights succesfully set")

    def tempo(self) -> Tempo:
        """ ! NodeError 
        """
        n    = self.node
        temp = n.subtensor.tempo(n.netuid)

        if not temp is None : return Tempo(temp)
        else                : raise  SubnetNotRegistered()

    def guard_hotkey_registred(self):
        """ ! NodeError 
        """
        n = self.node
        hotkey = n.wallet.hotkey.ss58_address
        netuid = n.netuid
        guard(
            n.subtensor.is_hotkey_registered(
                hotkey,
                netuid
            ), 
            HotkeyNotRegistered(hotkey, netuid)
        )

#------------------------------------------------------------------------------
#-- Worker

@dataclass
class Worker:
    node: JNode
    ip  : IPAddress
    port: int

    def __init__(self, ip: str, port: int, conf: JConfig):
        """ ! NodeError 
        """
        n = JNode(conf)

        axons = n.subtensor.query_map_subtensor("Axons")
        net = n.netuid
        hot = n.hotkey()

        if not (net, hot) in axons:
            bt.logging.debug(f"Registring Axon for: netuid: {net}, hotkey: {hot}")
            succ = serve_extrinsic(n.subtensor, n.wallet, ip, port, 4, n.netuid)
            if not succ: raise WorkerEndpointRegisterFailed()
        else:
            bt.logging.debug(f"Axon Registerd befor for: netuid: {net}, hotkey: {hot}")

        self.node = n
        self.ip   = IPAddress(ip)
        self.port = port

def serve_worker(w: Worker, s: RpcServer) -> None:
    serve(str(w.ip), w.port, s.rpcs())
