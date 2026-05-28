# QEMU Release and Versioning Guide

## Version Numbering
QEMU follows a major.minor.micro version scheme:
- Major: Incremented for very large, breaking changes (rare)
- Minor: Incremented 3 times per year (~April, August, December)
- Micro: Patch releases for bug fixes

## Release Tags
Tags in the QEMU git repository follow the pattern `v{major}.{minor}.{micro}`.
Example: `v8.2.0`, `v8.2.1`, `v8.2.2`

## CPU Model Change Tracking
CPU model changes are typically found in:
- `target/i386/cpu.c` — x86 CPU model definitions and registration
- `target/i386/cpu.h` — x86 CPU data structures and constants
- `target/i386/kvm/kvm.c` — KVM-specific x86 code
- `target/i386/kvm/kvm-cpu.c` — KVM CPU capabilities reporting

## Key Files for Feature Changes
- `target/i386/` — x86 emulation core
- `accel/kvm/` — KVM accelerator
- `include/hw/i386/` — x86 hardware headers
- `linux-headers/asm-x86/kvm.h` — KVM kernel headers (x86)

## Related Components
When a CPU model changes, these subsystems may also be affected:
- Machine types (`hw/i386/pc*.c`)
- Firmware/UEFI boot
- ACPI tables
- NUMA configuration
- Live migration protocol

## Typical Release Cycle
1. Development (3 months): Features merged to master
2. RC period (1 month): Release candidates for testing
3. Release: Tag vX.Y.0
4. Stable: Patch releases vX.Y.1, vX.Y.2, etc.

The next stable release typically follows 4 months after the previous one.
