import argparse

from configparser import ConfigParser

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

def generate_config(default=None):
    cmd, default = _arg_parser().__dict__, default or {}
    default.update(**_read_config(cmd.get('config', None)))
    return {**default, **cmd}
    
