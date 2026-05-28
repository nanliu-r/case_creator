# x86 CPU Models in QEMU-KVM

## Overview
QEMU-KVM supports a wide range of x86 CPU models, from ancient 486 to modern
server-class processors. Each CPU model defines a set of features, capabilities,
and compatibility levels.

## CPU Model Types

### Host Passthrough
- `host`: Passes through the host CPU features directly to the guest.
- Requires KVM. All host CPU features are exposed to the guest.
- Best for performance but not migratable between different hosts.

### Named Models
QEMU defines named CPU models that represent specific processor families:

- `qemu64` / `qemu32`: QEMU's baseline 64-bit / 32-bit models.
- `kvm64` / `kvm32`: KVM baseline models with KVM-specific enhancements.
- `EPYC`: AMD EPYC server processors.
- `EPYC-Rome`: AMD EPYC Rome (Zen 2) processors.
- `EPYC-Milan`: AMD EPYC Milan (Zen 3) processors.
- `EPYC-Genoa`: AMD EPYC Genoa (Zen 4) processors.
- `Cascadelake-Server`: Intel Cascade Lake Xeon.
- `Cooperlake`: Intel Cooper Lake Xeon.
- `Icelake-Server`: Intel Ice Lake Xeon.
- `SapphireRapids`: Intel Sapphire Rapids Xeon.
- `GraniteRapids`: Intel Granite Rapids Xeon.

### Versioned Models
CPU models can have versioned variants (e.g., `EPYC-v2`, `Cascadelake-Server-v4`)
that represent different compatibility levels for live migration.

## CPU Features and Flags

### Common Feature Categories
1. **Base features**: FPU, VME, DE, PSE, TSC, MSR, PAE, MCE, etc.
2. **SIMD**: MMX, SSE, SSE2, SSE3, SSSE3, SSE4.1, SSE4.2, AVX, AVX2, AVX512F
3. **Virtualization**: VMX, SVM, EPT, NPT, VPID
4. **Security**: SMEP, SMAP, IBPB, STIBP, SSBD, MD_CLEAR
5. **Power management**: ACPI, APIC, X2APIC

### KVM-Specific Features
- `kvm-asyncpf`: Asynchronous page faults
- `kvm-pv-eoi`: Paravirtualized end-of-interrupt
- `kvm-pv-unhalt`: Paravirtualized spinlocks
- `kvm-steal-time`: Paravirtualized steal time accounting
- `kvmclock`: KVM clock source
- `kvm-asyncpf-int`: Async PF interrupts
- `kvm-msi-ext-dest-id`: Extended MSI destination ID

## Typical Changes Between Versions
When a new qemu-kvm version is released, CPU model changes typically include:

1. **New CPU models**: Support for newly released hardware (e.g., new Intel/AMD generations)
2. **Version bumps**: Existing models get new versions for migration compatibility
3. **Feature additions**: New CPU flags added to existing models
4. **Default changes**: Default CPU model for a machine type changes
5. **Deprecations**: Old models or features marked as deprecated
6. **Bug fixes**: Incorrect feature bits corrected
