
Ledgable Data Node (C)2018 Ledgable BV

THIS SOFTWARE IS RELEASED UNDER THE GNU GENERAL PUBLIC LICENSE V3.0
https://www.gnu.org/licenses/gpl-3.0.en.html

Usage: srv.py -d <deviceid> -p <pin> [-l <0.0.0.0:0>] [-s <0.0.0.0:0>] --debug

-d <deviceid>      - Device identifier associated to realm
-p <pin>           - Device pin
-s <0.0.0.0:0>     - (Optional) Server providing indexer (default = www.ledgable.com)
-l <0.0.0.0:0>     - (Optional) Listen on alternate interface
-o 80,443          - Creates a webserver instance on ports (separated by ,) that
                     allows access via json and push/put/get functionality
-r <0.0.0.0:0>     - Register ip address as indicated as opposed to listener
                     Useful if behind a firewall or such infrastructure
--debug            - Enable console debugging

Notes

You will require a device id and pin code to download configuration for this node.
Goto https://www.ledgable.com to create a new device.

