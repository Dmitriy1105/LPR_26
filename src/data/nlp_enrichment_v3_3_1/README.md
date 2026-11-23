# NLP enrichment v3.3.1 — synthetic demonstration overlay

This branch does **not** modify the 767 CRM records, existing activity descriptions or IDs. It adds a separate evidence overlay for 90 existing multi-participant activities.

Run from the repository root:

```bash
node scripts/generate_nlp_enrichment_v3_3_1.mjs
node scripts/extract_nlp_influence_v3_3_1.mjs
node --test tests/nlp_enrichment_v3_3_1.test.mjs
```

- `scenarios.json`: synthetic evidence, names, participant IDs and source activity IDs.
- `ground_truth.json`: generator-only labels, never used by extractor.
- `extracted_relations.json`: extracted, **unverified** directed action hypotheses.
- Negative examples represent co-participation without directed action.
- Action labels are not proof of causal influence, decision authority, or human confirmation.

**Limitations:** This is a deterministic rule-based demo. Synthetic ground-truth matching is not an independent measure of production NLP performance. Evaluate separately on held-out texts before claiming generalization.
