"""
    Netconf python example by yang-explorer (https://github.com/CiscoDevNet/yang-explorer)

    Installing python dependencies:
    > pip install lxml ncclient

    Running script: (save as example.py)
    > python example.py -a {{host|safe}} -u {{user|safe}} -p {{passwd|safe}} --port {{port}}
"""

import lxml.etree as ET
from argparse import ArgumentParser
from ncclient import manager

payload = """
{{data|safe}}
"""

if __name__ == '__main__':

    parser = ArgumentParser(description='Usage:')

    # script arguments
    parser.add_argument('-a', '--host', type=str, required=True,
                        help="Device IP address or Hostname")
    parser.add_argument('-u', '--username', type=str, required=True,
                        help="Device Username (netconf agent username)")
    parser.add_argument('-p', '--password', type=str, required=True,
                        help="Device Password (netconf agent password)")
    parser.add_argument('--port', type=int, default=830,
                        help="Netconf agent port")
    args = parser.parse_args()

    # connect to netconf agent
    with manager.connect(host=args.host,
                         port=args.port,
                         username=args.username,
                         password=args.password,
                         timeout=90,
                         hostkey_verify=False,
                         device_params={'name': '{{platform}}'}) as m:

        # execute netconf operation
        response = {{nccall|safe}}{% if datastore == 'candidate' %}
        m.commit(){% endif %}

        # beautify output
        data = ET.fromstring(response)
        print(ET.tostring(data, pretty_print=True))
