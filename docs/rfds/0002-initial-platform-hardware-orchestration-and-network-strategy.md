# RFD 0002: Initial Platform: Hardware, Orchestration, and Network Strategy

<!-- RFD-META
Status: Draft
Date: 2025-10-05
Author: spencergilbert
-->

---

## Overview

This RFD establishes the initial platform architecture for the homelab: what hardware to use and how, which orchestration platform to adopt, and how to approach networking given current limitations and learning goals.

It makes concrete decisions to get something running while preserving flexibility for evolution as understanding and needs develop.

---

## Problem

I'm starting a homelab with a collection of hardware that's been accumulating:
two TuringPi 2 boards, four RK1 compute modules, some older Raspberry Pi 3B+s,
and soon an x86 tower with decent storage. I want to actually use this stuff,
not just have it sit in boxes.

The challenge is that I have multiple goals that don't always align:

**Learning, especially networking.** I've managed servers in datacenters before,
and I'm comfortable with orchestration. I've run both k3s and Nomad on ARM
clusters previously. But networking is my weak spot, and I want to really learn
it this time. My current setup is an ISP-provided router with limited configuration
options. I know I need to upgrade eventually, but I'm not sure if that should
be step one or something I work up to.

**Utility without becoming a second job.** I want to run practical things, starting
with a DNS adblocker for my home network. I enjoy tinkering, writing glue code,
and configuring systems. That's part of the fun. But it shouldn't become an
obligation. If I stop messing with it for a few weeks, it should still work.
If the cluster breaks and my house falls back to Cloudflare DNS and we see ads
for a few days until I fix it, that's acceptable. I'd rather have something
simple that occasionally breaks than a complex high-availability setup that
demands constant attention.

Automation feels important. I don't want to SSH into boxes and run manual commands
for routine maintenance. But I also know that building automation upfront is its
own complexity burden. The right answer is probably somewhere in the middle:
start simple, automate the things that become painful.

**Exploration and fun, not just work-at-home.** I use Kubernetes at work. I've
used it at previous jobs. At home, I'm leaning toward Nomad. It's simpler, has
a lower resource footprint, and honestly it just feels more interesting to me
right now. But I have reservations: HashiCorp went BSL, IBM acquired them, and
the ecosystem is smaller than K8s. Is my "gut feeling" about Nomad enough to
justify potential long-term friction?

**The hardware question.** I have this collection of gear, but I'm not sure how
to use it or if I have enough. Should the x86 tower be a storage server? A Nomad
server node? Should I populate both TuringPi boards even though I only have four
RK1 modules? What about the old RPi 3B+s? Are they too underpowered to be useful,
or could they run lightweight services? And more broadly: do I have enough hardware
to build something useful, or should I be buying more storage, more compute, or
different gear entirely before I start?

**Starting simple, growing into complexity.** I'm open to (even excited about)
increasing complexity as I learn and the platform matures. But starting with too
much complexity upfront will paralyze progress. I need to make concrete initial
decisions that don't box me in, so the system can evolve as my understanding and
needs evolve.

If I don't think through these decisions now, I'll end up with one of these
failure modes:
- I recreate a datacenter at home and it becomes a chore instead of fun
- I under-plan and hit some architectural wall that requires starting over
- I over-engineer for problems I'll never actually have
- I let the hardware sit unused because I'm paralyzed by choices

What I need is a concrete plan that gets something running while preserving
flexibility to learn and evolve.

---

## Discussion

### Orchestration Platform Choice

I'm leaning toward Nomad, but I need to think through whether that's the right call given the tradeoffs.

**Why Nomad appeals to me:**

The simplicity is real. Nomad has a smaller surface area than Kubernetes. A single binary, straightforward configuration, and less cognitive overhead. I've run both k3s and Nomad before, and Nomad just feels lighter. There's less ceremony to get things running.

Resource footprint matters at home in a way it doesn't in a datacenter. Kubernetes (even k3s) consumes more memory and CPU for control plane components. With limited hardware, especially if I'm running control plane on the RK1 modules, every hundred megabytes matters.

The smaller ecosystem is a double-edged thing. Fewer Helm-chart-equivalent resources means I'll write more job specs myself, which I actually don't mind. But the lack of examples and community resources when I hit something unusual is a real cost.

But here's the honest part: it also just sounds more fun right now. I use Kubernetes at work every day. I'm competent with it, maybe even comfortable. At home, I want to explore something different. I want to learn Nomad more deeply, understand its constraints, see where it shines and where it frustrates me. That's a legitimate reason for a homelab, even if it creates some friction.

