# A Flask service that turns uploaded invoices and receipts (PDF or image) into validated, structured records
## How it Works
- The upload is saved and gets a row with status uploaded.
- Claude extracts the fields against the Pydantic schema.
- The output is validated, with one retry that feeds the error back to the model.
- Business-rule checks run: line items against subtotal, subtotal plus tax against total, quantity times price against line total.
- The status ends as extracted, needs_review (with the flags stored) or failed
- Stack: `Python`, `Flask`, `Flask-SQLAlchemy`, `Pydantic`, `Anthropic SDK`, `pytest`

## Some Design Decisions Made
- **Schema-first:** one Pydantic model drives the prompt, the validation and the storage.
- **Validate, then retry, only once:** refusal and truncation from the LLM are terminal, does not retry in this case.
- **Separate Module that still checks LLM's Math:** money stays in Decimal throughout, and any record that fails the checks is flagged for a human.
- **Cost and latency logged per request:** about $0.007 and 4.5 s for the sample receipt.
- **Portable ORM types behind DATABASE_URL:** moving to a server database is a config change.
- **Tests fake the API at one seam:** the suite never touches the network

## WIP
- Containerization and Deployment with Docker
- Processing the LLM request as a background job with an additional thread
- Review page that shows the user the data from their upload (information currently in database, and upload returns a successful upload message)
- RESTful API so another system can curl the results
