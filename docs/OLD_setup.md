# Setup

This document outlines how setup this repo across three VMs in Prism to play around with yourself.

### [1. VM Creation](#vm-creation)
[1.1 Ignored Files](#ignored-files)

### [2. Installing Tools](#installing-tools)
[2.1 Postgres](#postgres)
[2.2 Python + Other](#other-dependencies)

### [3. Opening Ports](#opening-ports)

## VM Creation

You'll need to make three VMs. Fields to specify while making each VM:

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

Once installation and setup complete, you can access however you'd like. (I personally use remote connection through VS Code.)

### Ignored Files

At this point, you'll likely want to set up `git` on the machine and clone this repo. This is left to the reader.

One important thing to note, however, is that certain configuration files are hidden from git source but expected to be present.

- First, create a copy of `.THIS_NAME.example` and rename the file `.THIS_NAME` in the root directory. Each VM should have a unique name in this file, just a simple string should do.
- Then, create a copy of the entire `.config.example` folder. **NOTE:** For _each_ VM, you should list both the host (IP) and unique name you gave it in `.THIS_NAME`. This is how machines will create configuration files that boot patroni, so it's important this is done correctly.


## Installing Tools

The next step is to install the necessary tools on each VM.

### Postgres

Add the requirements repo

```
sudo yum install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
```

Install requirements

```
sudo yum install libzstd-devel
```

Add another repo

```
sudo yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm
```

Actually install last things

```
sudo yum -y install postgresql15-server python-devel postgresql-devel
```

Fix PATH. Open `~/.bashrc` and add

```
export PATH=$PATH:/usr/pgsql-15/bin/
```

### Other Dependencies

```
sudo yum install etcd haproxy libyaml python python3-psycopg2 gcc python3-devel
```

Next make a virtual environment for python by running

```
python3 -m venv venv
source venv/bin/activate
```

Then get the python dependencies using

```
pip3 install -r requirements.txt
```

## Opening Ports

`etcd` and `patroni` use a few ports which are not open for connections by default. To fix this, run
```
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

```
sudo firewall-cmd --zone=public --add-port 2379/tcp --permanent
sudo firewall-cmd --zone=public --add-port 2380/tcp --permanent
sudo firewall-cmd --zone=public --add-port 5432/tcp --permanent
sudo firewall-cmd --zone=public --add-port 5433/tcp --permanent
sudo firewall-cmd --zone=public --add-port 8009/tcp --permanent
sudo firewall-cmd --zone=public --add-port 5000/tcp --permanent
sudo firewall-cmd --zone=public --add-port 3000/tcp --permanent
sudo firewall-cmd --reload
```
