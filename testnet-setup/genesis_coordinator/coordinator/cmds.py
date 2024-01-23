from pathlib import Path
import shutil
import json
import tarfile
import re

from . import utils

def init_nodes(config, workspace):
    """
    init_nodes initializes all nodes according to the config spec
    """

    pwd = config["keyring_pwd"]
    chain_id = config["chain_id"]
    validators = config["validators"]
    nodes_data = {}
    for moniker in validators:
        try:
            node_data = init_node(workspace, moniker, chain_id, pwd)
            nodes_data[moniker] = node_data
        except Exception as e:
            raise RuntimeError(f'could not initialize node {moniker}: {e}')
    return nodes_data


def add_key(node_home, key_name, keyring_pwd):
    "adds a key to a node's local keyring"
    mnemonic = utils.run(f'sourcehubd keys add {key_name} --keyring-backend test --home {node_home} 2>&1 | tail -n 1')
    key = utils.run(f'echo {keyring_pwd} | sourcehubd keys export {key_name} --home {node_home} --keyring-backend test')
    addr = utils.run(f'sourcehubd keys show {key_name} --address --home {node_home} --keyring-backend test')
    return (addr, key, mnemonic)

def init_node(workspace, moniker, chain_id, keyring_pwd):
    "initialize a node under the given workspace, return key mnemonic, addr and encrypted key"
    data_dir = Path(workspace)/moniker
    node_home = data_dir/".sourcehub"

    #create subdirs if needed, clean up data from previous run and create fresh workin dir
    utils.run(f'mkdir -p {data_dir}')
    utils.run(f'rm -rf {data_dir}')
    utils.run(f'mkdir {data_dir}')

    utils.run(f'sourcehubd init {moniker} --chain-id {chain_id} --home {node_home}')

    mnemonic = utils.run(f'sourcehubd keys add {moniker} --keyring-backend test --home {node_home} 2>&1 | tail -n 1')
    addr = utils.run(f'sourcehubd keys show {moniker} --address --home {node_home} --keyring-backend test')
    key = utils.run(f'echo {keyring_pwd} | sourcehubd keys export {moniker} --home {node_home} --keyring-backend test')

    id = utils.run(f'sourcehubd cometbft show-node-id --home {node_home}')
    
    with (data_dir/"key").open("w") as f:
        f.write(key)

    return {
        "moniker": moniker,
        "mnemonic": mnemonic,
        "address": addr,
        "key": key,
        "node_home": str(node_home),
        "node_data": str(data_dir),
        "node_id": id,
    }

def add_gen_acc(node_home, addr, credits):
    "adds a genesis account with the given validator information"
    values = ','.join(credits)
    cmd = f'sourcehubd genesis add-genesis-account {addr} {values} --home {node_home}'
    utils.run(cmd)

def update_genesis_params(genesis, config):
    "Sets the given genesis with the parameters sourcehub requires"
    genesis["genesis_time"] = config["genesis_time"]

    genesis["app_state"]["staking"]["params"]["unbonding_time"] = "1s"
    genesis["app_state"]["staking"]["params"]["max_validators"] = "15"

    genesis["app_state"]["slashing"]["params"]["slash_fraction_double_sign"] = "0.0"
    genesis["app_state"]["slashing"]["params"]["slash_fraction_downtime"] = "0.0"

    genesis["app_state"]["mint"]["params"]["blocks_per_year"] = "31536000"

    genesis["app_state"]["gov"]["params"]["voting_period"] = "1800s"
    genesis["app_state"]["gov"]["params"]["expedited_voting_period"] = "900s"

    return genesis


def sign_genesis(node_data, validator_config, chain_id):
    """
    signs the genesis tx currently present in the given validator node home directory
    """
    cmd = f'sourcehubd genesis gentx {node_data["moniker"]} {validator_config["delegation"]} --chain-id {chain_id} --home {node_data["node_home"]} --keyring-backend test'
    utils.run(cmd)

def collect_genesis_txs(config, nodes_data):
    """
    collect_genesis_txs copies all signed gen txs for each valiadtor onto the coordinators directory and produces
    the final genesis.
    return genesis
    """
    for node, data in nodes_data.items():
        sign_genesis(data, config["validators"][node], config["chain_id"])

    coordinator = ""
    vals = []
    for node, node_params in config["validators"].items():
        if node_params.get("coordinator"):
            coordinator = node
        else:
            vals.append(node)

    dest = Path(nodes_data[coordinator]["node_home"])/"config"/"gentx"

    for node in vals:
        gentx_dir = Path(nodes_data[node]["node_home"])/"config"/"gentx"
        gentx = next(gentx_dir.iterdir())
        shutil.copy(gentx, dest)

    cmd = f'sourcehubd genesis collect-gentxs --home {nodes_data[coordinator]["node_home"]}'
    utils.run_stderr(cmd)
    genesis = utils.load_genesis(nodes_data[coordinator]["node_home"])
    return genesis

def archive_node_state(node_data, output_dir):
    "produces a tar archive of the current node configuration directory"
    node_data_dir = Path(node_data["node_data"])
    key = node_data_dir/"key"
    node_home = node_data["node_home"]

    filter = lambda tar_info: None if 'keyring-test' in tar_info.name else tar_info

    archive = Path(output_dir)/(f'{node_data["moniker"]}.tar.gz')
    file = tarfile.open(archive, "w:gz")
    file.add(key, arcname="key")
    file.add(node_home, arcname=".sourcehub", filter=filter)
    file.close()

def set_persistent_peers(comet_config, nodes_data, validators_config):
    """
    Sets the persistent peers configuration directive in config
    with the given validator node data.
    """
    formatter = lambda node_id, ip: f'{node_id}@{ip}:26656'
    peers_addrs = [formatter(data["node_id"], validators_config[moniker]["ip"]) for moniker, data in nodes_data.items()]
    peers_addrs = ",".join(peers_addrs)
    return utils.change_toml_string_directive(comet_config, "persistent_peers", peers_addrs)

def set_min_gas_price(app_config):
    """
    Updates an app.toml configuration to contain minimum-gas-price = "0stake,0uopen"
    """
    name = 'minimum-gas-prices' 
    value = '0stake,0uopen'
    return utils.change_toml_string_directive(app_config, name, value)

def configure_block_time(comet_config, config):
    """
    update block time parameters in comet config (config.toml)
    """
    comet = comet_config
    consensus = config["consensus"]

    applier = lambda name: utils.change_toml_string_directive(comet, name, consensus[name])

    comet = applier("timeout_propose")
    comet = applier("timeout_propose_delta")
    comet = applier("timeout_prevote")
    comet = applier("timeout_prevote_delta")
    comet = applier("timeout_precommit")
    comet = applier("timeout_precommit_delta")
    comet = applier("timeout_commit")

    return comet