**The concerns (mostly ideological):**

HashiCorp's BSL license change bothers me. I understand their business needs, but I don't agree with the direction as a user. Practically though, it doesn't shut down my usage. I can still run Nomad, it's still free for my purposes, and the license doesn't affect homelabs. It's more about principle than actual impact.

IBM's acquisition adds uncertainty. Will they invest in Nomad? Let it languish? Honestly, if it just keeps working as-is, does it matter? Nomad is mature enough that even reduced investment wouldn't break my homelab. This concern is more ideological than practical.

**What about Kubernetes?**

K3s specifically would be the choice. Full Kubernetes would be overkill, but k3s strips it down to something homelab-appropriate. It's what I know. The ecosystem is huge. Everything has a Helm chart, examples are everywhere, and community support is massive.

But that's also the problem. Do I really want my homelab to be "work, but at home"? I get enough K8s exposure during the day. Using it at home feels like practicing scales when I could be learning a new instrument.

There's also the resource question. Even k3s is heavier than Nomad. On limited ARM hardware, that matters.

**Where I'm landing:**

I'm going with Nomad, but with eyes open about the tradeoffs. The BSL change bugs me on principle, but it doesn't block me practically. The IBM acquisition is uncertain, but not an immediate concern. The smaller ecosystem means less hand-holding, but I'm okay with that.

The key is accepting that I'm trading ecosystem maturity for simplicity, lower resource usage, and the learning experience I actually want. That's a valid homelab tradeoff.

If I was building production infrastructure for a company, I'd choose K8s without hesitation. But this is a homelab. Learning and fun are legitimate optimization targets.

### Hardware Topology and Sufficiency

With Nomad (or really any orchestrator), hardware largely doesn't matter upfront. You provide compute, it figures out how to use it. An ARM SBC, x86 desktop, or cloud VM are all just nodes with resources. The specific topology can emerge from actual usage rather than upfront planning.

But there are some real constraints that affect how I deploy:

**Storage and eMMC wear:**

The RK1 modules have 32GB eMMC storage. eMMC isn't particularly robust under heavy write loads, and here's the critical issue: Nomad servers write raft logs constantly. Every state change, job scheduling decision, health check update goes to disk. Running servers on eMMC nodes means wearing them out faster than I'd like.

The x86 tower has real disks (~3TB), not eMMC. That makes it a much better candidate for running Nomad servers.

But there's a tension: proper Nomad consensus needs 3 servers (odd number), and I only have one x86 box with robust storage.

Options:
- Single server on x86 (pragmatic, accept single point of failure)
- Add NVMe storage to TuringPi boards (solves the problem, costs money)
- Run 3 servers with 2 on eMMC (accept some wear, wonder if it's dying)
- External storage for RK1s (USB SSDs? Adds complexity)

I'm going with the first option: **single x86 server to start**. It's not ideal for high availability, but it's a homelab. Downtime is acceptable. This avoids the eMMC wear concern and gets me running quickly.

When I'm ready to expand to a proper 3-server cluster (either for reliability or to learn multi-server operations), I have options: add NVMe storage to the TuringPi boards, acquire additional x86 nodes with robust storage, or use a mix. The path forward will depend on what makes sense at that time.

**OS support:**

The RK1s can run modern Ubuntu according to TuringPi docs. Ubuntu isn't my favorite (I'd prefer something Red Hat-based), but it's the practical path for now. Maybe I'll experiment with other options later.

**Server+client mode:**

Nomad servers don't schedule jobs by default, but can run as server+client to avoid wasting resources. That risks resource contention affecting the control plane, but with a single server on the x86 tower, I have plenty of headroom. I'll run it as server+client.

If I expand to 3 servers later, I'll need to reconsider whether to keep them as server+client or separate the roles.

**What I actually have:**

- 2x TuringPi 2 boards (can hold 4 modules each)
- 4x RK1 modules (8GB RAM, 32GB eMMC, ARM)
- 4x Raspberry Pi 3B+ (older, lower power)
- 1x x86 tower (i7-8086K, 32GB RAM, ~3TB storage)

**Operating System choice:**

I run Fedora on my personal machines and prefer Red Hat-based distributions. I'm also interested in immutable OS variants (Fedora CoreOS, Fedora IoT). But here's the thing: if I'm doing this right, most of the "magic" should happen in the cluster (Nomad), not the underlying OS.

