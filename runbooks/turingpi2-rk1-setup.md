# TuringPi 2 + RK1 Setup

**Last Updated**: 2025-10-05
**Hardware**: TuringPi 2 v2.5, RK1 Compute Module (8GB RAM, 32GB eMMC)
**Target OS**: Ubuntu 22.04 LTS Server

---

## Purpose

Initial setup of a TuringPi 2 board with RK1 compute module(s). This procedure covers both the one-time TuringPi board setup and the repeatable RK1 module installation process.

**Context**: See [RFD 0002](../docs/rfds/0002-initial-platform-hardware-orchestration-and-network-strategy.md) for the broader homelab strategy. RK1 modules will eventually run as Nomad client nodes, but we're avoiding Nomad servers on eMMC due to raft log write-wear concerns.

---

## Prerequisites

### Hardware
- [ ] TuringPi 2 board
- [ ] 1-4x RK1 compute modules
- [ ] Power supply
- [ ] Ethernet cable
- [ ] Network with DHCP
- [ ] (Optional) MicroSD card for BMC - only needed for firmware recovery/upgrades from v1.x

### Software
- [ ] Ubuntu 22.04 LTS Server image for RK1
  - Download: https://firmware.turingpi.com/turing-rk1/
  - **Use**: v1.33 or latest official 22.04 release
  - **Avoid**: Ubuntu 24.04/24.10 (USB and NVMe issues)

### Network Access
- [ ] Workstation on same network
- [ ] mDNS support (or access to router DHCP table)

---

## Part 1: TuringPi 2 Board Setup (One-Time)

This section only needs to be done once per TuringPi board.

### 1.1 Physical Setup

**Power and Network**:
1. Connect Ethernet cable to either 1Gbps RJ45 port (ports are bridged)
2. Connect TuringPi power supply to board
3. Power on the board
4. Wait ~30 seconds for BMC to boot

**Expected State**:
- BMC boots automatically
- RK1 modules do NOT auto-power-on (controlled via BMC)
- All node LEDs should be RED (off = not powered)

### 1.2 Access BMC

The Baseboard Management Controller (BMC) handles power management, OS flashing, and monitoring.

**Find BMC on network**:

**Method A - mDNS** (preferred):
```bash
# Test if mDNS resolution works
ping turingpi.local
```

**Method B - Router DHCP table** (if mDNS blocked):
- Check router admin interface for hostname "turingpi"
- Note the IP address

**SSH to BMC**:
```bash
# Default credentials: root / turing
ssh root@turingpi.local
```

### 1.3 Initial BMC Configuration

**CRITICAL - Change default password**:
```bash
passwd
# Enter new password twice
```

**Check BMC firmware version**:
```bash
bmcd --version
# Should show: bmcd 2.x.x
# Requirement: v2.x for web UI flashing
```

**Verify node status**:
```bash
tpi power status
# Should show all nodes OFF
```

**Access BMC Web Interface**:
- URL: `https://turingpi.local` (or `https://<bmc-ip>`)
- Login: `root` / (new password)
- Accept self-signed certificate warning

---

## Part 2: RK1 Module Setup (Repeatable)

This section can be repeated for each RK1 module you install.

### 2.1 Install RK1 Module Physically

**Choose a slot**: Node 1-4 (any slot works, suggest sequential: 1, 2, 3, 4)

**Installation**:
1. Ensure board is powered (BMC running), but target node is OFF
2. Align RK1 module's sides and notch with slot
3. Press vertically until you hear a **click**
4. Verify white side arms have locked into place
5. Confirm module is seated flush

**Note**: Hot-swap is supported, but safer to keep target node powered off.

### 2.2 Flash Ubuntu via BMC Web Interface

**This takes 60-90 minutes - plan accordingly.**

**In BMC web interface**:

1. Navigate to **"Flash Node"** page

2. **Select Node**: Choose the node where you installed the module (e.g., Node 1)

3. **Upload Image**:
   - Click "Choose File"
   - Select the downloaded Ubuntu 22.04 `.img.xz` file
   - Verify filename shows Ubuntu 22.04 (not 24.04)

4. **Start Flash**: Click "Flash" button

5. **Wait patiently**:
   - Progress bar shows flashing status (~60-90 min)
   - Verification runs after flashing (~10 min)
   - Do NOT close browser or power off board
   - You can minimize and check back periodically

6. **Confirm Success**: Wait for "Success" message

**Troubleshooting**:
- Flash fails → Verify correct image (Ubuntu 22.04), try re-downloading
- BMC hangs → Check firmware is v2.x
- Progress stuck → Some nodes take longer, wait at least 2 hours before aborting

### 2.3 First Boot

**Power on the node**:
```bash
# From BMC SSH session
tpi power on --node 1    # Replace 1 with your node number

# Verify status
tpi power status
# Node should show ON, red LED turns OFF
```

**Find the node's IP address**:

