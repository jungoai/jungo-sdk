from argparse                               import ArgumentParser, Namespace
from typing                                 import Callable
from bittensor.core.extrinsics.serving      import serve_extrinsic
from bittensor.core.extrinsics.set_weights  import do_set_weights
from dataclasses                            import dataclass
from netaddr                                import IPAddress
from jungo_sdk.transport                    import RpcServer, serve
from jungo_sdk.utils                        import guard, lmap, unOpt
from pathlib                                import Path

import bittensor        as bt
import bittensor_wallet as btwallet

#------------------------------------------------------------------------------
#-- Types/Constants


HOME_DIR = Path.home()
DEFAULT_SDK_DIR = HOME_DIR / ".jungoai"
DEFAULT_WALLETS_DIR = DEFAULT_SDK_DIR / "wallets"
DEFAULT_MINERS_DIR = DEFAULT_SDK_DIR / "miners"


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
    millisecs_per_block: int

    def __init__(self, block_number: int, fast_blocks: bool) -> None:
        self.block_number = block_number
        if fast_blocks:
            self.millisecs_per_block = 5000
        else:
            self.millisecs_per_block = 12000

    def millisecs(self) -> int:
        return self.block_number * self.millisecs_per_block

    def second(self) -> float:
        return self.block_number * self.millisecs_per_block / 1000

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
class JNode:
    netuid      : int
    uid         : int
    wallet      : btwallet.Wallet
    subtensor   : bt.Subtensor

    def __init__(
        self, 
        bt_conf: bt.Config,
        netuid : int,
        wallet_path: str = str(DEFAULT_WALLETS_DIR),
        logging_path: str = str(DEFAULT_MINERS_DIR),
        chain_endpoint: str = "wss://devnet-rpc.jungoai.xyz" # TODO: change it after runnig mainnet
    ):
        """ errors: NodeError 
        """

        bt_conf.wallet.path = wallet_path # type: ignore
        bt_conf.logging.logging_dir = logging_path # type: ignore
        bt_conf.subtensor.chain_endpoint = chain_endpoint # type: ignore

        wallet      = bt.wallet(config=bt_conf)
        subtensor   = bt.subtensor(config=bt_conf)
        hotkey_addr = wallet.hotkey.ss58_address

        guard(
            subtensor.is_hotkey_registered(hotkey_addr, netuid), 
            HotkeyNotRegistered(str(hotkey_addr), netuid)
        )

        self.netuid     = netuid
        self.uid        = subtensor.metagraph(netuid).hotkeys.index(hotkey_addr)
        self.wallet     = wallet
        self.subtensor  = subtensor

    def hotkey(self):
        return self.wallet.hotkey.ss58_address

def add_args_jnode_and_conf(parser):
    conf = mk_conf(parser)
    parser.add_argument("--netuid", type=int, help="netuid", required=True)
    parser.add_argument("--chain", type=str, help="chain") # TODO: help
    return conf

def mk_conf(parser):
    bt.wallet.add_args(parser)
    bt.subtensor.add_args(parser)
    bt.logging.add_args(parser)
    bt.axon.add_args(parser)
    return bt.config(parser)

def mk_jnode_from_args(args: Namespace, conf) -> JNode:
    return JNode(
        bt_conf = conf,
        netuid = args.netuid,
        chain_endpoint = args.chain
    )

#------------------------------------------------------------------------------
#-- Monitor

@dataclass
class Monitor:
    node        : JNode
    fast_blocks : bool

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

        if not temp is None : return Tempo(temp, self.fast_blocks)
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

def add_args_monitor_and_conf(parser: ArgumentParser):
    # conf should created before add new args
    conf = add_args_jnode_and_conf(parser)
    parser.add_argument("--fast_blocks", action="store_true", help="netuid")
    return conf

def mk_monitor_from_args(args: Namespace, conf) -> Monitor:
    jnode = mk_jnode_from_args(args, conf)
    return Monitor(jnode, args.fast_blocks)

#------------------------------------------------------------------------------
#-- Worker

@dataclass
class Worker:
    node:   JNode
    ip:     str
    port:   int

    def __init__(
        self, 
        node: JNode,
        ip_: IPAddress,
        port: int
    ):
        """ errors: NodeError 
        """
        n    = node
        ip   = str(ip_)

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
        self.ip   = ip
        self.port = port

def add_args_worker_and_conf(parser: ArgumentParser):
    # conf should created before add new args
    conf = add_args_jnode_and_conf(parser)
    parser.add_argument("--ip", type=str, help="ip", required=True) # TODO: help
    parser.add_argument("--port", type=int, help="port", required=True) # TODO: help
    return conf

def mk_worker_from_args(args: Namespace, conf) -> Worker:
    node = mk_jnode_from_args(args, conf)
    return Worker(
        node,
        args.ip,
        args.port
    )

def serve_worker(port: int, s: RpcServer) -> None:
    serve("0.0.0.0", port, s.rpcs())
