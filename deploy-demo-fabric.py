#!/usr/bin/env python3
"""
Netris Spectrum-X CloudSim Demo Fabric Deployer
Dynamically inspects the Netris Controller, resolves non-conflicting IPAM/ASNs,
creates an isolated data centre workspace, writes standard terraform.tfvars,
and automatically initialises and plans OpenTofu/Terraform.
"""

import argparse
import ipaddress
import json
import os
import re
import shutil
import string
import subprocess
import sys
import urllib.request
import urllib.error

# Environment defaults (can be overridden via ENV or CLI arguments)
DEFAULT_URL = os.environ.get("NETRIS_URL", "http://localhost")
DEFAULT_USER = os.environ.get("NETRIS_USER", "netris")
DEFAULT_PASS = os.environ.get("NETRIS_PASS", "913QGAi6oQTSGgZm20eU")


def get_auth_cookie(base_url, username, password):
    auth_data = json.dumps({"user": username, "password": password}).encode()
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/auth",
        data=auth_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.headers.get("Set-Cookie").split(";")[0]


def api_get(base_url, endpoint, cookie):
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}{endpoint}",
        headers={"Cookie": cookie, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_next_dc_letter(existing_sites):
    used = set()
    for name in existing_sites:
        m = re.search(r"Datacenter-([A-Z])", name, re.IGNORECASE)
        if m:
            used.add(m.group(1).upper())
    for letter in string.ascii_uppercase:
        if letter not in used:
            return letter
    return "X"


def find_free_subnet(existing_subnets, supernet_str, prefix_len):
    """
    Finds the first subnet of prefix_len inside supernet_str that does not overlap
    with any existing subnets on the controller.
    """
    supernet = ipaddress.ip_network(supernet_str)
    for candidate in supernet.subnets(new_prefix=prefix_len):
        if not any(candidate.overlaps(ext) for ext in existing_subnets):
            existing_subnets.append(candidate)
            return candidate
    raise RuntimeError(f"Exhausted pool inside {supernet_str} for /{prefix_len}")


def find_free_allocation(existing_allocs, supernet_str, prefix_len):
    """
    Finds a non-overlapping IP prefix for top-level netris_allocation resources.
    """
    supernet = ipaddress.ip_network(supernet_str)
    for candidate in supernet.subnets(new_prefix=prefix_len):
        if not any(candidate.overlaps(ext) for ext in existing_allocs):
            existing_allocs.append(candidate)
            return candidate
    raise RuntimeError(f"Exhausted pool inside {supernet_str} for /{prefix_len}")


def patch_repo_templates(dest_dir, site_name, leaf_asn_start, spine_asn_start):
    """
    Ensures unique hardware, switch, profile, and template names across data centres.
    In Netris, all Hardware names are globally unique across the entire controller.
    """
    pfx = site_name.lower()

    # 1. Server cluster template
    sct_file = os.path.join(dest_dir, "server-cluster-template.tf")
    if os.path.exists(sct_file):
        with open(sct_file, "r") as f:
            content = f.read()
        patched = re.sub(
            r'name\s*=\s*"server-cluster-template"',
            f'name  = "{pfx}-cluster-template"',
            content
        )
        with open(sct_file, "w") as f:
            f.write(patched)

    # 2. East-West Switches, Profiles, Allocations, and ASNs
    ew_file = os.path.join(dest_dir, "east-west.tf")
    if os.path.exists(ew_file):
        with open(ew_file, "r") as f:
            content = f.read()
        # Profiles
        patched = re.sub(
            r'resource "netris_inventory_profile" "inv-profile-1" \{\s*\n\s*name\s*=\s*"[^"]+"',
            f'resource "netris_inventory_profile" "inv-profile-1" {{\n  name                            = "{site_name}-East-West"',
            content
        )
        # Allocation name
        patched = re.sub(
            r'resource "netris_allocation" "private-ip-allocation" \{\s*\n\s*name\s*=\s*"[^"]+"',
            f'resource "netris_allocation" "private-ip-allocation" {{\n  name                            = "{site_name} Private IP Allocation"',
            patched
        )
        # ASNs
        patched = re.sub(
            r'leaf-asn-start\s*=\s*\d+',
            f'leaf-asn-start                  = {leaf_asn_start}',
            patched
        )
        patched = re.sub(
            r'spine-asn-start\s*=\s*\d+',
            f'spine-asn-start                 = {spine_asn_start}',
            patched
        )
        # Switch names
        patched = re.sub(r'name\s*=\s*"leaf-pod00-', f'name                            = "{pfx}-leaf-pod00-', patched)
        patched = re.sub(r'name\s*=\s*"spine-\$\{count\.index\}-pod00"', f'name                            = "{pfx}-spine-${{count.index}}-pod00"', patched)
        with open(ew_file, "w") as f:
            f.write(patched)

    # 3. North-South Switches, SoftGates, and Profiles
    ns_file = os.path.join(dest_dir, "north-south.tf")
    if os.path.exists(ns_file):
        with open(ns_file, "r") as f:
            content = f.read()
        # Profile name
        patched = re.sub(
            r'resource "netris_inventory_profile" "inv-profile-north-south" \{\s*\n\s*count\s*=\s*var\.north-south-fabric\.enable\s*\n\s*name\s*=\s*"[^"]+"',
            f'resource "netris_inventory_profile" "inv-profile-north-south" {{\n  count                           = var.north-south-fabric.enable\n  name                            = "{site_name}-North-South"',
            content
        )
        # Switch and SoftGate names
        patched = re.sub(r'name\s*=\s*"ns-leaf-', f'name                            = "{pfx}-ns-leaf-', patched)
        patched = re.sub(r'name\s*=\s*"ns-oob-leaf-', f'name                            = "{pfx}-ns-oob-leaf-', patched)
        patched = re.sub(r'name\s*=\s*"ns-spine-', f'name                            = "{pfx}-ns-spine-', patched)
        patched = re.sub(r'name\s*=\s*"ns-softgate-', f'name                            = "{pfx}-ns-softgate-', patched)
        with open(ns_file, "w") as f:
            f.write(patched)

    # 4. BGP Sessions, Network Interfaces, and SoftGate references
    bgp_file = os.path.join(dest_dir, "bgp.tf")
    if os.path.exists(bgp_file):
        with open(bgp_file, "r") as f:
            content = f.read()
        # Allocation names
        patched = re.sub(
            r'resource "netris_allocation" "public-nat-allocation" \{\s*\n\s*name\s*=\s*"[^"]+"',
            f'resource "netris_allocation" "public-nat-allocation" {{\n  name                            = "{site_name} Public NAT Allocation"',
            content
        )
        patched = re.sub(
            r'resource "netris_allocation" "public-l4lb-allocation" \{\s*\n\s*name\s*=\s*"[^"]+"',
            f'resource "netris_allocation" "public-l4lb-allocation" {{\n  name                            = "{site_name} Public L4LB Allocation"',
            patched
        )
        # Network interface targeting new leaf switch name
        patched = re.sub(r'swp51s(\d+)@ns-leaf-0', rf'swp51s\1@{pfx}-ns-leaf-0', patched)
        # SoftGate hardware reference
        patched = re.sub(r'hardware\s*=\s*"ns-softgate-(\d+)"', rf'hardware                        = "{pfx}-ns-softgate-\1"', patched)
        with open(bgp_file, "w") as f:
            f.write(patched)


def find_binary():
    if shutil.which("tofu"):
        return "tofu"
    if shutil.which("terraform"):
        return "terraform"
    return "/usr/local/bin/tofu"


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Netris Spectrum-X AI Fabric with collision avoidance"
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="Netris Controller URL")
    parser.add_argument("--user", default=DEFAULT_USER, help="Netris Username")
    parser.add_argument("--password", default=DEFAULT_PASS, help="Netris Password")
    parser.add_argument("--letter", help="Explicit DC letter (e.g. B, C, D)")
    parser.add_argument("--site-name", help="Custom site name (defaults to Datacenter-<Letter>)")
    parser.add_argument("--no-tofu", action="store_true", help="Do not run tofu automatically")
    parser.add_argument("--apply", action="store_true", help="Run tofu apply instead of plan")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"[*] Interrogating Netris Controller at {args.url}...")
    try:
        cookie = get_auth_cookie(args.url, args.user, args.password)
    except Exception as e:
        print(f"[!] Authentication failed: {e}")
        sys.exit(1)

    # 1. Fetch sites and public ASNs
    sites_res = api_get(args.url, "/api/v2/sites", cookie).get("data", [])
    existing_site_names = [s.get("name") for s in sites_res]
    existing_site_asns = {s.get("publicAsn") for s in sites_res if s.get("publicAsn")}

    letter = args.letter.upper() if args.letter else get_next_dc_letter(existing_site_names)
    site_name = args.site_name or f"Datacenter-{letter}"
    site_asn = max(existing_site_asns or [655000]) + 1

    # 2. Fetch existing Allocations
    allocs_res = api_get(args.url, "/api/v2/ipam", cookie).get("data", [])
    existing_allocs = []
    for item in allocs_res:
        p = item.get("prefix")
        if p:
            try:
                existing_allocs.append(ipaddress.ip_network(p))
            except ValueError:
                pass

    # 3. Fetch existing Subnets
    subnets_res = api_get(args.url, "/api/v2/ipam/subnets", cookie).get("data", [])
    existing_subnets = []
    for item in subnets_res:
        p = item.get("prefix")
        if p:
            try:
                existing_subnets.append(ipaddress.ip_network(p))
            except ValueError:
                pass

    # 4. Fetch existing HW ASNs
    hw_res = api_get(args.url, "/api/v2/hw", cookie).get("data", [])
    used_hw_asns = {h.get("asn") for h in hw_res if h.get("asn")}

    # Calculate collision-free top-level allocations across multiple supernets
    private_alloc = None
    for cand_supernet in ["172.18.0.0/15", "172.20.0.0/14", "172.24.0.0/13"]:
        try:
            private_alloc = find_free_allocation(existing_allocs, cand_supernet, 16)
            break
        except RuntimeError:
            continue
    if not private_alloc:
        raise RuntimeError("Could not find free /16 private allocation block")

    nat_alloc = find_free_allocation(existing_allocs, "100.64.0.0/10", 30)
    l4lb_alloc = find_free_allocation(existing_allocs, "100.64.0.0/10", 30)

    # Calculate subnets inside private_alloc:
    oob_mgmt = find_free_subnet(existing_subnets, str(private_alloc), 18)
    switch_lo = find_free_subnet(existing_subnets, str(private_alloc), 24)

    # North-South subnets (/16 from 10.0.0.0/8)
    ns_lo = find_free_subnet(existing_subnets, "10.0.0.0/8", 16)
    ns_mgmt = find_free_subnet(existing_subnets, "10.0.0.0/8", 16)

    # GPU server workload subnets (/21 inside 192.168.0.0/16)
    gpu_ns = find_free_subnet(existing_subnets, "192.168.0.0/16", 21)
    gpu_ipmi = find_free_subnet(existing_subnets, "192.168.0.0/16", 21)

    # Calculate gateways
    oob_gw = str(list(oob_mgmt.hosts())[-1])
    gpu_ns_gw = f"{list(gpu_ns.hosts())[-1]}/21"
    gpu_ipmi_gw = f"{list(gpu_ipmi.hosts())[-1]}/21"

    # Calculate distinct starting ASNs for all switch tiers
    ew_leaf_asn = 4200100001
    while any((ew_leaf_asn + offset) in used_hw_asns for offset in range(100)):
        ew_leaf_asn += 1000

    ew_spine_asn = 4200200001
    while any((ew_spine_asn + offset) in used_hw_asns for offset in range(100)):
        ew_spine_asn += 1000

    ns_switch_asn = 4200300001
    while any((ns_switch_asn + offset) in used_hw_asns for offset in range(300)):
        ns_switch_asn += 1000

    print(f"\n[+] Resolved Isolated Parameters:")
    print(f"    - Site Name:        {site_name}")
    print(f"    - Site Public ASN:  {site_asn}")
    print(f"    - Private Alloc:    {private_alloc}")
    print(f"    - NAT Pool Alloc:   {nat_alloc}")
    print(f"    - L4LB Pool Alloc:  {l4lb_alloc}")
    print(f"    - OOB Management:   {oob_mgmt} (GW: {oob_gw})")
    print(f"    - Switch Loopbacks: {switch_lo}")
    print(f"    - N-S Fabric Lo:    {ns_lo}")
    print(f"    - N-S Fabric Mgmt:  {ns_mgmt}")
    print(f"    - Workload Fabric:  {gpu_ns} (GW: {gpu_ns_gw})")
    print(f"    - Workload IPMI:    {gpu_ipmi} (GW: {gpu_ipmi_gw})")
    print(f"    - E-W Leaf Start ASN:  {ew_leaf_asn}")
    print(f"    - E-W Spine Start ASN: {ew_spine_asn}")
    print(f"    - N-S Switch Start ASN: {ns_switch_asn}")

    tfvars_body = f"""###################################################################################################
#  Standard terraform.tfvars - Auto-generated for {site_name}
###################################################################################################

controller_url                    = "{args.url}"
netris_controller_password        = "{args.password}"

gpu-server-count                  = 64
gpu-server-hostname               = "hgx-{letter.lower()}"
site-name                         = "{site_name}"

site = {{
    publicasn                       = {site_asn}
    acldefaultpolicy                = "permit"
    rohroutingprofile               = "default_agg"
    sitemesh                        = "disabled"
    vlanrangeautoassign             = "2-3999"
}}

pnap_ipam_public = {{
    default_route                   = "0.0.0.0/0"
    netris_cloudsim_nat_cidr        = "{nat_alloc}"
    netris_cloudsim_l4lb_cidr       = "{l4lb_alloc}"
}}

ipam = {{
    private-allocation              = "{private_alloc}"
    mgmt                            = "{oob_mgmt}"
    mgmt-gateway                    = "{oob_gw}"
    switch-loopback                 = "{switch_lo}"
}}

north-south-fabric = {{
    enable                          = 1
    leaf-count                      = 2
    leaf-port-count                 = 64
    leaf-port-breakout              = 4
    leaf-to-spine-link-count        = 4
    leaf-to-spine-start-port        = 192
    oob-leaf-count                  = 2
    oob-first-gpu-port              = 0
    oob-first-cpu-port              = 32
    oob-gpu-per-switch              = 32
    oob-cpu-per-switch              = 16
    oob-uplink-into-spine           = 1
    softgate-count                  = 4
    softgate-roles                  = ["general", "general", "snat", "snat"]
    softgate-leaf-list              = [0, 1]
    leaf-to-softgate-start-port     = 176
    spine-count                     = 2
    spine-port-count                = 64
    spine-port-breakout             = 4
    cpu-group-1-count               = 0
    cpu-group-1-name-pfx            = "BCM"
    cpu-group-2-count               = 0
    cpu-group-2-name-pfx            = "RUN"
    cpu-group-3-count               = 0
    cpu-group-3-name-pfx            = "SLOGIN"
    cpu-group-4-count               = 0
    cpu-group-4-name-pfx            = "STORAGE"
    lo-subnet                       = "{ns_lo}"
    mgmt-subnet                     = "{ns_mgmt}"
    gpu-server-ns-subnet            = "{gpu_ns}"
    gpu-server-ns-nexthop           = "{gpu_ns_gw}"
    gpu-server-ipmi-subnet          = "{gpu_ipmi}"
    gpu-server-ipmi-nexthop         = "{gpu_ipmi_gw}"
    asn-start                       = {ns_switch_asn}
}}
"""

    parent_dir = os.path.dirname(script_dir)
    target_dir = os.path.join(parent_dir, f"netris-spectrum-x-{site_name.lower()}")

    print(f"\n[*] Staging new deployment folder: {target_dir}")
    if not os.path.exists(target_dir):
        shutil.copytree(
            script_dir,
            target_dir,
            ignore=shutil.ignore_patterns(".terraform*", "*.tfstate*", ".git*")
        )
    else:
        print(f"[*] Target directory already exists, refreshing files...")

    # Patch server cluster template, switch names, profile names, and ASN offsets
    patch_repo_templates(target_dir, site_name, ew_leaf_asn, ew_spine_asn)

    # Standard terraform.tfvars (no -var-file needed)
    tfvars_path = os.path.join(target_dir, "terraform.tfvars")
    with open(tfvars_path, "w") as f:
        f.write(tfvars_body)

    # Also write demo-AI-fabric.tfvars
    demo_vars_path = os.path.join(target_dir, "demo-AI-fabric.tfvars")
    with open(demo_vars_path, "w") as f:
        f.write(tfvars_body)

    # Clear terraform.auto.tfvars so it doesn't override dynamic public pools
    auto_vars_path = os.path.join(target_dir, "terraform.auto.tfvars")
    if os.path.exists(auto_vars_path):
        os.remove(auto_vars_path)

    # Record target_dir for run-demo.sh wrapper
    with open(os.path.join(script_dir, ".last_deploy_dir"), "w") as f:
        f.write(target_dir)

    print(f"[✓] Written standard variable file: {tfvars_path}")
    print(f"[✓] Written demo-AI-fabric.tfvars:   {demo_vars_path}")

    # Step into folder and execute OpenTofu
    if not args.no_tofu:
        bin_path = find_binary()
        print(f"\n" + "=" * 70)
        print(f"[*] Executing in {target_dir}: {bin_path} init")
        print("=" * 70 + "\n")
        
        ret = subprocess.call([bin_path, "init"], cwd=target_dir)
        if ret != 0:
            print(f"[!] '{bin_path} init' exited with code {ret}")
            sys.exit(ret)

        tofu_cmd = [bin_path, "apply", "-auto-approve"] if args.apply else [bin_path, "plan"]
        print(f"\n" + "=" * 70)
        print(f"[*] Executing in {target_dir}: {' '.join(tofu_cmd)}")
        print("=" * 70 + "\n")
        
        ret = subprocess.call(tofu_cmd, cwd=target_dir)
        if ret != 0:
            print(f"[!] '{' '.join(tofu_cmd)}' exited with code {ret}")
            sys.exit(ret)

    print(f"\n[✓] Deployment directory ready: {target_dir}")


if __name__ == "__main__":
    main()
