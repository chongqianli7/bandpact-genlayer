# Validation

Verified on 2026-10-29 using only **Stable Studionet, chain 61999**, RPC `https://studio.genlayer.com/api`.

Canonical contract: `0xb07d57b5F8275722605C7a97D4A979d32Ce8d2E7`.

Source SHA-256: `f027b83a1dfb4b1a96b7398eaef146bdf225e5c0ce5b8441b376c380bcdfd1a0`.

## Local checks

- **21 mocked-host tests passed**, executing the actual deployable file. These include all 81 four-facet label vectors, all 441 pairs of closed integer intervals over endpoints 0–5 against an independent set-intersection oracle, source evidence binding, numeric prompt withholding, permissions, immutable reports, duplicate approvals, digest mismatch, incomplete reports and independent validator disagreement.
- Official `genvm-lint check`: three lint checks passed, validation passed, six public methods (four writes, two views). The generated ABI is `schema.json`.
- Pinned SDK Direct Mode passed with real SDK storage and calldata: report submission from separate senders, exact intersection, independent validator acceptance/rejection, one-party pending status and two-party AGREED state. Model responses are mocked. Direct Mode is native Python, not live network or Wasm execution.
- Python 3.12.14, genvm-linter 0.11.0, genlayer-test 0.29.2, genlayer-py 0.16.3, GenLayerJS 1.1.8, viem 2.57.8. The exact Python dependency is pinned in the source header. A newer-runner advisory was not treated as proof of stable compatibility: actual deployment and source readback were verified.

## Real network execution

All seven transactions below reached FINALIZED with MAJORITY_AGREE, successful leader execution and `leader_only:false`. Writes transfer zero value. The complete report/approval cycle is recorded in [evidence/studionet.json](evidence/studionet.json).

| Action | Hash | Execution |
|---|---|---|
| deploy | `0x800dbbb7703ee12aa2174a595b7f9204d2da4fd52b05821a78e9d5ae320fd35d` | FINALIZED / SUCCESS |
| open | `0xba5e023fb144bd540a63cc063c096590f90cf157f8d02088c2bc87ff6b4e810e` | FINALIZED / SUCCESS |
| report_a | `0xf722753ad7809af5c0929ed694e431983c71dbd63b703b85cf1295d27b202cff` | FINALIZED / SUCCESS |
| report_b | `0x82cf5264a69badc158aebe61a1ed36ed53ce61530b82a4b309545cdb6b5cdbaa` | FINALIZED / SUCCESS |
| compare | `0xa70ad818602a430d0d9d32193f2bcb118c428c6e2ea30d797d34b169caca932c` | FINALIZED / SUCCESS |
| approve_a | `0xaf8a58d780d6836882d084d7300d1de7c73271ce4ff18ad1c44c2bfa5f0b5f5c` | FINALIZED / SUCCESS |
| approve_b | `0x3414c0b29cc4a9f1bb7526ca954f65041121d9030bc743adce549d2832d96c29` | FINALIZED / SUCCESS |

Both signed report definitions were independently classified SAME for metric, population, window and basis. Numeric bands were excluded from model prompts. Code intersected `[90,110]` and `[100,120]` to `[100,110]`. The compare receipt records 3 agree and 2 idle votes; idle is not counted as acceptance.

`checkpoints.compared` records AWAITING_APPROVAL with no approvals. `checkpoints.one_approval` records the same state with exactly one approval. The second distinct party's approval produced the final AGREED record with both signers and the unchanged result digest and intersection.

The read-only verifier re-fetches deployed source, finalized state and all transaction receipts. It checks full-consensus mode, signer/contract/method/exact calldata arguments, source SHA-256, integer intersection and independently reconstructed canonical result digest. It also compares the full chain record with the saved final record. The evidence contains projected public receipt fields, omitting node configuration, timing logs and redundant byte arrays. The hashes can retrieve complete public RPC responses.

The count bands and archive descriptions are synthetic. Both dedicated test wallets were controlled by one operator; address separation does not prove independent institutions. No archive objects were counted or fetched. No user wallet key, user funds or private data were used. No paid model API was configured. No transaction was resent or appealed.

## Coverage boundaries

INCOMPARABLE, REVIEW, DISJOINT, touching singleton bands, wrong-party rejection, replay rejection and digest mismatch are local test coverage only, not all observed on chain. No browser-wallet signing, actual measurement, production data connector or independent data-source authentication is claimed. The common band is an agreement over submitted assertions, not an accuracy estimate or statistical confidence result. Semantic consensus can still be wrong.

Official references:

- https://docs.genlayer.com/developers/networks
- https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle
- https://docs.genlayer.com/api-references/genlayer-js/contracts
