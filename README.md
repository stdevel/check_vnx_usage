# check_vnx_usage
``check_vnx_usage`` is a Nagios / Icinga plugin for checking a EMC² VNX filer's storage usage.

# Requirements
I successfully tested the plugin on a EMC VNX Control Station release 3.0 (*NAS 8.1.9*). Make sure that the ``server_df`` command is available on your filer.

No additional Python packages are required - just deploy the script and use it.

# Usage
By defualt, the scripts checks all local file systems - it is also possible to include performance data for data visualization (*``-P`` / ``--show-perfdata`` parameters*).

The following parameters can be specified:

| Parameter | Description |
|:----------|:------------|
| `-d` / `--debug` | enable debugging outputs (*default: no*) |
| `-h` / `--help` | shows help and quits |
| `-P` / `--show-perfdata` | enables performance data (*default: no*) |
| `-p` / `--path` | path of a particular file system to be monitored (*default: none*) |
| `-w` / `--warning` | consumption warning threshold (*default: 80%*) |
| `-c` / `--critical` | consumption critical threshold (*default: 90%*) |
| `--version` | prints programm version and quits |

## Examples
The following example checks all local file systems:
```
# ./check_vnx_usage.py
OK: file system 'fs-giertz' OK (20%), file system 'fs-doge' OK (75%) |
```

Check a particular file system and also show performance data:
```
# ./check_vnx_usage.py -p fs-dolan -P
OK: file system 'fs-dolan' OK (0%) | 'fs-dolan_size'=103257584 'fs-dolan_used'=123664 'fs-dolan_free'=103133920
```

Check multiple file systems:
```
# ./check_vnx_usage.py -p fs-giertz -p fs-doge
OK: file system 'fs-giertz' OK (20%), file system 'fs-doge' OK (75%) |
```

# Installation
To install the plugin, simply deploy the script on the VNX Control Station.

# Configuration
Nagios / Icinga needs to execute the script by executing the ``check_by_ssh`` plugin with ``nasadmin`` privileges.

Ensure that the Nagios/Icinga(2) service user is able to login onto VNX Control Station without specifying a password:
```
# chsh -s /bin/bash icinga
# su - icinga
$ ssh-keygen
$ ssh-copy-id nasadmin@VNX-IP
$ ssh nasadmin@VNX-IP
$ exit
# chsh -s /sbin/nologin icinga
```

When generating the key, don't enter a passphrase, otherwise passwordless login will not work.

# Nagios / Icinga
Configure a command like this:
```
# 'check_vnx_usage' command definition
define command{
        command_name    check_vnx_usage
        command_line    $USER1$/check_by_ssh -t 40 -q -l nasadmin -H $HOSTADDRESS$ -C "/home/nasadmin/check_vnx_usage.py -P -w $ARG1$ -c $ARG2$"
        }
```

Alter your VNX filer object configuration to include this service:
```
define service{
        use                             generic-service
        host_name                       MY-VNX
        service_description             DIAG: Storage usage
        check_command                   check_vnx_usage!92!95
        }
```

## Icinga2
Configure a service like this:
```
apply Service "DIAG: Storage usage" {
  import "generic-service"
  check_command = "by_ssh"
  vars.by_ssh_command = [ "/home/nasadmin/check_vnx_usage.py" ]
  vars.by_ssh_arguments = {
    "-P" = {
      description = "Enable performance data (default: no)"
      set_if = "$vnx_perfdata$"
    }
    "-w" = {
      description = "Consumption warning threshold (default: 80%)"
      value = "$vnx_warn$"
    }
    "-c" = {
      description = "Consumption critical theshold (default: 90%)"
      value = "$vnx_crit$"
    }
    "-p" = {
      description = "Path of a particular fiel system to be monitored (default: none)"
      value = "$vnx_fs_path$"
    }
  }
  vars.by_ssh_quiet = true
  vars.by_ssh_timeout = 60
  vars.by_ssh_port = host.vars.ssh_port
  vars.by_ssh_logname = "nasadmin"
  assign where host.vars.os == "vnx" && host.vars.app == "filer"
}
```

Alter your VNX filer object configuration to include a SSH port, application and operating system flags and - optional - customized thresholds:
```
object Host "MY-VNX" {
  import "generic-host"

  address = "VNX-IP"

  vars.ssh_port = "22"
  vars.app = "filer"
  vars.os = "vnx"

  vars.vnx_warn = "85"
  vars.vnx_crit = "92"
}
```

To enable performance data, add the following definition:
```
vars.vnx_perfdata = true
```

To limit the plugin to a particular list of file systems, use the following statement:
```
vars.vnx_fs_path = [ "fs-giertz", "fs-doge" ]
```

