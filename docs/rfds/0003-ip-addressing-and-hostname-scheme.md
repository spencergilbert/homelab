# RFD 0003: IP Addressing and Hostname Scheme

<!-- RFD-META
Status: Draft
Date: 2025-10-05
Author: spencergilbert
-->

---

## Overview

This RFD establishes the IP addressing scheme and hostname conventions for the homelab network. It defines how IP addresses are allocated across infrastructure components, cluster nodes, and household devices, and sets naming conventions that scale with the infrastructure.

---

## Problem

I'm about to configure 4 RK1 nodes with static IP addresses, and need to establish a coherent addressing scheme before setting configurations that are painful to change later. The challenge is balancing several concerns:

**Immediate needs vs. future growth.** Right now I have one TuringPi 2 board with 4 RK1 modules and an x86 server arriving soon. But I also have a second TuringPi 2 board, leaving room for 4 more RK1 modules. The addressing scheme needs to work today without painting me into a corner for obvious next steps.

**Logical organization vs. simplicity.** I could organize IPs by hardware type (x86 vs ARM), by role (server vs client), by physical location (TuringPi board 1 vs 2), or just sequentially. Too much structure is premature optimization. Too little makes the network confusing as it grows.

**Router DHCP integration.** My ISP-provided router hands out DHCP addresses somewhere in the 192.168.1.x range. I need static IPs for cluster infrastructure that don't conflict with DHCP assignments to household devices (phones, laptops, etc.). I can either work around the existing DHCP range or reconfigure the router to shrink it.

**Hardware-agnostic design.** Per [RFD 0002](0002-initial-platform-hardware-orchestration-and-network-strategy.md), the nodes are substrate for Nomad — the orchestrator handles workload placement based on resources and constraints. IP addressing shouldn't encode assumptions about hardware architecture (x86 vs ARM) because that's not meaningful at the network layer. A node is a node.

**Changing IPs later is painful.** Once I set static IPs and configure systems to reference them (Nomad cluster config, SSH known_hosts, firewall rules, monitoring, etc.), changing them means updating multiple places and dealing with stale references. It's not impossible, but it's toil I'd rather avoid.

If I don't think this through now, I'll either:
- Pick arbitrary IPs and regret the lack of pattern later
- Create a scheme that's too clever and doesn't match how I actually use the network
- Conflict with DHCP and chase weird networking bugs
- Need to renumber everything when I add the second TuringPi board

What I need is a simple, logical scheme that works with my current router configuration (or justifies changing it), scales to obvious next steps, and treats nodes as role-based infrastructure rather than hardware-specific devices.

---

## Discussion

### Current Network State

The network is a simple flat topology with an ISP-provided router:

- **Network**: 192.168.1.0/24
- **Gateway**: 192.168.1.1
- **DHCP range**: (To be determined — checking router configuration)
- **Current assignments**:
  - TuringPi 2 BMC: 192.168.1.221 (DHCP-assigned)
  - Laptop: 192.168.1.186 (DHCP-assigned)

This is the "flat network" approach from RFD 0002 — no VLANs, no segmentation, everything on one subnet. Network upgrades (proper router, managed switch, VLANs) are a future project. For now, the addressing scheme needs to work within this flat topology.

### IP Range Allocation Strategy

The 192.168.1.0/24 network gives us 254 usable host addresses (.1 through .254). The question is how to carve this up logically.

**Option 1: Low-range static, high-range DHCP**

Reserve the low end (.1-.99 or .1-.149) for static infrastructure, leave the high end (.150-.254 or .100-.254) for DHCP.

Pros:
- Clear separation between static and dynamic
- Easy to remember: "anything below .100 is static infrastructure"
- Plenty of room for infrastructure growth
- Most routers don't DHCP from .1 by default anyway

Cons:
- Might require reconfiguring router DHCP range
- If router won't cooperate, need to use a different split

**Option 2: Use very low range to avoid router config**

Use .1-.49 for infrastructure, assume DHCP starts at .50 or higher.

Pros:
- Likely works without touching router settings
- Most consumer routers start DHCP at .100 or at least .50

Cons:
- Less room for infrastructure (only 48 addresses)
- Assumption about DHCP range might be wrong
- Doesn't scale as well long-term

**Option 3: Scattered ranges**

Put infrastructure in .10-.19, servers in .20-.29, nodes in .100+, etc.

Pros:
- Very organized categories

Cons:
- Overengineered for current scale
- Wastes address space with gaps
- Harder to remember the scheme

**Where I'm landing:**

