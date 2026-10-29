# BandPact protocol

## Inputs

An opening wallet owns its namespace. `pact_id` and `unit` use 1–40 ASCII letters, digits, hyphen or underscore. Peer must be a nonzero 20-byte hexadecimal address distinct from owner. Addresses are normalized to lowercase. The unit code is an opaque label, not a conversion table or asserted SI unit.

A report payload is JSON with exactly `metric`, `population`, `window`, `basis`, `lower`, `upper`. Text facets are each 12–500 stripped characters; total payload is 80–2600 characters and is not truncated. Bounds must be literal JSON integers (booleans and floats are rejected), with `0 <= lower <= upper <= 10^12`. Intervals are closed and count whole declared units. Values are retained exactly.

Only the signing participant can submit its report, once. The submit API cannot name another report author. The owner cannot fill the peer slot. Both reports are required before comparison, and either participant can request that comparison exactly once. A failed consensus leaves READY and does not create an assessment.

## Semantic alignment

The ordered facets are metric, population, window, basis. SAME requires affirmative equivalence, including unit scale, population exclusions, exact period/time zone and counting/aggregation rules. DIFFERENT indicates explicit incompatibility; UNCLEAR indicates missing, contradictory or ambiguous descriptions. The prompt requires consistency across fields inside each report and treats inputs as untrusted data. It performs no external fact lookup.

Leader and validators independently produce all four labels. The custom validator rejects malformed outputs, non-return leader results and any decision mismatch. It is not a format-only check. Deterministic code inserts the entire paired source facet text into each finding. Any supplied evidence field must equal those original texts. Explanations are contextual accepted-leader prose; equality of explanations is not required or claimed. Decision labels, not prose, control state.

Bounds and approvals are excluded from both leader and validator prompts. The shared unit code is shown but is not sufficient to infer equivalence on its own. No numeric extraction or model-generated interval exists.

## Resolution and consent

If any label is DIFFERENT, result is INCOMPARABLE. Otherwise any UNCLEAR gives REVIEW. Neither exposes an approvable intersection. If all labels are SAME, compute `lo = max(lower_A, lower_B)` and `hi = min(upper_A, upper_B)`. If `lo > hi`, result is DISJOINT. Otherwise `[lo,hi]` is the exact common band and status becomes AWAITING_APPROVAL. Touching endpoints produce a valid singleton band.

Only parties may approve. Each approval checks AWAITING_APPROVAL, exact result digest and no prior approval by this same wallet. Two unique party addresses change status to AGREED. Either approval order is valid. A repeated owner signature never substitutes for peer consent. There is no edit, override or resolution method for blocked pacts. Create a fresh pact for corrections.

## Digest

Canonicalization is Python `json.dumps(value, sort_keys=True, separators=(",", ":"))`, with default ASCII escaping. SHA-256 hashes its UTF-8 bytes.

The result digest binds `{protocol, owner, id, parties, unit, reports, alignment, resolution}`. `resolution` contains the assessment status and computed intersection. `reports` is keyed by lowercase signer wallet; `parties` fixes owner/peer order. Alignment includes source evidence and accepted explanations.

For an AGREED record, reconstruct resolution using status AWAITING_APPROVAL and the immutable intersection. Approvals are outside the digest, so a digest alone cannot establish either signature or final agreement. Verify authenticated finalized state and receipts. Owner/ID/party binding prevents a result digest from being reused for a different pact.

## Integration

Pin the intended contract source and chain 61999. Bind to expected owner, ID and participants; verify protocol, immutable reports, semantic labels, integer intersection, digest, two unique approvals and finalized state. Treat an arbitrary imported JSON or a user-selected clone contract as untrusted. Signatures identify wallets, not independent people or real data sources. AGREED reconciles the submitted claims only and must not replace data-quality or authorization checks in the consumer.

All development sends use zero value and `leaderOnly:false`. Success requires FINALIZED, MAJORITY_AGREE, successful leader execution, exact sender/recipient/method/argument binding and matching finalized readback. Persist hashes and resume them rather than re-signing on timeouts. Failures and unknown outcomes require inspection; the tools do not automatically retry writes or appeal.
