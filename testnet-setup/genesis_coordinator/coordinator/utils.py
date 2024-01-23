import tomllib
import subprocess
from pathlib import Path
import shutil
import json
import re

def load_config(config):
    with open(config, 'rb') as f:
        config = tomllib.load(f)
    return config

def run(cmd):
    """
    run spawns a command in a subshell and raises and error if the result code is != 0
    returns stdout
    """
    result = subprocess.run(cmd, capture_output=True, shell=True)
    if result.returncode != 0:
        err = result.stdout + result.stderr
        raise RuntimeError(f'subprocess err: {cmd}: {err}')
    return result.stdout.decode("utf-8").strip('\n')

def run_stderr(cmd):
    """
    run spawns a command in a subshell and raises and error if the result code is != 0
    returns stderr
    """
    result = subprocess.run(cmd, capture_output=True, shell=True)
    if result.returncode != 0:
        err = result.stdout + result.stderr
        raise RuntimeError(f'subprocess err: {cmd}: {err}')
    return result.stderr.decode("utf-8").strip('\n')

def load_genesis(node_home):
    "load genesis from node_home"
    path = Path(node_home) / "config" / "genesis.json"
    with path.open() as f:
        genesis = json.load(f)
    return genesis

def save_genesis(node_home, genesis):
    "save genesis to node_home"
    path = Path(node_home) / "config" / "genesis.json"
    with path.open("w") as f:
        json.dump(genesis, f, indent=4)

def update_genesis_files(nodes_data, genesis):
    """
    update the genesis files in the validator node config instances
    """
    for moniker, info in nodes_data.items():
        save_genesis(info["node_home"], genesis)

def cleanup(dir):
    shutil.rmtree(dir)

def change_toml_string_directive(config, name, value):
    """
    Update a *string* configuration directive in a toml configuration file.
    Searchers for a directive with `name` and substitute its string value to `value`.
    """
    replacement_str = f'{name} = "{value}"'

    regex = name + r'\s*=\s*".*"'
    return re.sub(regex, replacement_str, config)

def load_app_toml(node_home):
    path = Path(node_home) / "config" / "app.toml"
    with path.open() as f:
        return f.read()

def load_config_toml(node_home):
    path = Path(node_home) / "config" / "config.toml"
    with path.open() as f:
        return f.read()

def write_config_toml(node_home, config):
    path = Path(node_home) / "config" / "config.toml"
    with path.open('w') as f:
        return f.write(config)

def write_app_toml(node_home, config):
    path = Path(node_home) / "config" / "app.toml"
    with path.open('w') as f:
        return f.write(config)