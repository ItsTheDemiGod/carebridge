**POST-HOC (descriptive, done after the official run; not an official result; nothing in the system was changed in response).**

Seeded document-level cluster bootstrap on the 40 test documents (seed 20261028, 2000 resamples, percentile 95%): each resample draws 40 documents with replacement and keeps all five readings (and all explanation lines) of a document together; the statistic is the ratio of sums. Wilson = the official interval (treats readings as independent). Width ratio = cluster width / Wilson width.

| metric | k / n | proportion | official Wilson 95% | cluster bootstrap 95% | width ratio |
|---|---|---|---|---|---|
| must-confirm share | 406 / 795 | 0.511 | [0.476, 0.545] | [0.436, 0.578] | 2.04 |
| fully correct, raw | 205 / 782 | 0.262 | [0.233, 0.294] | [0.202, 0.333] | 2.13 |
| fully correct, after rules | 705 / 794 | 0.888 | [0.864, 0.908] | [0.846, 0.926] | 1.83 |
| interaction_ready share | 389 / 795 | 0.489 | [0.455, 0.524] | [0.423, 0.564] | 2.02 |
| schedule_ready share | 285 / 795 | 0.358 | [0.326, 0.392] | [0.293, 0.432] | 2.09 |
| wrong schedule among schedule_ready | 2 / 285 | 0.007 | [0.002, 0.025] | [0.000, 0.017] | 0.74 |
| explanation lines verified, en | 239 / 255 | 0.937 | [0.900, 0.961] | [0.914, 0.961] | 0.77 |
| explanation lines verified, ta | 46 / 255 | 0.180 | [0.138, 0.232] | [0.130, 0.232] | 1.09 |
| explanation lines verified, hi | 170 / 255 | 0.667 | [0.607, 0.722] | [0.607, 0.732] | 1.08 |

### Wrong resolved_generic among interaction_ready (0 events)

- Readings: 0 of 389; rule of three, 95% upper bound 0.0077 (official Wilson upper bound 0.010). Treats the 389 readings as independent, which they are not.
- Distinct medicines: the 389 readings are 106 distinct (document, medicine) pairs that were interaction_ready in at least one condition; rule of three on those: 0.0283.
- Documents: 39 of 40 documents contributed at least one interaction_ready medicine; with 0 documents showing a wrong one, the one-sided exact 95% upper bound for the share of documents is 0.0739 (rule of three 0.0769). This is a bound on documents, not on medicines.
- Reading: the per-reading figure (0.0077) is the most optimistic; the per-distinct-medicine figure (0.0283) is the more honest scale for a per-medicine statement, and the document-level figure (about 0.074) is the cautious one.
