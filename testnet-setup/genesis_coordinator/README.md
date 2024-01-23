# Coordinator

Coordinator is a python package used to produce a `genesis.json` and related Validator configuration and state for SourceHub.


## How it works

The coordinator package initializes the state directory for each validator (as per the TOML configuration), generates a validator key pair and moves the genesis tx back and forth to gather the signatures.
The coordination is done locally, as such this deployment model should only be done when the coordinator can be trusted to access the private keys of the initial validators.

Once the coordinator has built the genesis, it archives each validators node state.
The node state is then served through HTTP and individual validators can fetch their state, alongside with their encrypted private key.

## Usage

### Coordinator

Run the python package locally, specifying the configuration file.

```python
python -m coordinator {config.toml}
```

By default, it will serve the Node archived on port 8000.


### Validators

Validators must fetch their node state from the coordinator.

To fetch the state run, fetch the archive using the validators moniker and the coordinators IP.
The state can be extracted with tar, producing the default `.sourcehub` state directory and an encrypted private key file `key`.
The key can be imported using SourceHub's key management commands.

Example:

```sh
cd ~
curl -L http://my.coordinator.xyz:8000/my_moniker.tar.gz > state.tar.gz
tar -xvf state.tar.gz
sourcehubd keys import validator key

# cleanup
rm key
rm -rf state.tar.gz
```


## Coordinator Configuration

The configuration file is a TOML file with 4 main sections: root, validators, admin and consensus.

### Validators

Validators are defined as a TOML table under the `validators` prefix / namespace.

Each validator entry must define a few entries.
`gen-credits` is the list of credits given to the validator account in the genesis file.
`delegation` is the ammount of tokens the validator will delegate in the genesis tx
`ip` is the validators p2p ip address, to which peers will connect to.

The following is an example Validator definition.
It adds a new validator called `my_moniker`.
Example:

```toml
[validators.my_moniker]
gen-credits = ["10000000stake"]
delegation = "5000000stake"
ip = "10.0.0.1"
```

Note: There should be *one* validator which acts as the coordinator for the setup.
This validator is selected by settings the key-value  `coordinator = true` in the config file.


### Admin

The admin section defines and additional account added to the genesis file, which may act as a faucet or token bank.

The admin is receives a list of tokens, specified in the `gen-credits` key-value.

### Consensus

Consensus contains a list of consesus parameters as defined by CometBFT's `config.toml` file.
It's repeated in the coordinator config to ease configuration management among the validators.

### Root

Root contains some general genesis parameters such as genesis time and chain id.

It also contains a `keyring_pwd` which is the password used to encrypt the validator's private keys.
