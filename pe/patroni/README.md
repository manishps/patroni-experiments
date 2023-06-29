# Patroni

## Usage

To make sure that we are able to run the nodes with different names and IPs (as needed) we don't store the actuall patroni config in source. Instead we store this template, with the understanding that each node will need to run `make_conf.sh` whenever the template changes, which will generate the `conf.yml` file in this directory that we actually use to start patroni.