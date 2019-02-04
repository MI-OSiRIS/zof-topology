import zof
import argparse
import warnings
import json 

from zof.demo import rest_api

from sdn_handler import *
from registration_handler import *
from configparser import ConfigParser
from collections import defaultdict

def _arg_parser():
    parser = argparse.ArgumentParser(description="ZOF Topology Controller")
    parser.add_argument('-u','--unis',type=str, help="Local Unis to store domain topology resources.") 
    parser.add_argument('-r','--remote',type=str, help="Remote Unis url to register discovered topology")
    parser.add_argument('-d','--domain',type=str,  help="Name of domain resource for topology")
    parser.add_argument('-t','--topology',type=str,  help="Name of the topology object in the remote UNIS to register discovered domain to")
    parser.add_argument('-w','--wsapi',type=str,  help="Endpoint to server rest api. Default 127.0.0.1:8080")
    parser.add_argument('-c','--config',type=str,  help="Path to configuration file.")
    return parser

'''
        Read from Config File helper
'''
def _read_config(file_path):
    if not file_path:
        return {}
    parser = ConfigParser(allow_no_value=True)
    
    try:
        parser.read(file_path)
    except Exception:
        raise AttributeError("INVALID FILE PATH FOR STATIC RESOURCE INI.")
        return

    config = parser['CONFIG']
    try:
        result = {'unis': str(config['unis']),
                  'remote': str(config['remote']),
                  'wsapi': str(config['wsapi']),
                  'topology': str(config['topology']),
                  'domain': str(config['domain'])}
        return result

    except Exception as e:
        print(e)
        raise AttributeError('Error in config file, please ensure file is '
                             'formatted correctly and contains values needed.')

        
APP = zof.Application("TopologyController",
        arg_parser=_arg_parser())

SDN = SDN_Handler(runtime_url="http://iu-ps01.osris.org:8888", 
        domain_name="Zof")

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

@APP.event('start')
async def start(_):

    conf = {'unis': 'http://localhost:8888', 'wsapi': '127.0.0.1:8080', 'remote': 'http://localhost:8888',
                        'topology': 'Local Topology', 'domain': 'ZOF Domain'}

    conf.update(**_read_config(APP.args.config))
    conf.update(**{k:v for k,v in APP.args.__dict__.items() if v is not None})
    
    APP.http_endpoint = conf['wsapi'] 
    APP.website = None 
    warnings.filterwarnings('ignore')

    APP.logger.info("\nStarting ZOF Topology Controller\n \
        Local UNIS: " + conf['unis'] + "\n \
        Remote UNIS: " + conf['remote'] +"\n \
        Remote Topology Name: " + conf['topology'] +"\n\
        Domain Name: " + conf['domain'] +"\n\
        REST API Endpoint: "+ conf['wsapi'])

    # Registration check/update domain/topology resources. 
    RegHandler = RegistrationHandler(SDN.rt, conf['remote'])
    
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

    SDN.domain_name = APP.args.domain
    SDN.local_domain = local_domain

    await rest_api.WEB.start(APP.http_endpoint)

@APP.event('stop')
async def stop(_):
        await rest_api.WEB.stop()

@APP.message('packet_in', eth_type=0x88cc)
def lldp_packet_in(event):
    #APP.logger.info("LLDP message %r", event)
    SDN.handle_lldp(event)
    return

@APP.message('channel_up')
def channel_up(event):
    #APP.logger.info("switch %s Connected", event['datapath_id'])  
    SDN.handle_switch_enter(event)


if __name__ == '__main__': 
    zof.run()


