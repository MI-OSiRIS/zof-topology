from unis import Runtime
from unis.models import *

class RegistrationHandler(object):

    def __init__(self, local_runtime_url, remote_runtime_url):
        self.local_rt  = Runtime(local_runtime_url, name="Local")
        self.remote_rt = Runtime(remote_runtime_url, name="Remote") 

    def check_local_topology(self, topology_name):
        
        local_topology = self.local_rt.topologies.first_where({"name": topology_name})

        if local_topology is not None:
            print("Found Local Topology", topology_name) 
        else:
            print("Local Topology not found. Creating new entry in local UNIS")

            local_topology = Topology({"name": topology_name})
            
            self.local_rt.insert(local_topology, commit=True)
            self.local_rt.flush()

        return local_topology

    def check_local_domain(self, domain_name, local_topology):

        local_domain = self.local_rt.domains.first_where({"name": domain_name}) 
        if local_domain is not None:
            print("Found Local Domain - ", domain_name)
        else:
            print("Local Domain - ", domain_name, ", not found. Creating new entry in local UNIS")

            local_domain = Domain({"name": domain_name})

            self.local_rt.insert(local_domain, commit=True)
            self.local_rt.flush()
        
        if local_domain in local_topology.domains:
            print("Domain already in local topology")
        else:
            print("Domain not in local topology, adding..")
            local_topology.domains.append(local_domain)
            self.local_rt.flush()

        return local_domain

    '''
        Upload local topology domain to remote UNIS instance.
        If no remote UNIS exists create the remote topology instance.
    '''
    def register_remote(self, topology_name, domain):

        remote_topology = self. remote_rt.topologies.first_where({"name": topology_name})
        
        if remote_topology is None:
            remote_topology = self.add_remote_topology(topology_name)            
        
        for d in remote_topology.domains:
            if d.id == domain.id: 
                print("Found domain " + domain.name + " in remote topology " + remote_topology.name  + ".")
                return remote_topology
        
        print("Domain " + domain.name + " not found in remote topology " + remote_topology.name + ", adding it to remote topology.")
        remote_topology.domains.append(domain)
        self.remote_rt.flush()

        return remote_topology

    def add_remote_topology(self, topology_name):
        
        remote_topology = Topology({"name": topology_name})
        self.remote_rt.insert(remote_topology, commit=True)
        self.remote_rt.flush()

        return remote_topology

    def clean_up(self):
        self.local_rt.flush()
        self.remote_rt.flush()

        
