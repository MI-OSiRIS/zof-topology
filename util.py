from unis import Runtime
from unis.models import *
from pprint import pprint

OFSwitchNode = schemaLoader.get_class("http://unis.crest.iu.edu/schema/ext/ofswitch/1/ofswitch#")

class UnisUtil(object):
    
    def __init__(self, runtime):
        self.rt = runtime

    def check_switch_exists(self, dpid):
        switch = self.rt.nodes.first_where(lambda n: n.name == ("switch:" + str(dpid)))
        print(switch.to_JSON())
        return switch

    def check_switch_ports(self, switch, event):
        datapath_ports = event['msg']['features']['ports']

        for p in datapath_ports:
            p_name = "switch:" + str(event['datapath'].id) + ":" + p['name']
            p_num  = p['port_no']
            p_mac  = p['hw_addr']

            unis_port = self.port_in_switch(switch, p_name, p_num) 

            if unis_port is not None:
                print("FOUND PORT: %s in switch:%d" % (unis_port.name, event['datapath'].id))
                self.update_switch_port(unis_port, p)
            else:
                print("Could not find port %s" % (p_name))
                self.add_switch_port(switch, p)
        return

    def port_in_switch(self, node, port_name, port_number):
        try:
            for p in node.ports:
                if p.name == port_name and p.properties.vport_number == str(port_number):
                    return p
            return None
        except: 
            return None

    def check_port_in_node_by_name(self, node, port_name):
        for p in node.ports:
            if p.name == port_name:
                return p
        return None
    
    def create_new_switch(self, event):
        print(event)
        switch_name = "switch:" + str(event['datapath'].id)
        switch_ip   = event['msg']['endpoint'].split(':')[0]
        
        switch = OFSwitchNode({"name":switch_name, "datapath_id":event['datapath'].id})
        switch.properties.mgmtaddr = switch_ip

        self.rt.insert(switch, commit=True)

        return switch

    def update_switch_port(self, port, dp_port):
        
        port.properties = {
                    "type":"vport",
                    "vport_number": str(dp_port['port_no']),
                    "mac_addr":     dp_port['hw_addr']
                    #"supported":    dp_port['supported'],
                    #"curr_speed":   dp_port['curr_speed'],
                    #"max_speed":    dp_port['max_speed']
                }
        
        print("Updated port properties")
        
        return

    def add_switch_port(self, node, dp_port):
        
        port = Port({
            "name": "switch: " + node.name + ":" + dp_port['name']
            })

        port.properties = {
                    "type":"vport",
                    "vport_number": str(dp_port['port_no']),
                    "mac_addr":     dp_port['hw_addr']#,
                    #"supported":    dp_port['supported'],
                    #"curr_speed":   dp_port['curr_speed'],
                    #"max_speed":    dp_port['max_speed']
                }

        self.rt.insert(port, commit=True)
        node.ports.append(port)
        print("Added port %s to switch %s" % (dp_port['name'], node.name))
        return port

    def check_lldp_msg(self, msg, dpid):
        node_name = msg['pkt']['x_lldp_sys_name']
        print("Message from: ", node_name)
        
        node = self.rt.nodes.first_where({"name": node_name})
        
        if node:
            print("Found node in UNIS")
        else:
            print("Node not found in UNIS. Adding node")
            node = self.create_node(msg)

        return node
    
    def create_node(self, msg):
        
        new_node = Node({"name":msg['pkt']['x_lldp_sys_name'],
                         "description":"Discovered by ZOF Controller"})

        self.rt.insert(new_node, commit=True)
        self.rt.flush()

        return new_node

    def check_update_node(self, node, dp_msg):
        
        # check for port
        port_name = node.name + ":port:" + dp_msg['pkt']['x_lldp_port_descr']
        port = self.check_port_in_node_by_name(node, port_name)

        if port is not None:
            print("Found port %s in node %s" % (port.name, node.name))
        else:

            try:
                port = self.rt.ports.first_where(lambda p: p.name == port_name)
            except:
                port = None

            if port is None:
                print("No Port found. Adding port %s to node %s" % (str(port_name), str(node.name))) 
                port = Port({
                    "name": port_name
                    })

                self.rt.insert(port, commit=True)
                node.ports.append(port)
            
            else:
                print("Port found in UNIS, but not in Node, adding it to node.")
                node.ports.append(port)

        port.address = {
                    "type":"mac",
                    "address":dp_msg['pkt']['x_lldp_port_id'][3:]
                }
        port.properties = {
                    "type":"vport",
                    "vport_number":dp_msg['in_port']
                }


        return port
    
    def find_port_in_node_by_port_num(self, node, port_num):
        try:
            for p in node.ports: 
                if str(p.properties.vport_number) == str(port_num):
                    print("Found port in switch", p.properties.vport_number)
                    return p
            return None
        except:
            return None

    def check_node_in_domain(self, node, domain):
        result = None
        for n in domain.nodes:
            if n.id == node.id:
                result = node
                print("Found resourc in local domain")
        if result is None:
            print("Resource not in local domain, adding it now.")
            domain.nodes.append(node)
            self.rt.flush()

        return node

    def check_link_in_domain(self, link, domain):
        result = None
        for l in domain.links: 
            if l.id == link.id:
                result = link
                print("Found resource in local domain")
        if result is None:
            print("Resource not in local domain, adding it now.")
            domain.links.append(link)
            self.rt.flush()
        return link

