# Overview

Opentrons REST API Server.

# Install on Opentrons

SSH into the Opentrons system and run `wget -q -O - https://raw.githubusercontent.com/genie-inc/opentrons_rest_api/master/install.sh | sh`

# Restarting the Rest server

- To restart the rest server. Usually only needed if you are replacing the code.
  `systemctl restart opentrons-rest-server.service`
- It can be performed remotely like the above commands by using `ssh` to invoke it.

# Accessing the log on the Opentrons

- To tail and follow the log for our rest server
  `journalctl -u opentrons-rest-server -f`
- To just see the log omit the `-f`