The nodes are just compute substrate. They run the Nomad agent and provide resources. The interesting work—service deployment, orchestration, configuration—happens at the cluster level, not the OS level.

From that perspective, OS choice matters less than I initially thought. What matters is:
- Does it run Nomad reliably?
- Is it well-supported on the hardware?
- Will I spend time fighting OS quirks instead of learning orchestration?

Ubuntu is well-documented on TuringPi hardware, has good ARM support, and I'm not unfamiliar with it. It's not my preference, but that preference matters more for a desktop or a server I'm directly administering. For cluster nodes that mostly just run a Nomad agent, Ubuntu is fine.

I can revisit this later. Maybe experiment with immutable variants on a node or two once the cluster is stable. But for initial deployment, Ubuntu everywhere is the practical choice that gets out of my way.

**Where I'm landing:**

Start with x86 tower as a single Nomad server+client. Use RK1s as client-only nodes for workloads. Keep writes off the eMMC as much as possible.

The RPi 3B+s might be too underpowered to be useful, but I can test that once the cluster is running.

When I add more robust storage or nodes, I'll expand to a 3-server topology for proper consensus. Until then, single-server is fine for a learning environment.

### Network Strategy

Networking is my weak spot, and I want to learn it properly this time. But I also need to balance learning goals with getting something running.

**Current state:**

I have an ISP-provided router with limited configuration options. No VLAN support, basic routing, minimal control. It works for a household network, but it's not what I'd use for a proper homelab setup.

**What I'd like eventually:**

Proper network segmentation. VLANs to isolate the homelab from the household network. Maybe separate subnets for different security zones (control plane, workloads, management). A managed switch. A router I actually control. The ability to experiment with firewall rules, routing policies, maybe even overlay networks like Tailscale or WireGuard for future multi-site connectivity.

Basically, I want to learn networking the way I learned orchestration: by doing it.

**The question: upgrade network first, or start flat?**

Option 1: **Upgrade networking infrastructure before deploying the cluster**
- Buy a proper router (Ubiquiti Dream Machine? MikroTik?)
- Add a managed switch for VLANs
- Design the network topology upfront
- Deploy Nomad into a properly segmented network

This makes networking a prerequisite for the homelab. It's the "do it right from the start" approach.

Option 2: **Start on flat network, upgrade later**
- Deploy Nomad on the existing router's flat network
- Everything on one subnet, minimal security
- Get the cluster running and workloads deployed
- Upgrade networking as a separate project once the cluster is stable

This makes networking a future learning project rather than a blocker.

**Where I'm leaning:**

Start flat, upgrade later. Here's why:

The current router isn't blocking me from running Nomad. Both the orchestrator and my initial workloads (DNS adblocker, experimental services) will work fine on a flat network. Millions of homelabs run on basic home routers.

If I make networking a prerequisite, I'm adding a big upfront learning curve before I can deploy anything. I'll be learning router configuration, VLAN tagging, subnet design, and firewall rules all at once, before I even have a cluster running. That's a recipe for analysis paralysis.

Better approach: get Nomad running on the flat network. Deploy some workloads. Understand what the cluster actually needs from a network perspective. *Then* upgrade the network infrastructure as a focused learning project, informed by actual usage patterns.

I can add network segmentation later. VLANs can be introduced without rebuilding everything. Overlay networks like Tailscale can layer on top of the existing flat network if I need multi-site connectivity.

**The learning path:**

Phase 1 (now): Deploy on flat network, understand orchestration and workload patterns
Phase 2 (later): Upgrade router and switch, learn VLAN configuration and segmentation
Phase 3 (future): Experiment with overlay networks, advanced routing, maybe multi-site

This way networking becomes a deliberate learning project rather than a prerequisite that blocks everything else.

**Security considerations:**

Yes, a flat network means the homelab isn't physically segmented from the household. That's not ideal, but I can mitigate it with host-based firewalls.

Each node can run firewalld (or similar) to control what traffic it accepts. I can:
- Lock down Nomad control plane ports to only accept connections from cluster nodes
- Restrict SSH access to specific IPs or networks
- Default-deny for management interfaces
- Leave workload ports more permissive initially (managing firewall rules per-workload would be painful with dynamic scheduling)

This gives me security boundaries without requiring VLAN-capable hardware. It's not as clean as network segmentation (managing firewall rules on each host vs. controlling it at the switch), but it's effective for protecting the cluster infrastructure itself.

