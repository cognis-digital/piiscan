# Demo 01 - Basic PII scan of a customer export

A data governance analyst at a warehouse team receives `customers_sample.csv`,
an ad-hoc export landed in a raw-zone S3 bucket. Before it is promoted to a
curated schema, policy requires a PII scan so that sensitive columns can be
tagged, masked, or access-restricted.

## Input

`customers_sample.csv` contains a realistic mix of columns:

- `customer_id`     - opaque surrogate key (NOT PII)
- `full_name`       - person names (name-hint + value pattern)
- `email`           - email addresses (high confidence)
- `phone`           - US phone numbers
- `ssn`             - US SSNs (validated via area/group rules)
- `card_number`     - credit card PANs (validated via Luhn)
- `signup_ip`       - IPv4 addresses
- `birth_date`      - dates of birth
- `notes`           - free text that happens to leak an email/phone
- `region`          - low-cardinality category (NOT PII)

## Run it

```bash
python -m piiscan scan demos/01-basic/customers_sample.csv --format table
# JSON for downstream tagging / governance catalogs:
python -m piiscan scan demos/01-basic/customers_sample.csv --format json
```

## What to expect

- `ssn` and `card_number` surface as **CRITICAL** risk (validated, high
  sensitivity).
- `email`, `phone`, `birth_date` surface as HIGH/MEDIUM.
- `customer_id` and `region` produce no findings.
- The process exits with code **2** because PII was detected (use this in CI to
  block promotion of un-tagged datasets).

Note how `card_number` only flags values that pass the Luhn checksum, so a
plain numeric id column would not be a false positive.
