# Focused Homelab Implementation Plan

## Core Principle: Start Simple, Iterate Based on Pain

**Philosophy**: Build the minimum viable homelab that provides real value, then expand based on actual needs rather than hypothetical requirements.

---

## Core Decisions

### Container Runtime: Podman
**Decision**: Use Podman task driver instead of Docker

**Rationale:**
- Daemonless architecture (simpler, more secure)
- Rootless containers by default
- Native Ubuntu 24.04 support
- Better aligns with modern container practices
- Drop-in compatible with Docker commands/images

**Tradeoff**: Slightly fewer online examples, but syntax is nearly identical (just change `driver = "docker"` to `driver = "podman"`)

**Fallback**: Both drivers can coexist if needed for specific use cases

---

## Phase 1: Foundation (Month 1)
**Goal**: Working cluster with visibility

### Week 1-2: Basic Cluster
**Hardware allocation:**
- **3x RK1 nodes**: Nomad/Consul servers + client (lab-polaris, lab-vega, lab-rigel)
- **1x RK1 node**: Nomad/Consul client (lab-antares)
- **4x Pi 3B+**: Set aside for now (not worth the complexity)

**Why this split:**
- 3 servers = proper HA and quorum
- Learn real production patterns
- Can practice rolling updates
- All nodes can run workloads (reasonable for a homelab)

**Setup tasks:**
1. Flash Ubuntu 24.04 to all RK1s
2. Static IPs: 192.168.1.20-23
3. Install Consul, Nomad, Podman via packages (not Ansible yet)
4. Configure the server + client nodes
```hcl
# /etc/nomad.d/nomad.hcl (example for lab-polaris)
server {
  enabled = true
  bootstrap_expect = 3
}
   
client {
  enabled = true
}

plugin "podman" {
  config {
    volumes {
      enabled = true
    }
  }
}
```
5. Form cluster manually to understand the process
5. Verify with `nomad server members` and `consul members`

**Success criteria:**
- Can SSH to all nodes
- Nomad UI accessible at http://192.168.1.20:4646
- Consul UI accessible at http://192.168.1.20:8500
- Cluster survives single node failure

### Week 3-4: Observability Foundation
**Why now**: Before you depend on services, you need to see when they break
**Why Vector**: Single, flexible observability agent that can collect metrics and logs, then route to any destination. Start with remote scraping, expand to local collection only when needed.

**Deploy Vector:**
1. Single instance job scraping all Nomad/Consul endpoints
2. Expose Prometheus exporter
3. Watch metrics to understand baseline cluster health

**What to observe:**
- Are all nodes checking in?
- Are server elections stable?
- What does "healthy" look like in metrics?

**Success criteria:**
- Vector collecting metrics from all 4 nodes
- Can curl Vector's Prometheus endpoint and see data
- Understand basic Nomad/Consul health metrics
- Comfortable reading `nomad alloc logs` output

---

## Phase 2: Useful Services (Month 2)
**Goal**: Deploy services you'll actually use, with confidence

### Week 5-6: DNS Ad-Blocking
**Now that you have observability:**

Deploy Blocky as system job on server nodes using the robust pattern (host networking, runs on all 3 servers).

**Prerequisites:**
Add node metadata to distinguish servers from clients in Nomad config.

**Use your observability:**
- Watch Vector metrics during deployment
- See task allocations succeed/fail in real-time
- Monitor resource usage
- Verify all 3 instances are healthy

**Deployment:**
1. Write Nomad job for Blocky (system job, constrained to servers)
2. Deploy using `nomad job run blocky.nomad`
3. Verify running on all 3 servers: `nomad job status blocky`
4. Test DNS: `dig @192.168.1.20 example.com`
5. Configure your workstation DNS:
   - Primary: 192.168.1.20
   - Secondary: 192.168.1.21
   - Tertiary: 192.168.1.22
6. Verify ad-blocking: `dig @192.168.1.20 ads.google.com` (should return blocked)

```hcl
job "blocky" {
  datacenters = ["dc1"]
  type = "system"  # Runs on every node
  
  # Only run on server nodes
  constraint {
    attribute = "${meta.node_class}"
    value     = "server"
  }
  
  group "blocky" {
    network {
      mode = "host"
    }
    
    task "blocky" {
      driver = "podman"
      
      config {
        image = "spx01/blocky:latest"
        network_mode = "host"
      }
      
      template {
        data = <<EOF
upstream:
  default:
    - 1.1.1.1
    - 1.0.0.1
blocking:
  blackLists:
    ads:
      - https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts
  clientGroupsBlock:
    default:
      - ads
port: 53
httpPort: 4000
EOF
        destination = "local/config.yml"
      }
      
      resources {
        memory = 128
        cpu    = 100
      }
    }
  }
}
```

**Success criteria:**
- Blocky running on all 3 server nodes
- Metrics show all instances healthy
- DNS queries work and are fast
- Ad-blocking works
- Survives single server failure (test this!)

### Week 7-8: Configuration Management
**Now codify your work:**

Set up Ansible to reproduce:
- Node configuration
- Vector deployment
- Blocky deployment

Test by rebuilding one node from scratch.

**Use your observability:**
- Watch metrics as node rejoins cluster
- Verify services redeploy correctly
- Confirm cluster stabilizes

**Success criteria:**
- Can rebuild any node via Ansible
- Observability confirms successful rebuild
- Documentation of the process

