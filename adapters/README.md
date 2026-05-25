# Adapters

Adapters turn model-specific outputs into PaveBench prediction JSONL.

Keep public adapters explicit about:

- model name and version
- prompt text or prompt hash
- number of model calls
- auxiliary data used
- whether the model was trained or fine-tuned on PaveBench data
- latency and cost accounting

Do not hide parcel clipping, image cleaning, or ensembles inside an adapter without declaring the method as `hybrid_production` or `image_generation_mask`.
