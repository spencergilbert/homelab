# RFD 0002: System Abstraction Model

<!-- RFD-META
Status: Draft
Date: 2025-10-05
Author: spencergilbert
-->

## Overview

This RFD defines the **System Abstraction Model** for the Homelab project.
It establishes foundational principles for how hardware, networking, and orchestration layers interact—ensuring that the system can evolve fluidly across heterogeneous substrates (ARM, x86, RISC-V, cloud) while remaining a single cohesive platform.

The model intentionally remains **implementation-agnostic**, focusing on desired capabilities and boundaries between layers.
Specific tooling, orchestration platforms, and network technologies will be decided in future RFDs.

---

## Guiding Principles

* Treat hardware as a **fungible substrate**. The cluster defines the platform, not the underlying node type.
* Design for **fluidity and evolution**: nodes may join or leave without manual reconfiguration.
* Keep **Day-0 complexity low**, deferring advanced automation until justified by scale or reliability.
* Maintain **security and isolation** appropriate for a mixed-use home environment.
* Ensure **portability** across architectures and **clear abstraction boundaries** between layers.

---

## Secrets and Bootstrap

### Current Approach (Day-0 / Day-1)

* **Human credentials** are managed in 1Password.
* **Workload secrets** use the orchestration layer’s native mechanisms (e.g., Kubernetes Secrets, Nomad Variables).
* **Bootstrap secrets** (admin tokens, CA keys, join credentials) are **never stored in Git**.

  * Provided interactively, through environment variables, or via 1Password CLI.
  * Rotated manually or through orchestration lifecycle tools.
* Nodes follow the **least-privilege principle**, regardless of permanence.
* **Dynamic secrets** or machine-level credential issuance may be explored in later phases.

### Future Direction

Automated bootstrap (Tier 2+)—nodes register themselves using short-lived credentials issued by the control plane or a bootstrap endpoint.
This enables zero-touch provisioning once the orchestration platform and secure network overlay are established.

---

## Networking Principles

* **Control Plane Isolation:**
  The cluster control plane is not publicly exposed. It is accessible only from trusted local networks or through a secure private tunnel.

* **Network Segmentation:**
  The desired architecture places homelab nodes on a dedicated network segment, logically isolated from the general household network.
  At present, existing network equipment does not support VLAN tagging or multiple routed subnets; therefore, the lab initially operates on a flat local network with logical separation only.

* **Flat Local Connectivity:**
  Nodes communicate directly within the lab’s local network during early phases. This topology favors simplicity while supporting orchestration bootstrapping and service communication.

* **DNS and Addressing:**
  Lab nodes and services initially resolve under a local domain (e.g., `lab.local`).
  Centralized DNS or service discovery may later unify namespaces (e.g., `lab.internal`).

* **Service Exposure:**
  All workloads and system services are private by default.
  Any publicly accessible service must explicitly declare ingress and security requirements and terminate TLS locally.

* **Future Direction:**
  As the homelab evolves to include remote or cloud nodes, a private encrypted overlay or mesh network (WireGuard, Tailscale, or equivalent) may replace the flat topology, providing secure multi-site connectivity and consistent addressing.

---

## Multi-Architecture Substrate Management

**Overview:**
The homelab accommodates heterogeneous compute substrates, including current ARM SBCs and potential future x86, RISC-V, or cloud nodes.
The system aims to preserve a single-cluster operational model where workloads are scheduled to compatible nodes automatically.

**Goals:**

* Support mixed architectures without fragmenting the platform.
* Prefer portability and reproducibility across architectures.
* Allow pragmatic exceptions for vendor-specific binaries or experimental workloads.

**Policy:**

1. **Multi-arch preferred:** Workloads and base images should be published as multi-architecture artifacts when practical. CI pipelines will build and publish multi-arch images for in-house services using cross-build tools (e.g., Docker `buildx` + QEMU).
2. **Architecture-aware scheduling:** Nodes are labeled by architecture (e.g., `arch=arm64`, `arch=amd64`). The orchestrator’s scheduler places workloads only on compatible nodes when single-architecture images are used.
3. **Vendor-specific workloads:** If a workload is available only for a specific architecture, it may run on a designated pool of matching nodes. These exceptions should be documented per-service.
4. **Emulation:** Emulation (e.g., qemu-user) is acceptable for development, testing, or convenience, but not recommended for performance-sensitive or stateful workloads.
5. **Stateful services:** Prefer to run stateful workloads natively on nodes that match their architecture. Networked storage or orchestration abstractions may relax this if tested reliable.
6. **Registry & CI:** The platform uses a registry that supports manifest lists. CI can cross-build or run native runners as needed; implementation specifics are deferred to a later RFD.

