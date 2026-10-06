###################################################################################################
#  NETRIS Terraform Module for 2-tier Nvidia Spectrum-X switch-fabric for GPU cluster use case    #
#  Version: 1.9.1                                                                                 #
###################################################################################################

terraform {
  required_providers {
    netris = {
      source  = "netrisai/netris"
      version = "=3.6.22"
    }
  }
}
