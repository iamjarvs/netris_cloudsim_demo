###################################################################################################
#  NETRIS Terraform Module for 2-tier Nvidia Spectrum-X switch-fabric for GPU cluster use case    #
#  Version: 1.9.1                                                                                 #
###################################################################################################

resource "netris_site" "site1" {
  rohasn            = null
  vmasn             = null
  rohroutingprofile = null
  sitemesh          = null
}
