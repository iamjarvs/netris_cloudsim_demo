###################################################################################################
#  NETRIS Terraform Module for 2-tier NVIDIA Spectrum-X switch-fabric for GPU cluster use case    #
#  Version: 1.9.1                                                                                 #
###################################################################################################


controller_url                    = "http://localhost"

netris_controller_password        = "newNet0ps"

gpu-server-count                  = 64 #max 1024 (8K GPUs)
gpu-server-hostname               = "hgx" #gpu server hostname prefix
site-name                         = "Datacenter-A"

# server-ip-first-octet = 172

ipam                              = {
    private-allocation              = "10.0.0.0/8"
    mgmt                            = "10.253.0.0/18"
    mgmt-gateway                    = "10.253.63.254"
    switch-loopback                 = "10.253.128.0/24"
}

north-south-fabric                = {
    enable                          = 1    # 1 = Enable the fabric, 0 = Disable the Fabric
    #Leaf switches
    leaf-count                      = 2 # Number of leaf switches
    leaf-port-count                 = 64 # Number of switch ports before breakout
    leaf-port-breakout              = 4 # Switch port breakout factor
    leaf-to-spine-link-count        = 4 # Number of links between each spine and leaf
    leaf-to-spine-start-port        = 192 # First switch port (counting from 0), after breakout, to start leaf-spine links. 192=swp49s0
    #OOB
    oob-leaf-count                  = 2 # Number of OOB switches in the N-S fabric
    oob-first-gpu-port              = 0 # First port on OOB switch (counting from 0) for connecting GPU servers
    oob-first-cpu-port              = 32 # First port on OOB switch (counting from 0) for connecting CPU servers
    oob-gpu-per-switch              = 32 # How many GPU Servers per OOB switch
    oob-cpu-per-switch              = 16 # How many CPU Servers per OOB switch
    oob-uplink-into-spine           = 1 # 1 = uplink OOB switches to Spine switch; 0 = uplink OOB switches to Leaf switches
    #SoftGate
    softgate-count                  = 4 # Number of SoftGate nodes (minimum 2 for redundancy)
    softgate-roles                  = ["general", "general", "snat", "snat"] # Define SoftGate roles per each role
    softgate-leaf-list              = [0, 1] # Specify any two leaf switches for linking SoftGate nodes to
    leaf-to-softgate-start-port     = 176 # First switch port (counting from 0), after breakout, to start leaf-softgate links. 176=swp45s0
    #Spine switches
    spine-count                     = 2 # Number of spine switches
    spine-port-count                = 64 #Number of switch ports before breakout
    spine-port-breakout             = 4 # Switch port breakout factor
    #CPU servers
    cpu-group-1-count               = 0
    cpu-group-1-name-pfx            = "BCM"
    cpu-group-2-count               = 0
    cpu-group-2-name-pfx            = "RUN"
    cpu-group-3-count               = 0
    cpu-group-3-name-pfx            = "SLOGIN"
    cpu-group-4-count               = 0
    cpu-group-4-name-pfx            = "STORAGE"
    #IP and ASN
    lo-subnet                       = "10.2.0.0/16" # Subnet for loopback IPs
    mgmt-subnet                     = "10.3.0.0/16" # Subnet for Management IPs
    gpu-server-ns-subnet            = "192.168.0.0/21" # Subnet for GPU server NS fabric interfaces
    gpu-server-ns-nexthop           = "192.168.7.254/21" # Next hop for GPU server NS fabric interfaces
    gpu-server-ipmi-subnet          = "192.168.8.0/21" # Subnet for GPU server IPMI interface
    gpu-server-ipmi-nexthop         = "192.168.15.254/21" # Next hop for GPU server NS fabric interfaces
    asn-start                       = 4200300001 # Start ASN, every switch will have an individual ASN
}