The DNS adblocker will be accessible to the whole household network, which is what I want. Other services can be restricted if needed, but I'm not going to try to firewall every dynamic port that Nomad might allocate. That's fighting the orchestrator.

Host-based firewalls also have a learning benefit: I'll understand what traffic the cluster actually needs, which will inform my network design when I do upgrade the infrastructure.

**Where I'm landing:**

Start on the current flat network with host-based firewalls for control plane and management security. Get Nomad running and deploy workloads. Treat the network upgrade as a separate project once the cluster is stable and I understand what it actually needs. This unblocks progress now, provides reasonable security for infrastructure, and makes networking a focused learning opportunity later.

### Maintenance and Automation Philosophy

I want this homelab to be fun, not a second job. The constraint I keep coming back to is: less than an hour a week on maintenance.

**The tension:**

I enjoy tinkering. Writing glue code, configuring systems, experimenting with new tools—that's part of the appeal. But there's a difference between "fun tinkering when I feel like it" and "forced maintenance because things broke."

If I stop messing with the homelab for a few weeks (busy at work, life happens, just not interested), it should still work. Services should stay up. The cluster shouldn't require constant babysitting.

At the same time, I don't want to spend months building elaborate automation before I've deployed a single workload. That's its own form of complexity debt.

**What needs automation:**

Some things are clearly worth automating from the start:
- Infrastructure as code (Nomad job specs, config management)
- Deployment workflows (so I'm not SSHing to boxes to manually start services)
- Basic monitoring (so I know when things break, even if I'm not actively watching)

These reduce toil and make the system more reproducible. They're "good automation."

**What doesn't need automation yet:**

Other things can stay manual initially:
- OS updates on nodes (I can SSH and apt upgrade quarterly, it's fine)
- Adding new nodes to the cluster (how often will I actually do this?)
- Backup and restore procedures (what am I even backing up at this stage?)
- Certificate rotation (if I'm using self-signed certs, manual rotation once a year is acceptable)

These might become painful eventually. When they do, automate them. But not before.

**The "automate pain" principle:**

The right time to automate something is when doing it manually becomes painful. Not when it *might* be painful, or when best practices say to automate it, but when I actually feel the pain.

Examples:
- Deploying a service once manually? Fine.
- Deploying the same service for the third time? Time to write a job spec.
- Updating one node's firewall rules? Fine.
- Updating the same rules on four nodes? Time for config management.

This way automation is driven by actual need, not premature optimization.

**Graceful degradation over high availability:**

I'd rather have simple systems that occasionally break than complex systems that demand constant attention. If the DNS adblocker goes down and the house falls back to Cloudflare DNS for a few days, that's acceptable. I'll fix it when I have time.

This means:
- Accept some downtime rather than building elaborate HA setups
- Focus on making services easy to restart/rebuild rather than never failing
- Use fallback mechanisms (like secondary DNS) rather than clustering everything

**Where I'm landing:**

Start with basic infrastructure as code (Nomad job specs) and simple deployment workflows. Keep everything else manual until it becomes painful. Monitor enough to know when things break, but don't build elaborate automation upfront.

The goal is a system that's stable enough to ignore for a few weeks, but flexible enough to tinker with when I want to. Automation serves that goal, not the other way around.

---

## Proposed Direction

I'm starting with Nomad because it's simpler than Kubernetes, has a lower resource footprint, and is different enough from work to stay interesting. The initial cluster will be a single x86 server (avoiding eMMC wear from raft logs) with RK1 modules as client nodes. Ubuntu everywhere because the nodes are just substrate for Nomad—the interesting work happens at the cluster level, not the OS.

Networking starts flat with host-based firewalls protecting the control plane. I'll upgrade to proper segmentation later as a dedicated learning project once I understand what the cluster actually needs. Automation focuses on infrastructure as code (Nomad job specs) and basic deployment workflows. Everything else stays manual until pain drives it.

First workload is a DNS adblocker to validate the cluster and provide immediate household utility. From there, expand topology when I add robust storage (3-server consensus), upgrade network infrastructure when ready to learn it, and automate pain points as they emerge.

This gets something running quickly while keeping complexity low and preserving flexibility to evolve based on actual usage and learning goals.

---

## Outcome

<!-- # (Once resolved, document the final decision and reasoning. Future readers should understand why this was the right choice *at the time*.) -->

---

## References

<!-- # (List related RFDs, external documents, specs, or links that informed this discussion.) -->
