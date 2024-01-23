from pathlib import Path
from http.server import SimpleHTTPRequestHandler, HTTPServer
import logging



from . import cmds
from . import utils

def produce_genesis(config, workspace_path):
    validators_conf = config["validators"]
    coordinator_moniker = list(filter(None, [moniker for moniker, params in validators_conf.items() if params.get("coordinator")]))[0]

    nodes_data = cmds.init_nodes(config, workspace_path)
    logging.info(f'Initialized nodes under {workspace_path}')

    coordinator_home = nodes_data[coordinator_moniker]["node_home"]
    
    for moniker, data in nodes_data.items():
        cmds.add_gen_acc(coordinator_home, data["address"], validators_conf[moniker]["gen-credits"])
    
    admin_addr, admin_key, admin_mnemonic = cmds.add_key(coordinator_home, "admin", config["keyring_pwd"])
    cmds.add_gen_acc(coordinator_home, admin_addr, config["admin"]["gen-credits"])

    genesis = utils.load_genesis(coordinator_home)
    genesis = cmds.update_genesis_params(genesis, config)
    
    utils.update_genesis_files(nodes_data, genesis)

    genesis = cmds.collect_genesis_txs(config, nodes_data)

    logging.info(f'Produced genesis')

    # TODO update config

    return {
        "nodes": nodes_data,
        "admin": {
            "address": admin_addr,
            "key": admin_key,
            "mnemonic": admin_mnemonic,
        }
    }

def update_configurations(config, workspace_path, nodes_data):
    """
    update_configurations changes required configuration directives in app.toml and config.toml
    for every validator
    """
    for node, data in nodes_data.items():
        app_toml = utils.load_app_toml(data["node_home"])
        config_toml = utils.load_config_toml(data["node_home"])

        app_toml = cmds.set_min_gas_price(app_toml)
        config_toml = cmds.set_persistent_peers(config_toml, nodes_data, config["validators"])
        config_toml = cmds.configure_block_time(config_toml, config)

        utils.write_app_toml(data["node_home"], app_toml)
        utils.write_config_toml(data["node_home"], config_toml)

def setup_server(config, nodes_data, server_directory, addr, port):
    try:
        Path(server_directory).mkdir()
    except FileExistsError:
        pass

    for moniker, data in nodes_data.items():
        cmds.archive_node_state(data, server_directory)
    logging.info(f'Produced Node Archives')

    class Handler(SimpleHTTPRequestHandler):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=server_directory, **kwargs)

    return HTTPServer((addr, port), Handler)