**Inventory (keep it simple):**
```yaml
all:
  vars:
    ansible_user: ubuntu
    datacenter: dc1
    region: global
    
  children:
    servers:
      hosts:
        lab-polaris:
          ansible_host: 192.168.1.20
        lab-vega:
          ansible_host: 192.168.1.21
        lab-rigel:
          ansible_host: 192.168.1.22
      vars:
        nomad_server: true
        nomad_client: true
        consul_server: true
        bootstrap_expect: 3
        
    clients:
      hosts:
        lab-antares:
          ansible_host: 192.168.1.23
      vars:
        nomad_server: false
        nomad_client: true
        consul_server: false
```

---

## Phase 3: Expansion (Month 3)
**Goal**: Deploy 2-3 services you'll actually use

### Week 9-10: Container Registry (Zot)
- Avoid Docker Hub rate limits
- Cache images locally
- **Monitor**: Registry metrics via Vector

### Week 11-12: Pick ONE Service
Based on your interests:
- Local LLM (Ollama)
- Media Server (Jellyfin)
- Home Automation (Home Assistant)

Don't deploy all three - pick what you'll actually use.
**Monitor**: Service-specific metrics via Vector

---

## Decision Framework

### Storage Strategy
**Start with:** Local storage on each node
**Upgrade when:** You have data you care about
**Then consider:** External NAS, not distributed storage

### Secrets Management  
**Start with:** Environment variables in Nomad jobs
**Upgrade when:** You have more than 5 secrets
**Then consider:** Vault in dev mode to learn

### Monitoring
**Start with:** Nomad/Consul UIs + Vector
**Upgrade when:** You need historical data
**Then consider:** Datadog or Grafana

### Networking
**Start with:** Flat network, simple DNS
**Upgrade when:** Never (probably)
**Why:** VLANs add complexity with minimal benefit at this scale

### Backups
**Start with:** You don't need backups for a learning environment
**Upgrade when:** You have data you can't recreate
**Then consider:** Rsync to external drive

---

## What We're NOT Doing (And Why)

### Not Using the Pis in the Cluster
**Why not:** 1GB RAM is too constrained. Better uses:
- Dedicated Pi-hole (redundant DNS)
- Network monitoring probe
- Cold spare
- Separate learning cluster

### Not Building Complex DNS
**Why not:** Consul DNS for internal, Cloudflare for external. Done.

### Not Implementing GitOps
**Why not:** Ansible push is fine. GitOps is resume-driven development for a homelab.

---

## Success Metrics

The goal isn't to complete tasks - it's to **build something useful while learning**.

### After Month 1
You should be able to say **yes** to:
- "My cluster is stable and I understand how it works"
- "I can see what's happening via observability"
- "I've deployed one service and know it's healthy"

If no: Don't move forward. Debug, simplify, or restart.

### After Month 2
You should be able to say **yes** to:
- "I can rebuild a node without panic"
- "I'm using at least one service regularly"
- "I know where to look when something breaks"

If no: You've added complexity faster than understanding. Simplify.

### After Month 3
You should be able to say **yes** to:
- "I use this cluster weekly"
- "I'm comfortable with Nomad job files"
- "I learned something valuable"

If no: Honestly evaluate whether to continue or shut it down.

---

## The 3-Month Checkpoint

After 3 months, honestly answer:

**1. Are you using the cluster regularly?**
- Yes → Continue to Phase 4
- No → Why not? Either fix the root cause or simplify/shutdown

**2. What services do you actually use?**
- Keep those, remove the rest
- Focus beats breadth

**3. What was painfully complex?**
- Simplify it or document why it's necessary
- Complexity should earn its keep

**4. What are you curious to learn next?**
- Pick ONE thing
- Go deep, not broad

**5. Is this still fun?**
- Yes → Great, keep going
- No → Either change approach or gracefully shut down

---

## Red Flags to Watch For

Stop and reassess if you notice:
- Spending more time fixing the homelab than using it
- Avoiding the homelab because it's "broken again"
- Adding features you "might need someday"
- Copying configurations without understanding them
- The cluster has been "almost working" for weeks

These are signs to simplify, not push forward.

---

## Remember

**Your homelab should be:**
- Simple enough to maintain in 2 hours/week
- Complex enough to learn from
- Useful enough to justify its existence
- Reliable enough to depend on

**Your homelab should NOT be:**
- A second job
- A source of stress
- More complex than your work environment
- Trying to solve problems you don't have

---

## Key Learnings Focus

Instead of trying to learn everything, master these:

1. **Nomad job lifecycle**: deploy, update, rollback
2. **Consul service discovery**: How services find each other
3. **Operational debugging**: Where to look when things break
4. **Resource management**: Understanding CPU/memory allocation

These skills transfer to any orchestration platform.

---

## When to Add Complexity

Add complexity when you feel pain, not before:

- **Pain:** "I keep forgetting what changes I made"  
  **Solution:** Add Ansible

- **Pain:** "I don't know why the service is slow"  
  **Solution:** Add monitoring

- **Pain:** "Docker Hub rate limited me"  
  **Solution:** Add registry

- **Pain:** "I lost important data"  
  **Solution:** Add backups

- **No Pain:** "I might need VLANs someday"  
  **Don't:** You probably won't

---

## Phase 4 and Beyond (Optional)

Only after the 3-month checkpoint:

- **If you want more compute:** Consider cloud bursting, not desktop integration
- **If you need external access:** Tailscale is 10 minutes of work
- **If you want Kubernetes experience:** Create a separate k3s cluster on the Pis
- **If you need real HA:** Focus on service-level HA, not infrastructure
