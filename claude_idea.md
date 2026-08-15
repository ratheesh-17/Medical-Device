What's in the dataset

Your archive has three linked CSVs from the ICIJ Implant Files:

File	Rows	Role
devices.csv	118,249	one row per device, has your target column risk_class
events.csv	124,969	one row per recall/safety-alert/field-safety-notice, links to devices via device_id
manufacturers.csv	32,531	one row per manufacturer, links via manufacturer_id

Every event maps to exactly one device (avg ~1.06 events/device, max 116), so your join path is events → devices → manufacturers.

The critical finding: your target variable is thin and geographically skewed

risk_class (values 1, 2, 3 — this is the device's inherent regulatory risk classification, not the recall severity) is:

Missing in 72% of rows (85,301 of 118,249) — the rest is junk labels like "Unclassified," "HDE," "II" that don't belong in a clean 3-class scheme
Present only for USA-sourced records. I checked: of the 32,602 rows with a clean 1/2/3 label, literally 100% are country == USA. None of the other ~30 countries in the dataset report this field.

So the real, honest framing of this problem is: "predict FDA device risk class (I/II/III) from device metadata," trained on ~32.6k USA records — not a global failure-prediction model, even though the brief says "distributed worldwide." That distinction matters a lot for the "Use Case Understanding" criterion on your rubric — if your team frames it as global risk prediction without flagging this, a sharp evaluator will catch it.

Within that usable 32.6k subset, feature quality is actually good: classification (device category, e.g. Cardiovascular/Orthopedic/Radiology) is 99.3% populated, description is 99.99% populated, and you have a manufacturer link for all of them.

Class imbalance is real: class 2 = 76%, class 1 = 17%, class 3 = 7%. Plain accuracy will be misleading — you'll need macro-F1 or per-class precision/recall (matches "Model Performance and Evaluation" on your rubric).

events.csv has a second, different label

action_classification (Class I/II/III, in inconsistent formats — "Class 2," "II," "2" all appear and need normalization) describes the severity of the recall action itself, not the device's inherent risk class. I cross-tabbed the two where both exist (35k rows): they're only weakly related — risk_class=2 devices dominate across every action_classification bucket. So these are genuinely different signals, not duplicates. You could:

use action_classification as an auxiliary/engineered feature (does this device have a history of severe recalls?), or
pick it as an alternative or secondary target if your team wants a richer, less USA-locked classification task (it's populated for more countries, though still ~58% missing overall and needs label cleanup).
My view on architecture
Preprocessing: normalize the messy label formats in both risk_class and action_classification, drop the ~72% unlabeled devices.csv rows for the target subset, engineer manufacturer-level features (recall count, distinct countries, repeat-offender flag) from events.csv by aggregating per manufacturer_id.
Features: classification (categorical) + description (TF-IDF or embeddings — it's free-text device names/descriptions) + manufacturer aggregates. Description text is your richest signal since risk class correlates with device type.
Model: start with a strong tabular baseline (Random Forest / XGBoost with class-weighting or SMOTE for the imbalance) as your defensible baseline, then try a text-embedding-augmented model if time allows — gives you a nice "alternatives considered" story for the rubric's "Proposed architecture and various alternatives" line.
Evaluation: macro-F1, per-class precision/recall, confusion matrix — directly hits "Model Performance and Evaluation."
Deployment/UI: a simple form (device description + category → predicted risk class + confidence) is enough; wire it through a basic API, mention CI/CD even if only conceptually in your roadmap slide, since "Deployment and Integration" is explicitly scored.
Presentation: I'd open with the missingness/USA-only finding — showing you understood the data's real limits (rather than glossing over them) is exactly what "Use Case Understanding and Relevance" and "clarity of problem statement" are rewarding.