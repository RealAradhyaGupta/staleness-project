# DRAFT: not filed anywhere

Draft of an issue for `Qiskit/qiskit-aer`. **Do not post this until the
calibration data question is settled.** The reproduction currently needs a
real IBM calibration card, and we have not yet checked what IBM's terms allow
us to publish. Everywhere a card would be needed is marked `[HOLE]`.

---

**Title:** `QuantumError: Kraus is empty` from `NoiseModel.from_backend` on a
156 qubit target, depending on noise for qubits the circuit never touches

### Informations

- **qiskit-aer version**: 0.17.2
- **qiskit version**: 2.5.2
- **Python version**: 3.12.4
- **Operating system**: macOS 15 (Darwin 25.6.0), Apple silicon

### What is the current behavior?

Running a compiled 10 qubit Bernstein-Vazirani circuit on a 156 qubit device
noise model fails with

```
QiskitError: 'ERROR:  [Experiment 0] QuantumError: Kraus is empty. ,
              ERROR: QuantumError: Kraus is empty.'
```

The noise model is built by `NoiseModel.from_backend(backend)`, where
`backend` is a small `BackendV2` whose `target` carries per qubit T1 and T2
and per instruction durations and errors. It holds 790 local quantum errors
and 152 readout errors.

The failure is deterministic: six consecutive fresh processes with the same
seed all fail. It happens on the first simulation in a clean process, so it is
not a leftover from an earlier run, although once it has fired it does tend to
recur for later simulations in the same process.

Two properties suggest this is not simply bad input:

**1. It depends on noise attached to qubits the circuit never uses.** The
compiled circuit touches 15 physical qubits. If I rebuild the noise model with
only those 15 qubits' entries and run the identical circuit, it succeeds. Put
the other qubits' entries back and it fails again. A circuit's result should
not depend on noise on qubits outside its support.

**2. It turns on at a threshold in the number of measurements.** Keeping only
the first k of the circuit's 9 `measure` instructions, with everything else
identical:

| measurements kept | result |
|---|---|
| 0 to 6 | runs normally |
| 7, 8, 9 | `Kraus is empty` |

It is also independent of the simulation method: `statevector` and
`matrix_product_state` both fail, and `density_matrix` only avoids it by
running out of memory first. That points at the noise application path rather
than at one state representation.

I checked the Python side noise model for an empty error and there is none.
Every one of the 790 local quantum errors has at least one term. The only
non-Pauli entries are on 15 qubits where T2 > T1, which makes
`thermal_relaxation_error` return a single term holding a 3 operator Kraus
channel instead of a Pauli mixture. None of those qubits is touched by the
circuit, and loading any one of them on its own does not reproduce the fault,
so the trigger appears to be cumulative.

### Steps to reproduce the problem

`[HOLE]`: a runnable reproduction is not attached yet.

I have a script that reproduces it reliably, but it reads a real calibration
card from disk, and I have not yet confirmed that the card can be
redistributed. I also tried to rebuild the fault from invented numbers on a
156 qubit target of the same shape, including 95 single term Kraus entries,
which is more than the real model has, and it runs clean. So I cannot yet
offer a self contained reproduction.

If a maintainer would find it useful, I can attach:

- the serialised `NoiseModel` and the compiled `QuantumCircuit`, once the
  redistribution question is settled, or
- the full characterisation above against a card you supply.

### What is the expected behavior?

Either the simulation runs, or Aer raises an error that names the instruction
and qubit whose Kraus set came out empty. At the moment the message gives no
way to locate the entry, which is why the work above took as long as it did.

### Suggested solutions

I have not read the C++ source, so this is a pointer and not a diagnosis. The
two useful facts are that unused qubits' noise entries change the outcome and
that the threshold sits at seven measured qubits. A first step that would help
users regardless of the cause is to include the instruction name and the qubit
indices in the "Kraus is empty" message.
