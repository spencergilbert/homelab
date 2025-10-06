# Runbooks

This directory contains operational procedures for the homelab - both planned tasks and incident response.

## What Goes Here

**"How to do X" documentation**, including:

- Initial setup procedures (hardware, services, configuration)
- Routine maintenance tasks (updates, scaling, configuration changes)
- Incident response (failures, recovery, troubleshooting)
- Operational workflows (deployments, migrations, upgrades)

If it's a step-by-step procedure you'll need to reference while operating the homelab, it belongs here.

## What Doesn't Go Here

- **Why decisions were made** → See [RFDs](../docs/rfds/)
- **System architecture and topology** → See [architecture.md](../docs/architecture.md)
- **General reference material** → See [docs/](../docs/)

## Philosophy

Following the "automate pain" principle from [RFD 0002](../docs/rfds/0002-initial-platform-hardware-orchestration-and-network-strategy.md):

- Start with flat structure - don't create subdirectories until navigation becomes painful
- Document procedures as you do them, not before
- Keep it practical - these are working docs, not polished manuals
- Update when things change - runbooks should reflect reality

## Organization

Currently flat. When the number of runbooks makes this annoying, we'll add subdirectories (probably by domain: `hardware/`, `nomad/`, `network/`).
