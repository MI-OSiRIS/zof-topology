from unis import Runtime
from unis.models import *
from pprint import pprint

from util import UnisUtil
from link_handler import LinkHandler

OFSwitchNode = schemaLoader.get_class("http://unis.crest.iu.edu/schema/ext/ofswitch/1/ofswitch#")

class SDN_Handler(object):
    
    def __init__(self, runtime_url=None, domain_name=None):
        
        # Connect to runtime
        try:
            if runtime_url is not None:
                self.rt = Runtime(runtime_url, name="zof")
            else:
                print("Connecting to localhost...")
                self.rt = Runtime("http://localhost:8888")
        except Exception as e:
            print(e)
            raise Exception("Could not connect to runtime.")
        
        self.switches = []
        self.util         = UnisUtil(self.rt)
        self.link_handler = LinkHandler(self.rt)

    def handle_switch_enter(self, event):
        try:
            dpid   = event['datapath'].id
            switch = self.util.check_switch_exists(dpid)
        except:
            switch = None
            dpid   = event['datapath_id']

        if switch is None:
            print("Could not find Unis resource for , creating new resource")
            switch = self.util.create_new_switch(event) 
        else: 
            print("Found Unis resource for Datapath ID %s." % (switch.datapathid))
        
        print("Checking ports")
        self.util.check_switch_ports(switch, event)
        self.util.check_node_in_domain(switch, self.local_domain)

        self.rt.flush()

        return
    
    def handle_lldp(self, event):
        
        in_port = event['msg']['in_port']

        # checks to see if a node exists, and the corresponding port discovered via lldp
        node = self.util.check_lldp_msg(event['msg'])
        port_name = node.name + ":" + event['msg']['pkt']['x_lldp_port_descr']
        node_port = self.util.check_update_node(node, event['msg'])
       
        node_port.touch()
        node.touch()
        
        self.util.check_node_in_domain(node, self.local_domain)
        
        self.rt.flush() 

        switch_node = self.rt.nodes.first_where({"name": "switch:" + str(event['datapath'].id)})
        switch_port = self.util.find_port_in_node_by_port_num(switch_node, in_port)

        if switch_port is None:
            print("Could not find port in Switch. Continuing.")
            return
        if node_port is None:
            print("Could not find port in Node. Coninuting.")
            return

        # checks to see if a link between the src/dst ports via lldp exist.
        link = self.link_handler.check_link_connecting_ports(switch_port, node_port)

        if link is None:
            link = self.link_handler.create_new_link(port_a, port_b)

        link.touch()
        self.util.check_link_in_domain(link, self.local_domain)
        self.rt.flush()

        print("Finished LLDP Update.")

        return
