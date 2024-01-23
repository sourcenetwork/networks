if __name__ == '__main__':
    import sys
    import logging
    import json
    import argparse
    from coordinator import coordinator
    from coordinator import utils

    parser = argparse.ArgumentParser( prog='coordinator',
        description='initializes genesis and sourcehub node data')
    parser.add_argument('config', help='path to coordinator configuration file')

    args = parser.parse_args()

    logging.basicConfig(stream=sys.stderr, encoding='utf-8', level=logging.DEBUG)
    config = utils.load_config(args.config)
    workspace = "/tmp/sourcehub-testnet-coordination"
    server_dir = "/tmp/sourcehub-nodes-archival"
    genesis_data = coordinator.produce_genesis(config, workspace)
    coordinator.update_configurations(config, workspace, genesis_data["nodes"])

    addr = ('0.0.0.0', 8000)
    server = coordinator.setup_server(config, genesis_data["nodes"], server_dir, addr[0], addr[1])

    data = json.dumps(genesis_data, indent=4)
    print(data)

    try:
        logging.info(f'Serving directory {server_dir}')
        logging.info(f'Listening on {addr}')
        server.serve_forever()
    except BaseException as e:
        logging.info(f'Cleaning up workspaces: {workspace}, {server_dir}')
        utils.cleanup(workspace)
        utils.cleanup(server_dir)
        raise e
