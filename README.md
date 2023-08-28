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

SSH into the Opentrons system and run `wget -q -O - https://raw.githubusercontent.com/genie-inc/opentrons_rest_api/master/install.sh | sh`

# Restarting the Rest server

- To restart the rest server. Usually only needed if you are replacing the code.
  `systemctl restart opentrons-rest-server.service`
- It can be performed remotely like the above commands by using `ssh` to invoke it.

# Accessing the log on the Opentrons

- To tail and follow the log for our rest server
  `journalctl -u opentrons-rest-server -f`
- To just see the log omit the `-f`

# Running server in Simulate mode

Server can be run locally using this command:

```
cd server
uvicorn server:app  --host 0.0.0.0 --port 9090
```

It's not very useful without simulate mode. You need to be in the server directory first.

To start in server in simulate mode create the environment variable OT_DEBUG:
`export OT_DEBUG=true`
and then start the server. Opentrons will display some useful info in the log about the simulate process.

To stop simulating just run `unset OT_DEBUG`

# Running in debugger

- Read this: https://fastapi.tiangolo.com/tutorial/debugging/
- Follow the instructions for vscode.
- You will probably want to run in simulate mode so will need to set the env var in the launcher:

```
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "env": {
        "OT_DEBUG": "true"
      }
    }
  ]
}
```

- don't forget to remove the uvicorn stuff from the file before merging!