**Use the .1-.149 range for static infrastructure, configure router DHCP to use .150-.254.**

This is the cleanest long-term approach. It gives 149 static addresses (way more than I'll ever need) and 105 DHCP addresses (plenty for household devices). The cutoff at .150 is easy to remember.

If the router won't let me reconfigure DHCP (some ISP routers are locked down), I'll fall back to using .10-.49 and accept the tighter constraints. But it's worth checking the router first.

### IP Allocation by Role

Within the static range, how should addresses be organized?

The key insight from thinking through this: **nodes are nodes, regardless of hardware**. The x86 server and the RK1 modules are all just Nomad cluster members. Some run server+client mode, some run client-only, but that's a Nomad concern, not a network concern.

**Proposed allocation:**

```
.1              Gateway (router)
.10-.19         Infrastructure (BMC, switches, future management interfaces)
.20-.99         Reserved for future infrastructure expansion
.100-.149       Cluster nodes (Nomad members, regardless of architecture)
.150-.254       DHCP pool for household devices
```

**Specific assignments (initial):**

```
192.168.1.1     Gateway (router)
192.168.1.10    turingpi-bmc-1 (TuringPi 2 board 1 BMC)
192.168.1.11    turingpi-bmc-2 (TuringPi 2 board 2 BMC, future)

192.168.1.101   node1 (x86 server, Nomad server+client)
192.168.1.102   node2 (RK1 on board 1 slot 1, Nomad client)
192.168.1.103   node3 (RK1 on board 1 slot 2, Nomad client)
192.168.1.104   node4 (RK1 on board 1 slot 3, Nomad client)
192.168.1.105   node5 (RK1 on board 1 slot 4, Nomad client)
192.168.1.106   node6 (future: RK1 on board 2 slot 1)
...
192.168.1.149   (room for 49 total nodes)
```

This scheme is architecture-agnostic. The x86 server is node1 not because it's special hardware, but because it's the first node configured. The RK1s are node2-5. If I add another x86 box later, it's node6 or whatever the next number is.

The .100+ range makes nodes easy to identify ("anything in the 100s is a cluster node") while keeping them separate from infrastructure (.10s) and future expansion space (.20-.99).

### Hostname Conventions

**Requirements:**
1. Quickly identify node location (local vs cloud provider)
2. Essentially infinite pool of unique names
3. Short prefixes (2-4 characters)

**For infrastructure:**
- `turingpi-bmc-1` - Descriptive, indicates hardware and instance number
- `turingpi-bmc-2` - Scales for second board

**For cluster nodes - Location-prefixed celestial names:**

**Prefix scheme:**
- `lab-` - Local hardware
- `aws-` - Amazon Web Services
- `gcp-` - Google Cloud Platform
- `az-` - Microsoft Azure
- `do-` - DigitalOcean

**Naming pattern:** `<prefix>-<celestial-body>`

**Examples (with variety of celestial types):**
- Planets: `lab-mercury`, `lab-venus`, `lab-jupiter`, `lab-mars`
- Moons: `lab-io`, `lab-europa`, `lab-titan`, `lab-ganymede`
- Stars: `lab-sirius`, `lab-polaris`, `lab-vega`, `lab-betelgeuse`
- Asteroids: `lab-ceres`, `lab-vesta`, `lab-pallas`
- Cloud: `aws-rigel`, `gcp-antares`, `az-deneb`

**Rationale:**

Short prefixes identify location at a glance. Celestial names provide memorable, opaque identifiers with an effectively infinite namespace. DNS handles IP resolution - no need to memorize mappings.

**Fully-qualified domain names (future):**

For now, nodes are just `node1`, `node2`, etc. with no domain suffix. If I set up internal DNS later (via Consul, CoreDNS, or similar), I might use something like `node1.homelab.internal`. But that's a future concern — local hostnames work fine for now.

### DNS and Name Resolution

Currently relying on:
- **mDNS** (Avahi) for `.local` resolution (`turingpi.local` → 192.168.1.221)
- **Router DNS** for anything else (forwards to ISP DNS)
- **/etc/hosts** on individual machines as needed

This is fine for initial setup. As the cluster grows, I might want:
- Internal DNS server (CoreDNS, dnsmasq, or Consul DNS)
- Proper zone files for homelab.internal or similar
- DNS-based service discovery integrated with Nomad

But that's a future enhancement. For now, static IPs in /etc/hosts and mDNS for BMC access is sufficient.

### Router DHCP Configuration

The critical question: what DHCP range is the router currently using, and can I change it?

If the router allows reconfiguring DHCP to .150-.254, great — the scheme above works perfectly.

If the router is locked down or won't cooperate, fallback plan:
- Use .10-.49 for infrastructure/nodes
- Accept that this limits scaling to ~40 static IPs
- Revisit when router is replaced (per RFD 0002 future network upgrade)

The scheme is designed to work either way, just with different ranges.

### Changing IPs Later

What if this scheme doesn't work out and I need to renumber?

The pain points of changing IPs:
- Nomad server/client configs reference IPs (or hostnames that resolve to IPs)
- SSH known_hosts files have IP-based entries
- Firewall rules might reference specific IPs
- Monitoring/observability systems track by IP
- Any hardcoded references in scripts or docs

Mitigation strategies:
- **Use hostnames in configs where possible** - Nomad can use hostnames instead of IPs for server addresses, making renumbering less painful
- **Keep /etc/hosts accurate** - If configs use hostnames, changing the IP just means updating /etc/hosts (and DNS if/when that exists)
- **Document the scheme** - This RFD serves as the source of truth for IP allocation

If I do need to renumber later, the process would be:
1. Update static IP on each node
2. Update /etc/hosts on all nodes
3. Update Nomad configs (if using IPs directly)
4. Clear SSH known_hosts
5. Update any monitoring/firewall configs

It's not catastrophic, just annoying. The goal is to pick a scheme that minimizes the likelihood of needing to do this.

---

## Proposed Direction

The homelab uses the following IP addressing and hostname scheme:

### IP Allocation

**Network:** 192.168.1.0/24

**Static Range:** 192.168.1.1 - 192.168.1.149
- `.1` - Gateway (router)
- `.10-.19` - Infrastructure (BMC, switches, management interfaces)
- `.20-.99` - Reserved for future infrastructure
- `.100-.149` - Cluster nodes (Nomad members, architecture-agnostic)

**DHCP Range:** 192.168.1.150 - 192.168.1.254
- Household devices (phones, laptops, IoT, guests)

**Initial Assignments:**

| IP | Hostname | Description |
|----|----------|-------------|
| 192.168.1.1 | gateway | ISP router |
| 192.168.1.10 | turingpi-bmc-1 | TuringPi 2 board 1 BMC |
| 192.168.1.11 | turingpi-bmc-2 | TuringPi 2 board 2 BMC (future) |
| 192.168.1.101 | lab-sirius | x86 server (Nomad server+client, future) |
| 192.168.1.102 | lab-mercury | RK1 module (Nomad client) |
| 192.168.1.103 | lab-venus | RK1 module (Nomad client) |
| 192.168.1.104 | lab-mars | RK1 module (Nomad client) |
| 192.168.1.105 | lab-jupiter | RK1 module (Nomad client) |

### Hostname Conventions

- **Infrastructure:** Descriptive names indicating hardware type and instance number (`turingpi-bmc-1`)
- **Cluster nodes:** Pure sequential (`node1`, `node2`, ...) regardless of hardware architecture or Nomad role
- **No domain suffix:** Use simple hostnames for now; add `.homelab.internal` or similar if internal DNS is implemented later

### Router Configuration

Configure ISP router DHCP server to use range 192.168.1.150 - 192.168.1.254.

If router does not allow DHCP reconfiguration, fallback to using .10-.49 for static infrastructure and accept reduced scaling headroom.

### Name Resolution

- **mDNS (Avahi):** For `.local` resolution (e.g., `turingpi-bmc-1.local`)
- **Manual /etc/hosts:** For cluster nodes to resolve each other by hostname
- **Future:** Internal DNS server (CoreDNS, dnsmasq, Consul DNS) when cluster complexity justifies it

---

## Outcome

The IP addressing scheme has been adopted as proposed.

**Router DHCP Configuration (Verizon CR1000A):**
- DHCP range configured to: 192.168.1.150 - 192.168.1.254
- Previous range was: 192.168.1.2 - 192.168.1.254
- Static range (.1-.149) is now free for infrastructure use

**Implementation Notes:**
- Existing DHCP leases in the .2-.149 range will gradually migrate to .150+ as they renew
- No immediate impact on connected devices
- Static IP assignments can now proceed without conflict risk

**Scope:**
- This RFD addresses IPv4 addressing only
- IPv6 is left as future consideration if specific needs arise or as a learning project

---

## References

- [RFD 0002: Initial Platform: Hardware, Orchestration, and Network Strategy](0002-initial-platform-hardware-orchestration-and-network-strategy.md) - Context on flat network topology and future network upgrade plans
