# GEN-010.11B.1 — blinded ChatGPT annotations

Sample: `GEN01011B1-SEED-20261125`  
Records: 220  
Annotator: ChatGPT GPT-6.2 (in-conversation semantic annotation)

## Files

- `gen01011b1_llm_annotations.json.gz` — locked annotation JSON, gzip-compressed.
- `gen01011b1_annotation_qc.json` — structural/schema QC.
- `gen01011b1_annotation_manifest.json` — input/output hashes and annotation provenance.

Decompress locally:

```bash
gzip -dk gen01011b1_llm_annotations.json.gz
```

## Blindness and provenance

Only reviewer-visible `subject` and `body` were used for classification. The separate Ground Truth answer key was not opened. No external provider API was called; the annotations were produced by ChatGPT in the conversation.

The annotation file is locked by SHA-256 in the manifest. Do not change labels after unlocking the answer key; any corrections must create a new annotation version and retain this baseline.

## Current QC

- 220 unique review IDs and complete input coverage: PASS.
- All 11 event labels represented: PASS.
- Label schema, confidence and rating ranges: PASS.
- Ground Truth fields absent: PASS.
- Predicted distribution: approve 22; complete_task 22; delegate 20; recommend 20; object 20; revise 20; unit_approval 20; reject 20; close 20; review 19; request_information 17.

These are predicted labels, not evaluation metrics. Accuracy, precision, recall, F1 and confusion matrix are not available until the separate restricted answer key is opened after annotation lock.