**Method 1** - Check BMC web UI (may show connected nodes)

**Method 2** - Check router DHCP table for hostname "ubuntu"

**Method 3** - Network scan from your workstation:
```bash
nmap -sn 192.168.1.0/24 | grep -B 2 "rk3588\|ubuntu"
```

**Note**: Serial console access via `tpi uart` is available but configuration varies by BMC version. Check web UI for serial console access, or use SSH once node has network connectivity.

### 2.4 SSH Access

**Default credentials**: `ubuntu` / `ubuntu`

```bash
# From your workstation
ssh ubuntu@<node-ip>
```

**First login prompts for password change** - choose a secure password.

**Set a meaningful hostname**:
```bash
sudo hostnamectl set-hostname rk1-node1    # Adjust for node number
```

### 2.5 Post-Install Updates (CRITICAL)

The RK1 has known issues (USB, hardware support) that resolve after updates and reboots.

**First update cycle**:
```bash
sudo apt update
sudo apt -y upgrade
sudo reboot
```

**Wait ~2 minutes, SSH back in, then second update cycle**:
```bash
sudo apt update
sudo apt -y upgrade
sudo reboot
```

**Why twice?**
- First upgrade updates kernel/bootloader
- Second ensures all packages work with new kernel
- USB support typically works after 2 reboot cycles

**Verify hardware** (after second reboot):
```bash
# Check USB
lsusb    # Should show USB controllers

# Check storage
lsblk    # Should show mmcblk0 (eMMC)

# Check network
ip addr show eth0    # Should be UP with IP

# Check kernel
uname -r    # Should be 5.10.x (BSP kernel)
```

### 2.6 Optional: Static IP Configuration

For cluster nodes, static IPs are recommended.

**Edit netplan config**:
```bash
sudo nano /etc/netplan/50-cloud-init.yaml
```

**Example** (adjust for your network):
```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: no
      addresses:
        - 192.168.1.101/24    # Increment for each node
      gateway4: 192.168.1.1
      nameservers:
        addresses:
          - 192.168.1.1
          - 1.1.1.1
```

**Apply**:
```bash
sudo netplan apply
ip addr show eth0    # Verify new IP
```

---

## Known Issues and Workarounds

### USB Ports Not Working

**Symptom**: `lsusb` shows nothing or USB devices not detected.

**Solution**: Run `sudo apt update && sudo apt -y upgrade && sudo reboot` **twice**.

**Timeline**: Should work after 2 update/reboot cycles.

---

### NVMe Boot Issues (Mainline Kernel Only)

**Symptom**: NVMe drives not detected (only affects experimental mainline kernel images).

**Solution**: Use Ubuntu 22.04 with BSP kernel 5.10.x (recommended).

**Not applicable**: If using official Ubuntu 22.04 image.

---

### Display Defaults to 1080p

**Symptom**: HDMI always outputs 1080p regardless of monitor.

**Cause**: EDID detection broken on TuringPi 2 v2.4/v2.5.

**Impact**: None for headless server setup.

---

### eMMC/NVMe UUID Conflicts

**Symptom**: System randomly mounts wrong partitions (only if cloning eMMC to NVMe).

**Solution**: Generate new UUIDs after cloning:
```bash
sudo tune2fs -U random /dev/nvme0n1p1
```

**Not applicable**: Until you add NVMe storage for external boot.

---

## Validation Checklist

After completing this procedure:

**Per TuringPi Board**:
- [ ] BMC accessible via SSH
- [ ] BMC default password changed
- [ ] BMC web interface accessible

**Per RK1 Module**:
- [ ] Module physically installed and seated
- [ ] Ubuntu 22.04 flashed via BMC
- [ ] Node powers on successfully
- [ ] Node accessible via SSH
- [ ] Default password changed
- [ ] Two update/reboot cycles completed
- [ ] USB hardware working (`lsusb`)
- [ ] Network configured (DHCP or static)
- [ ] Hostname set appropriately

---

## Next Steps

**For additional RK1 modules**: Repeat Part 2 for each module.

**Once all nodes are running**:
1. Test basic workloads and document performance characteristics
2. Wait for x86 server to arrive (will run Nomad server)
3. Install Nomad client on RK1 nodes
4. Join nodes to Nomad cluster

See [RFD 0002](../docs/rfds/0002-initial-platform-hardware-orchestration-and-network-strategy.md) for the broader homelab architecture plan.

---

## References

- TuringPi Official Docs: https://docs.turingpi.com/docs/turing-pi2-intro
- RK1 Firmware Downloads: https://firmware.turingpi.com/turing-rk1/
- TuringPi Forum: https://forum.turingpi.com/
- Ubuntu Rockchip Project: https://github.com/Joshua-Riek/ubuntu-rockchip

---

## Troubleshooting Log

Use this section to document issues you encounter during setup.

### [Date] - Issue Description

**Problem**:

**Solution**:

**Notes**:
