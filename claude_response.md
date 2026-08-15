Genuinely, this is good work — better than most hackathon teams will produce. But I'd push back on a few things before you go further.

What's actually strong:

The leakage catch on device-level event counts is the single best point in that whole exchange. If you'd used a device's own recall history as a feature, you'd essentially be predicting risk_class from a signal that's downstream of it — that's the kind of mistake that tanks a model silently (looks great in validation, means nothing in production). Fixing it by moving to manufacturer-level aggregates is the right call.
The confidence threshold in the API response is a nice, cheap touch that maps directly onto "real-world safety consideration" for a medical-device use case — exactly the kind of detail evaluators remember.
Pipeline/model separation (fit once in the notebook, never refit inside FastAPI) is correct and worth drilling into your teammates — this is the most common way ML hackathon demos silently break.

Where I'd push back:

Leakage isn't fully closed. The fix only covers event counts. If anyone joins other event fields onto the training table — action_classification, determined_cause, date_terminated — before training, you can still leak, since those events may postdate (or directly encode) the risk_class assignment. Worth an explicit rule: device-level event fields are off-limits entirely, only manufacturer-level aggregates.
CI/CD is documented but not built. Your rubric explicitly scores "use of CI/CD pipelines," and right now that's a doc file, not a pipeline. Even a bare-bones GitHub Actions workflow that runs lint + a couple of pytest tests on push would turn "we mentioned CI/CD" into "we have CI/CD" — cheap to add, and it's a scored line item.
No test suite planned. "Technical Implementation and Source Code Quality" rewards best practices, and a tests/ folder with even 5-10 tests (schema validation, one service function, one route) signals professionalism disproportionate to the effort.
The build order creates an 8-person bottleneck. The suggested sequence (notebook → DB/API → React form → …) means most of your team sits idle until one person finishes the notebook. For a team this size, get a trivial baseline model (even a dummy classifier) exporting pipeline.pkl/model.pkl on day one, so backend and frontend can build against real interfaces immediately while the ML side iterates toward XGBoost in parallel.
No explicit validation strategy stated. Given the class imbalance (76/17/7), you want a stratified train/test split at minimum, ideally stratified k-fold for a more defensible Macro-F1 number — this should get nailed down before anyone starts the notebook, not left implicit.