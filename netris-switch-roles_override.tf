###################################################################################################
#  NETRIS Terraform Module for 2-tier Nvidia Spectrum-X switch-fabric for GPU cluster use case    #
#  Version: 1.9.1                                                                                 #
###################################################################################################

resource "netris_switch" "east-west-leaf" {
  role = "leaf"
}

resource "netris_switch" "east-west-spine" {
  role = "spine"
}

resource "netris_switch" "north-south-leaf" {
  role = "leaf"
}

resource "netris_switch" "north-south-spine" {
  role = "spine"
}

