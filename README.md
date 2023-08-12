# Overview

Opentrons REST API Server.

# Setup

- Install python >= 3.7
- Setup and configure a virtual python environment
  ```bash
  python3.7 -m venv .venv
  source .venv/bin/activate
  pip install poetry
  poetry install
  ```

# Install on Opentrons

```bash
export IP=xxx.xxx.xxx.xxx
ssh root@${IP} 'mount -o remount,rw /'
ssh root@${IP} 'mkdir -p /data/user_storage/opentronsrestserver'
scp server/server.py root@${IP}:/data/user_storage/opentronsrestserver
scp opentrons-rest-server.service root@${IP}:/etc/systemd/system
ssh root@${IP} 'systemctl enable opentrons-rest-server'
ssh root@${IP} '/sbin/reboot'
```

# Restarting the Rest server

- To restart the rest server. Usually only needed if you are replacing the code.
  `systemctl restart opentrons-rest-server.service`
- It can be performed remotely like the above commands by using `ssh` to invoke it.

# Accessing the log on the Opentrons

- To tail and follow the log for our rest server
  `journalctl -u opentrons-rest-server -f`
- To just see the log omit the `-f`
