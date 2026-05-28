# Regression Test Patterns for QEMU-KVM CPU Features

## Test Categories

### 1. CPU Model Enumeration Tests
Verify that all expected CPU models are available in the new version.
- Run `-cpu help` and verify new models appear
- Check that removed models are no longer present
- Verify model aliases resolve correctly

### 2. Feature Flag Verification Tests
For each new or changed CPU feature:
- Boot a VM with the feature enabled, verify it's visible in `/proc/cpuinfo`
- Boot a VM with the feature disabled, verify it's absent
- Test feature toggling via `-cpu model,+feature` and `-cpu model,-feature`

### 3. Migration Compatibility Tests
- Live-migrate a VM from old version to new version with same CPU model
- Verify CPU features are identical after migration
- Test versioned CPU models across migration scenarios

### 4. Performance Regression Tests
- Run CPU-intensive benchmarks (e.g., SPEC CPU, sysbench) on both versions
- Compare performance metrics within acceptable thresholds
- Focus on features known to affect performance (e.g., cache modeling, TLB)

### 5. Default Behavior Tests
- Boot a VM without specifying a CPU model, verify the default
- Check that default CPU features are correct for each machine type
- Verify that KVM-specific defaults are correct when KVM is enabled

### 6. Boundary and Error Tests
- Try to use a removed CPU model, verify graceful error
- Try invalid feature combinations, verify error messages
- Test maximum CPU count with new models
- Test memory limits with new features enabled

### 7. Guest OS Compatibility
- Boot common Linux distributions (RHEL, Ubuntu, Fedora) with new CPU models
- Verify kernel detects CPU correctly
- Check for kernel warnings or errors in dmesg

## Sample Test Case Structure (Polarion Format)

```json
{
  "id": "QEMU-CPU-001",
  "title": "Verify new EPYC-Genoa CPU model enumeration",
  "description": "After upgrading to the new qemu-kvm version, verify that EPYC-Genoa CPU model is available and enumerable.",
  "severity": "critical",
  "priority": 1,
  "preconditions": "1. New qemu-kvm version installed\n2. x86_64 host with KVM enabled\n3. At least 2 CPU cores available",
  "test_steps": [
    {
      "step": "Run 'qemu-system-x86_64 -cpu help'",
      "expected": "EPYC-Genoa appears in the output list of available CPU models"
    },
    {
      "step": "Boot a VM with -cpu EPYC-Genoa",
      "expected": "VM boots successfully without errors"
    },
    {
      "step": "Check /proc/cpuinfo inside the guest",
      "expected": "CPU flags match the expected EPYC-Genoa feature set"
    }
  ],
  "test_type": "regression",
  "component": "cpu_model"
}
```
