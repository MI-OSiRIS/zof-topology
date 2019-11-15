
# Temporary monkey patch for ZoF bug
import builtins, uuid
base_import, sentinal = builtins.__import__, str(uuid.uuid4())
def _patch(self, message):
    from zof import exception as _exc
    """Called when `OFP.MESSAGE` is received with type 'CHANNEL_ALERT'."""
    # First check if this alert was sent in response to something we said.
    msg_xid = message['xid']
    if msg_xid and self._handle_xid(message, msg_xid,
                                  _exc.DeliveryException):
        return
    # Otherwise, we need to report it.
    msg = message['msg']
    data_hex = msg['data']
    data_len = len(data_hex) / 2
    if len(data_hex) > 100:
        data_hex = '%s...' % data_hex[:100]
    LOGGER.warning(
        'Alert: %s data=%s (%d bytes) [conn_id=%s, datapath_id=%s, xid=%d]',
        msg.get('alert', '#UNKNOWN#'), data_hex, data_len, message.get('conn_id', "#UNKNOWN#"),
        message.get('datapath_id', "#UNKNOWN#"), msg_xid)
    
    for app in self.apps:
        app.handle_event(message, 'message')

def patch_import(*args, **kwargs):
    m = base_import(*args, **kwargs)
    if m.__name__ == "zof.controller" and not getattr(m, sentinal, None):
        m._handle_alert = _patch
        setattr(m, sentinal, True)
    return m
builtins.__import__ = patch_import
# End monkey patch


import zof
import warnings
import json

import config, rest_api

from pprint import pprint
from sdn_handler import *
from registration_handler import *
from collections import defaultdict

APP = zof.Application("TopologyController")

# TODO
# - Read arguments from config file/command line. (done-ish, need to read from file too)
# - Explicitly declare listening endpoint.
# - Topology registration. (done)
# - Keep discovered stuff in same domain. (done)
# - Web Api. (done, yay)
# - Port add/modify/delete handlers. (probably not necessary)
# - Set default forwarding rules. (not sure if necessary, will test)
# - Get asyncio ssl warnings from ZoF to go away (done)
# - Containerize
# - README



'''
    To listen to a specific endpoint rather than everything that is pointed to the controller, add
    --listen-endpoint flag to the run statement.

    ex) python3.6 app.py -c my_config.ini --listen-endpoints [::]:6653
'''
@APP.event('start')
async def start(_):
    conf = config.generate_config({'unis': 'http://localhost:8888',
                                   'wsapi': '127.0.0.1:8080',
                                   'remote': 'http://localhost:8888',
                                   'topology': 'Local Topology',
                                   'domain': 'ZOF Domain',
                                   'of_port': 6653})

    APP.SDN = SDN_Handler(runtime_url=conf['unis'],
        domain_name=conf['domain'])

    APP.website = None 
    warnings.filterwarnings('ignore')

    APP.logger.info("\nStarting ZOF Topology Controller\n \
        Local UNIS: " + conf['unis'] + "\n \
        Remote UNIS: " + conf['remote'] +"\n \
        Remote Topology Name: " + conf['topology'] +"\n\
        Domain Name: " + conf['domain'] +"\n\
        REST API Endpoint: "+ conf['wsapi'])


    # Registration check/update domain/topology resources. 
    RegHandler = RegistrationHandler(APP.SDN.rt, conf['remote'])
    
    APP.logger.info("Checking Local Topology and Domain")
    local_topology      = RegHandler.check_local_topology("Local Topology")
    local_domain        = RegHandler.check_local_domain(conf['domain'], local_topology)
    
    APP.logger.info("Attempting to register domain to remote topology")
    remote_topology     = RegHandler.register_remote(conf['topology'], local_domain)

    if not local_topology or not local_domain or not remote_topology:
        APP.logger.info("ERROR - problem with startup local or remote registration.")
    else:
        APP.logger.info("Successfully registered topology and domain")

    RegHandler.clean_up()

    APP.SDN.domain_name = APP.args.domain
    APP.SDN.local_domain = local_domain

'''
@APP.message('packet_in', eth_type=0x88cc)
def lldp_packet_in(event):
    #APP.logger.info("LLDP message %r", event)
    SDN.handle_lldp(event)
    return
'''

@APP.message('packet_in')
def generic_packet_handler(event):
        
    pkt = event['msg']['pkt']
    
    APP.logger.info("-- PACKET IN EVENT --")
        
    APP.logger.info("\n     eth_src: %s\n\
        eth_dst: %s\n\
        eth_type: %d", pkt['eth_src'], pkt['eth_dst'], pkt['eth_type'])
    
    if pkt['eth_type'] == int(35020):
        APP.logger.info("Recieved LLDP Packet")
        APP.SDN.handle_lldp(event)
    
    return

@APP.message('channel_up')
def channel_up(event):
    
    APP.logger.info("switch %s Connected", event['datapath_id'])  
    
    APP.logger.info("Inserting OUTPUT_NORMAL_FLOW")
    OUTPUT_NORMAL_FLOW.send()

    APP.logger.info("Inserting LLDP_FLOW")
    LLDP_FLOW.send()
    
    APP.SDN.handle_switch_enter(event)

OUTPUT_NORMAL_FLOW = zof.compile('''
  # Add permanent flow entry to table 0
  type: FLOW_MOD
  msg:
    command: ADD
    table_id: 0
    priority: 0
    instructions:
      - instruction: APPLY_ACTIONS
        actions:
          - action: OUTPUT
            port_no: NORMAL 
            max_len: NO_BUFFER
''')

LLDP_FLOW = zof.compile('''
  # Add permanent table miss flow entry to table 0
  type: FLOW_MOD
  msg:
    command: ADD
    table_id: 0
    priority: 1 
    match:
      - field: ETH_TYPE 
        value: 35020 
    instructions:
      - instruction: APPLY_ACTIONS
        actions:
          - action: OUTPUT
            port_no: CONTROLLER
            max_len: NO_BUFFER
''')



if __name__ == '__main__': 
    zof.run()