**Future Direction:**
As the cluster expands, build pipelines may produce per-architecture artifacts automatically and validate them through architecture-specific test matrices.
The scheduler’s constraint rules may also evolve to support architecture-specific affinities, resource weighting, or tiered node pools.

---

## Cluster Composition and Orchestration Abstraction

**Overview:**
The homelab operates as a single logical cluster spanning all substrates.
Orchestration provides workload scheduling, service lifecycle management, and limited self-healing.
The design remains orchestration-agnostic but assumes a control plane and scheduler capable of managing heterogeneous substrates.

**Principles:**

* **Single cluster by default:** One unified platform, with isolated clusters used only for experiments or testing.
* **Control plane locality:** Control-plane services typically run on persistent local hardware for cost and reliability.
* **Reasonable self-healing:** Workloads and nodes should recover automatically from transient faults; full cluster recovery may require manual action.
* **Automated orchestration:** Scheduling and scaling decisions are automatic, with operator input limited to hints and constraints.
* **Layered composition:**

  * **Control Plane:** Persistent coordination and scheduling components.
  * **Workload Plane:** User and platform workloads managed by the control plane.
  * **Substrate Layer:** Physical or virtual nodes supplying compute, storage, and network capacity.
* **Hybrid service model:**

  * **Out-of-band:** Services required for cluster bootstrap or recovery (e.g., local DNS, 1Password/identity, network configuration).
  * **In-cluster:** Platform and application services that can depend on the orchestrator (e.g., monitoring, ingress, CI/CD, internal DNS).
  * This balance may shift toward in-cluster management as the platform stabilizes.
* **Upgrade philosophy:** Begin with manual upgrades; progress toward automated and rolling upgrades once validated.

**Future Direction:**
Future RFDs may define additional orchestration automation, upgrade workflows, or limited multi-cluster experimentation as the system matures.

---

## Storage and Data Persistence

**Overview:**
The homelab balances operational simplicity with appropriate data durability.
Most workloads are **stateless** and **rebuildable**, with persistence introduced only where required by the service itself.
The storage model supports heterogeneous nodes and evolving substrates, assuming a mix of local and shared capacity that can change over time.

**Principles:**

* **Stateless by default:** Workloads should not rely on local persistence unless explicitly required.
* **Persist only when necessary:** Data is retained only when critical to service continuity or recovery.
* **Self-managed state preferred:** Use software that replicates or distributes state internally (e.g., clustered databases).
* **Composable tiers:** The storage layer may include ephemeral, local, shared, and remote/object tiers.
* **Durability over convenience:** Critical data (e.g., control-plane state, identity material) should be persisted to shared or replicated storage.
* **Fluid substrate independence:** Storage must not assume homogeneous hardware or constant node presence.

**Storage Tiers:**

1. **Ephemeral local storage** — Default tier for stateless workloads; data is non-durable and tied to container or node lifetime.
2. **Persistent local storage** — Node-bound volumes for small databases or dev services. Simple but node-specific.
3. **Shared network storage** — Centralized NAS/NFS or similar mount for shared configurations, backups, and durable data.
4. **Object storage** — Optional tier for artifacts and long-term backups, hosted locally (MinIO) or via cloud (S3, Backblaze).

**Day-0 / Day-1 Operating Model:**

* Start with ephemeral and node-bound persistence.
* Add shared network storage as stable workloads emerge.
* No automated backups initially; rebuildability is prioritized over restoration.
* Control-plane state is manually exported or backed up on change.

**Future Direction:**

* Introduce dynamic storage or in-cluster storage (Longhorn, Rook/Ceph, OpenEBS) for portable volumes.
* Evaluate object storage for backup and replication.
* Consider cloud-based storage providers when multi-site substrates exist.
* Define retention and recovery policies as durable workloads appear.

---

## Open Topics (Deferred to Future RFDs)

* **Storage Implementation Details** — driver selection, volume management, backup process.
* **Observability and Health Model** — metrics, logs, tracing, alerting across substrates.
* **Orchestration Platform Decision** — selecting and configuring the control plane technology.
* **Bootstrap Automation** — expanding the Tier 2+ concept once orchestration and overlay networking are stable.
