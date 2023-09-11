# Developer Instructions

# Setup

- Install python >= 3.7
- Setup and configure a virtual python environment
  ```bash
  python3.7 -m venv .venv
  source .venv/bin/activate
  pip install poetry
  poetry install
  ```

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

- Add the following debug target into VSCode:

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

- Put a breakpoint in server/server.py
- Run the launch target against the file debug/server_debug.py
- For details read this: https://fastapi.tiangolo.com/tutorial/debugging/
