# Jungo SDK

## Run Examples

### Via Rye

[Install rye](https://rye.astral.sh/guide/installation/):

### Run Echo worker

```bash
rye run echo-worker --ip <HOST-IP> --port <PORT> --netuid <NETUID> --logging.debug --chain ws://<CHAIN-IP>:<CHAIN-PORT> --wallet.name <NAME> --wallet.hotkey <HOTKEY>
```

### Run Echo monitor

```bash
rye run echo-monitor --chain_endpoint ws://<CHAIN-IP>:<CHAIN-PORT> --wallet.name <NAME> --wallet.hotkey <HOTKEY> --logging.debug --netuid <NETUID>
```
