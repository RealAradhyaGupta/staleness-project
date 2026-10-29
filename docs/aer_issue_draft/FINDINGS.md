# What I measured about the "Kraus is empty" fault

Everything below was run on 14 October 2026 against the project's own data.
All of it is read only: nothing in `engine/`, `data/raw`, `PROTOCOL.md` or
`PROTOCOL_AMENDMENTS.md` was changed, and the 22 frozen checksums from L-033
were re-verified afterwards.

## Environment

```
macOS 25.6.0, Apple silicon
Python 3.12.4          (team_code/.venv)
qiskit 2.5.2
qiskit-aer 0.17.2
numpy 2.5.4
```

## The failing case

One job from the test run:

```
machine      ibm_marrakesh
truth state  237            (also fails on 233)
circuit      bv10
arm          random, draw 1 of 5
layout       [109, 118, 123, 124, 125, 126, 127, 128, 129, 136]
```

The noise model is `NoiseModel.from_backend(backend)` where `backend` is a
thin `BackendV2` wrapper around a 156 qubit `Target`. It holds 790 local
quantum errors and 152 readout errors.

## Facts, in the order I found them

**1. It is deterministic.** Six consecutive fresh processes, same inputs, same
seed: six failures. It is not intermittent.

**2. It fails as the FIRST simulation in a fresh process.** This corrects part
of L-037, which recorded the fault as only appearing after some other
simulation had run in the same process. That is true of the 333 jobs the
finisher recovered, but it is NOT true of these two jobs: they fail even when
nothing has run before them. That is why they could not be recovered and were
skipped.

**3. It is sticky.** Once the error has fired once in a process, later
simulations in the same process can fail too, including ones that run fine in
a clean process. This is what made my first bisection give a wrong answer.

**4. It does not depend on the simulation method.**

| method | result |
|---|---|
| auto (picks statevector) | Kraus is empty |
| statevector | Kraus is empty |
| matrix_product_state | Kraus is empty |
| density_matrix | insufficient memory, so no information |

So it is in the noise application path, not in one state representation.

**5. There is no empty Kraus on the Python side.** Every one of the 790 local
quantum errors has at least one term. The histogram of terms per entry:

```
cz    3 terms: 4     reset 1 term : 14      sx 1 term : 2
cz    9 terms: 10    reset 3 terms: 138     sx 3 terms: 26
cz   16 terms: 2                            sx 4 terms: 12
cz   45 terms: 2                            sx 12 terms: 112
cz   48 terms: 50                           x  likewise
cz  135 terms: 2
cz  144 terms: 264
```

The emptiness is therefore produced inside Aer, not handed to it.

**6. It depends on noise entries for qubits the circuit never touches.** The
compiled circuit touches 15 physical qubits:

```
105 106 107 108 109 117 118 123 124 125 126 127 128 129 136
```

Rebuilding the noise model with ONLY those 15 qubits' entries, and running the
identical circuit, **succeeds**. Adding back entries for unused qubits brings
the failure back. This is the strongest single pointer at Aer: a circuit's
result should not depend on noise attached to qubits it never uses.

**7. A sharp threshold in the number of measured qubits.** Taking the same
compiled circuit and keeping only the first k of its 9 `measure`
instructions, everything else identical:

| measurements kept | result |
|---|---|
| 0 to 6 | runs |
| 7, 8, 9 | Kraus is empty |

**8. The only non-Pauli entries belong to 15 qubits with T2 > T1.** When
T2 > T1, `thermal_relaxation_error` cannot return a Pauli mixture and returns a
single term holding a 3 operator Kraus channel instead. In this model that
happens on qubits

```
26 35 39 48 51 54 59 81 83 90 91 94 95 121 152
```

none of which the circuit touches. **No single one of them reproduces the fault
on its own**: loading only the Kraus entry for qubit 26, or 35, or the sx entry
for 26, or the readout error for 26, all run fine. So the trigger is
cumulative, not one bad entry.

**9. I could not rebuild it from invented numbers.** See
`repro_synthetic_no_ibm_data.py`. I checked the attempt was not a no-op, the
same way Amendment A3 checked its null: the synthetic model really does
contain 95 single term Kraus entries, which is more than the 18 in the real
model, and it still runs clean. So "has Kraus channels" is not by itself the
trigger. This is a real negative result and it narrows the search, but it
means I cannot yet hand a maintainer a script they can run.

## Two corrections to my own earlier work

- **L-037 said the fault only appears after another simulation in the same
  process.** Incomplete. These two jobs fail first in a clean process. See
  fact 2.
- **My first bisection of the circuit said a single `sx` on qubit 105 was
  enough.** Wrong, twice over. The prefixes with no measurement raise "no
  counts", which my shell loop counted as the fault, and the stickiness in
  fact 3 poisoned the later probes. A corrected bisection with a fresh process
  per step and an added measurement gives fact 7 instead. I am recording the
  wrong answer rather than quietly replacing it.
