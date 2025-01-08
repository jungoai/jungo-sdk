## Installation

[Install rye](https://rye.astral.sh/guide/installation/):

```bash
curl -sSf https://rye.astral.sh/get | bash
```

Then install Jungo-sdk via `rye`:

``` bash
rye install jungo-sdk --git https://github.com/jungoai/jungo-sdk.git
```

## Run Echo worker

```bash
jungo-sdk-echo-worker --ip <HOST-IP> --port <PORT> --netuid <NETUID> --logging.debug --subtensor.chain_endpoint ws://<CHAIN-IP>:<CHAIN-PORT> --wallet.name <NAME> --wallet.hotkey <HOTKEY>
```

## Run Echo monitor

```bash
jungo-sdk-echo-monitor --subtensor.chain_endpoint ws://<CHAIN-IP>:<CHAIN-PORT> --wallet.name <NAME> --wallet.hotkey <HOTKEY> --logging.debug --netuid <NETUID>
```
