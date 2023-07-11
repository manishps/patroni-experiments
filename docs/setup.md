# Setup

This document outlines how to use this repository and the Nutanix Cloud to begin experimenting with HA Postgres yourself.

# 1. Configuration

Configuration files are kept in the `pe/config` directory. To play around with the specific tools, you should edit:

- `pe/config/haproxy.cfg` - HA Proxy configuration
- `pe/config/patroni.yml` - Patroni configuration

To change the `etcd` settings, you'll need to edit `EtcdController` in `pe/runner/controllers.py` directly, as `etcd` is started via command-line dynamically.

## 1.1 Playing With the Topology

Part of the beauty of this testing framework is that it's agnostic as to whether you're running it locally or on the Nutanix Cloud. Simply copy `pe/config/topology.example.yml` into a new file and edit it to match whatever setup you want to play around with. It's recommended that you start testing a given configuration locally, to ensure everything works as expected, and then move on to distributing the nodes across an actual cluster.

Topology configuration files have a couple important parts, explained in comments below (`pe/config/topology.example.yml`):

```yml
# These are the database nodes that will participate in the experiment
# Each node will run flask, patroni, etcd, and postgres.
# You should make sure that each node has access to the necessary ports.
# IF THIS IS A LOCAL CONFIGURATION you're all set.
# IF THIS IS A REMOTE CONFIGURATION you'll need to manually go in to each
# node and make sure the firewall allows the needed ports, and then
# manually start the flask server by running `pe/runner/api.py <host> <port>`.
nodes:
  -
    # Name used internally and for etcd/patroni. Must be unique.
    name: pe1
    # Host/ip
    host: localhost
    # Port used for the flask server
    api_port: 3000
    # Port used for patroni
    patroni_port: 8009
    # Port used for etcd
    # NOTE: etcd uses TWO ports, the value `x` provided below, AND `x + 1`.
    # NOTE: Therefore you need to make sure that this node has access to the
    # NOTE: below port AND the below port + 1.
    etcd_port: 2379
    # Port used for postgres
    pg_port: 5433

  -
    # Same as above
    name: pe2
    host: 127.0.0.1
    api_port: 3001
    patroni_port: 8010
    etcd_port: 2381
    pg_port: 5434

  # You can specify as many nodes as you want to by extending this list

# This is the setup for the proxy. It only runs flask and HAProxy.
# Like above, make sure it can use the needed ports, and if it's a remote
# configuration manually start the flask api on this machine.
proxy:
  name: pe4
  host: 127.0.0.1
  api_port: 3002
  proxy_port: 5000
```

## 1.2 Running A Simple Local Configuration

First, ensure you have installed...

- `Python` version 3.9 or higher ([instructions here](https://www.python.org/downloads/release/python-390/))
- `Postgres` version 15 ([instructions here](https://www.postgresql.org/docs/current/tutorial-install.html))
- `HAProxy` version 1.1 or higher ([instructions here](https://www.haproxy.com/documentation/hapee/latest/getting-started/installation/))

Then create a virtual environment by running

```sh
python3 -m venv venv
source venv/bin/activate
```

from the project root. Then we can install all the other tools we need by running

```sh
pip3 install -r requirements.txt
pip3 install --editable .
```
The second command installs the project directory as an editable dependency, which allows us to use module access patterns and more easily configure project scripts. If all goes well, we can run the default local experiment using

```sh
experiment config/topology.local.yml --is-local
```

## 1.3 Preparing Nodes on the Nutanix Cloud

### 1.3.1 VM Creation

In order to run the experiment in a real distributed setup, you'll need to manually configure as many VMs as you want to play with. This subsection describes what you'll need to do inside each individual node.

Using [Prism](https://www.nutanix.com/go/nutanix-cloud-tco-roi?nis=8), create a VM specifying the following:

- `name` - \<PREFIX\>\_patroni_exp_\<i\>
- `vCPU(s)` - 1
- `Number of Cores Per vCPU` - 4
- `Memory` - 8 GiB
- `Disks`
    - `x` Delete existing disk (in CD-ROM)
    - `+ Add New Disk` (leave rest default)
        - `Type` - CD-ROM
        - `Operation` - Clone from Image Service
        - `Image` - Centos_7.6_new
        - Hit `Add`
    - `+ Add New Disk` (leave rest default)
        - `Size` - 25 GiB
        - Hit `Add`
- `Network Adapters (NIC)`
    - `+ Add New NIC` (leave all default)
        - `Add`
- Hit `Save`

Go to the VM list (top left of Prism) and find the VM you just created. Hit `Power on`. Make note of the IP address it is given (you may need to wait a few minutes and refresh for an IP to be assigned).

Next follow CentOS setup inside the VM. Probably easiest to just do this through the `Launch Console` button available on the Prism console when the VM is selected.
- Automatic partitioning is fine, everything else should be fine as default from the disk image selected during VM creation.

Create a root password, and user. 

```
POTENTIAL ISSUE
When standing up a new VM like this (using ipam) you'll need to tweak the settings for the network to be reachable. 
To fix this, run
    sudo vi /etc/sysconfig/network-scripts/ifcfg-eth0
and add
    BOOTPROTO=dhcp
    ONBOOT=yes
to the end of the file. You will then need to reboot.
```

Once installation and setup complete, you can access however you'd like. (I personally use remote connection through VS Code.) You'll want to go into each node and clone this repo into a sane location.

### 1.3.2 Postgres

For CentOS 7.6, run:

```sh
sudo yum install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
sudo yum install libzstd-devel
sudo yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm
sudo yum -y install postgresql15-server python-devel postgresql-devel
```

Fix PATH. Open `~/.bashrc` and add

```
export PATH=$PATH:/usr/pgsql-15/bin/
```

### 1.3.3 Python 3.9

The version of CentOS that we're using comes with Python 3.6 by default, which is lacking many of the features we need. You can upgrade to 3.9 by following [this tutorial](https://www.inmotionhosting.com/support/server/linux/install-python-3-9-centos-7/). You can make sure you've got it installed by running
```sh
python3.9 --version
```
You should see `Python 3.9.6` printed.

### 1.3.4 Other Dependencies + Environment

```sh
sudo yum install etcd haproxy libyaml python python3-psycopg2 gcc python3-devel
```

Next make a virtual environment for python by running

```sh
python3.9 -m venv venv
source venv/bin/activate
pip3.9 install -r requirements.txt
pip3.9 install --editable . # From inside the root of this project
```

### 1.3.5 Firewall Management

`etcd` and `patroni` use a few ports which are not open for connections by default. To fix this, run
```sh
sudo vi /etc/services
```
and add
```
etcd            2379/tcp                # etcd client
etcd            2380/tcp                # etcd peers
...
pg              5432/tcp                # Postgres
...
patroni         8009/tcp                # Patroni REST Api
```

Then we need to allow them on the firewall

```sh
sudo firewall-cmd --zone=public --add-port 2379/tcp --permanent
sudo firewall-cmd --zone=public --add-port 2380/tcp --permanent
sudo firewall-cmd --zone=public --add-port 5432/tcp --permanent
sudo firewall-cmd --zone=public --add-port 5433/tcp --permanent
sudo firewall-cmd --zone=public --add-port 8009/tcp --permanent
sudo firewall-cmd --zone=public --add-port 5000/tcp --permanent
sudo firewall-cmd --zone=public --add-port 3000/tcp --permanent
sudo firewall-cmd --reload
```

Depending on your setup, you may need to add additional ports to `/etc/services` and run `firewall-cmd` addtional times. That's up to you.
