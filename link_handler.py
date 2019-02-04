from unis import Runtime
from unis.models import Link

class LinkHandler(object):
    def __init__(self, runtime):
        self.rt = runtime
        return

    def check_link_connecting_ports(self, port_a, port_b):

        link = self.rt.links.first_where(lambda l: l.endpoints[0] == port_a and l.endpoints[1] == port_b)
        
        if link is not None:
            print(link.id)
            print("Found link %s, connecting ports %s and %s." % (link.name, port_a.name, port_b.name))
            return link

        link = self.rt.links.first_where(lambda l: l.endpoints[1] == port_a and l.endpoints[0] == port_b)

        if link is not None:
            print(link.id)
            print("Found link %s, connecting ports %s and %s." % (link.name, port_a.name, port_b.name))
            return link
        
        print("Could not find link connecting ports %s and %s." % (port_a.name, port_b.name))

        return None

    def create_new_link(self, port_a, port_b):

        new_link = Link({
                "name": port_a.id + ":" + port_b.id,
                "directed": False,
                "endpoints": [port_a, port_b]
            })

        new_link.endpoints = [port_a, port_b] 
        
        return new_link
