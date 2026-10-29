# Aer "Kraus is empty": PRIVATE DRAFT, NOT FILED

**Status: nothing here has been posted anywhere.** No GitHub issue was opened,
no comment was posted, and nothing was sent to any external service. This
folder exists so my supervisor can read it before anything is filed. That is
decision L-040.

**Why it is not filed yet.** The only reproduction I have needs a real IBM
calibration card. Until we have checked what IBM's terms allow us to publish,
no calibration numbers go into a public issue. So the draft is held here.

## What is in this folder

| file | what it is |
|---|---|
| `ISSUE_DRAFT.md` | the issue text as I would post it, with the data-bearing part marked as a hole |
| `FINDINGS.md` | everything I measured about the fault, with the commands |
| `repro_synthetic_no_ibm_data.py` | a reproduction attempt built from invented numbers. It does NOT reproduce the fault. Safe to publish. |
| `repro_needs_local_card.py` | the script that DOES reproduce it. It contains no calibration numbers, but it reads them from `data/raw`, so it only runs on this machine. Not publishable until the terms question is settled. |

## The short version

`qiskit-aer` 0.17.2 raises

```
QiskitError: 'ERROR: [Experiment 0] QuantumError: Kraus is empty.'
```

for one compiled 10 qubit Bernstein-Vazirani circuit on a 156 qubit device
noise model built by `NoiseModel.from_backend` from a `Target`. There is no
empty Kraus anywhere in the Python side noise model. Two things make it look
like a bug in Aer rather than in our data:

1. The failure depends on noise entries for qubits the circuit never touches.
2. It flips on a sharp threshold in the number of measured qubits: six
   measured qubits run, seven or more fail, with everything else identical.

## What is NOT claimed

I have not found the cause inside Aer and I have not read its C++ source. I
also could not rebuild the fault from invented numbers, so I cannot yet hand a
maintainer anything they can run. Both of those are stated plainly in the
draft.

## What I checked before calling anything publishable

`ISSUE_DRAFT.md` was audited for calibration content. The only numbers left in
it are software versions and aggregate counts: 156 qubits, 790 local quantum
errors, 152 readout errors, 9 measurements, 15 qubits with T2 > T1, 95 Kraus
entries in the synthetic attempt. There is no T1, T2, gate error or readout
error value in it, and no list of qubit indices.

`FINDINGS.md` DOES carry qubit index lists, for example which qubits have
T2 > T1 on that card. Those are derived from a real calibration card. They are
fine for this folder, which is internal, but they are the part to look at
first if any of this is ever posted.
