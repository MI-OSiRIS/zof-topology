from configparser import ConfigParser

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

def generate_config(default, cmd):
    return {**default, **_read_config(cmd.get('config', None)), **{k:v for k,v in cmd.items() if v is not None}}
