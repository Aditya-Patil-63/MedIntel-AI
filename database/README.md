# Database Module

Data storage and schema definitions for MedIntel AI.

## Status

**Phase 2 — Schema Defined** ✅

SQLAlchemy ORM models created. SQLite used as the initial database.

---

## Schema Overview

The database has **7 tables**:

```
users
  │
  ├── reports
  │     ├── test_results
  │     ├── predictions
  │     ├── prescriptions
  │     │     └── medicines
  │     └── summaries (also linked to users)
  │
  └── summaries
```

### Tables

| Table           | Key Columns                                                    |
|-----------------|----------------------------------------------------------------|
| `users`         | id, name, email, language_preference, created_at               |
| `reports`       | id, user_id, file_name, file_type, document_type, status       |
| `test_results`  | id, report_id, test_name, test_value, unit, classification     |
| `predictions`   | id, report_id, condition, risk_score, risk_level, disclaimer   |
| `prescriptions` | id, report_id, doctor_name, hospital_name, prescription_date   |
| `medicines`     | id, prescription_id, medicine_name, dosage, frequency, duration|
| `summaries`     | id, user_id, report_id, language, summary_text, pdf_path       |

### Key Design Decisions

- **Deterministic classification**: `test_results.classification` uses reference ranges, not ML
- **Mandatory disclaimers**: `predictions.disclaimer` and `summaries.disclaimer` have non-null defaults
- **User verification**: `test_results.is_user_verified` and `prescriptions.is_user_verified` flags
- **Cascade deletes**: Deleting a user cascades to reports, predictions, summaries, etc.
- **Extensible enums**: `report_file_type`, `extraction_method_type`, etc. can be extended

## Schema Definition

The ORM models are defined in:

[backend/app/models/models.py](../backend/app/models/models.py)

## Planned Enhancements (Later Phases)

- Migration scripts (Alembic) for schema evolution
- Seed data for development and testing (synthetic only)
- Database upgrade path from SQLite to PostgreSQL if needed
