
Ledgable Data & Console Node (C)2018 Ledgable BV

THIS SOFTWARE IS RELEASED UNDER THE GNU GENERAL PUBLIC LICENSE V3.0
https://www.gnu.org/licenses/gpl-3.0.en.html

Usage: srv.py -m {node|console} -d <deviceid> -p <pin> [-l <0.0.0.0:0>] [-s <0.0.0.0:0>] --debug

-m {node|console}  - Use device is specific mode
                     Node = datanode is a replication group
                     Console = querying and committing data to chains
-d <deviceid>      - Device identifier associated to realm
-p <pin>           - Device pin
-s <0.0.0.0:0>     - (Optional) Server providing indexer (default = www.ledgable.com)
-l <0.0.0.0:0>     - (Optional) Listen on alternate interface
-o 80,443          - Creates a webserver instance on ports (separated by ,) that
                     allows access via json and push/put/get functionality
-r <0.0.0.0:0>     - Register ip address as indicated as opposed to listener
                     Useful if behind a firewall or such infrastructure
--debug            - Enable console debugging


-- CONSOLE MODE

-c <chainid>       - Chain ID for operation (required for console mode)

Notes

You will require a device id and pin code to download configuration for this node.
Goto https://www.ledgable.com to create a new device.

In "Console" mode
Console mode allows for chains to be queried and data to be written to the service
It should be noted that no control on who can write data is expressly defined in the platform other
than replication nodes

If a console is not allowed to write data (for a chain), then attempts to write will fail

