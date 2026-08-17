I checked both notebooks, and your frontend input should match the model's actual inference features, not the fields used to create the failure label.

Your trained model uses these 6 input fields:

classification
description
mfr_loo_event_count
mfr_countries_all
mfr_devices_all
description_len

The preprocessing pipeline then transforms these before sending them to the trained classifier.

How frontend → backend → model works
5

For example, your frontend could have a form like:

Device Classification: Cardiovascular
Device Description: Implantable cardiac defibrillator lead
Manufacturer ID: 12345

But there is an important point:

The frontend should NOT necessarily ask the user for all 6 model features.

Some features can be calculated by the backend.

Recommended flow
                 FRONTEND
                    │
                    │ User enters
                    │
                    ▼
        ┌─────────────────────────┐
        │ Classification           │
        │ Description              │
        │ Manufacturer ID          │
        └────────────┬────────────┘
                     │
                     │ JSON
                     ▼
                FASTAPI
                     │
          ┌──────────┴──────────┐
          │ Backend calculates  │
          │ derived features    │
          └──────────┬──────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │ mfr_loo_event_count     │
        │ mfr_countries_all       │
        │ mfr_devices_all         │
        │ description_len         │
        └────────────┬────────────┘
                     │
                     ▼
             pipeline.pkl
                     │
                     ▼
                model.pkl
                     │
                     ▼
          Failure probability
                     │
                     ▼
             Failure YES / NO
                     │
                     ▼
                 FRONTEND
What the frontend actually sends

For example:

{
  "classification": "Cardiovascular",
  "description": "implantable cardiac defibrillator lead insulation failure",
  "manufacturer_id": 12345
}

Then your FastAPI backend looks up/calculates the manufacturer-history features.

For example:

{
  "classification": "Cardiovascular",
  "description": "implantable cardiac defibrillator lead insulation failure",
  "mfr_loo_event_count": 40,
  "mfr_countries_all": 5,
  "mfr_devices_all": 20,
  "description_len": 58
}

That is exactly the type of dataframe your notebook expects.

Your own verification cell demonstrates this structure:

sample = pd.DataFrame([{
    "classification": "Cardiovascular",
    "description": "implantable cardiac defibrillator lead insulation failure",
    "mfr_loo_event_count": 40,
    "mfr_countries_all": 5,
    "mfr_devices_all": 20,
    "description_len": 58,
}])

Then:

X = pipeline.transform(sample)
prediction = model.predict(X)
probability = model.predict_proba(X)[:, 1]
What comes back to frontend?

The model produces:

Probability of failure = 0.78

Then your tuned threshold is applied.

For example, if your selected threshold is 0.54:

0.78 >= 0.54
       ↓
Failure = YES

The frontend could display:

Medical Device Risk Assessment


Classification:
Cardiovascular


Description:
Implantable cardiac defibrillator lead insulation failure


--------------------------------


Failure Probability: 78%


Prediction: HIGH RISK / FAILURE LIKELY
Very important: action_classification and determined_cause

These should NOT come from the frontend.

Your notebook explicitly uses them only to construct the historical failure label:

action_classification
        +
determined_cause
        ↓
   risk_score
        ↓
    failure

But during real prediction:

classification
description
manufacturer history
        ↓
      MODEL
        ↓
P(failure)
        ↓
Failure YES/NO

This is actually a strong point for your presentation:

"During training, historical action classification and determined cause were used only to generate the target label. They are excluded from the model features to prevent data leakage. During inference, the model predicts failure risk using information available for a new device."

One correction to your earlier understanding: your current notebook is predicting failure (binary), not risk_class (1/2/3). The uploaded training notebook explicitly defines failure as the target.

don't make it it like manufacture, id, make it as manufacture name, it looks good right, also whether the device level aggregates not help this
Which option do you prefer?

Improve your experience by letting us know which option is better.

Option 1
Option 2
I prefer this option
Skip
ChatGPT
Option 1

Yes — manufacturer name is much better for the frontend than asking the user for a manufacturer ID.

The important distinction is: what the user enters does not have to be identical to what the model ultimately receives.

For your project, I would design it like this:

FRONTEND


Manufacturer Name:
[ Medtronic                  ▼ ]


Device Classification:
[ Cardiovascular             ▼ ]


Device / Product Name:
[ Evera MRI ICD                 ]


Device Description:
[ Implantable cardiac defibrillator... ]


              [ Predict Risk ]

Then internally:

Manufacturer Name
"Medtronic"
      ↓
Backend / Database
      ↓
Find corresponding manufacturer record

      ↓
Calculate/retrieve historical aggregate features
      ↓
Model

So the user never needs to know something like manufacturer_id = 12345. That's an internal database key.

And yes — device-level aggregates can help or device_classification level aggregates

I would actually consider them useful.

Your current features include manufacturer-level historical information such as:

mfr_loo_event_count
mfr_countries_all
mfr_devices_all

These answer questions like:

"How much historical activity does this manufacturer have?"

But imagine one manufacturer produces 100 different devices. Some may have excellent histories while one particular device repeatedly appears in adverse-event records.

Manufacturer aggregates alone could hide that.

So you could have two levels of historical information:

                    New Device Input
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
       Manufacturer History       Device History


       mfr_event_count           device_event_count
       mfr_countries             device_countries
       mfr_devices               device_failure_count
              │                       │
              └───────────┬───────────┘
                          ▼
                     ML MODEL
                          ↓
                  Failure Probability

For example:

Manufacturer: Medtronic
Device: XYZ Cardiac Lead


Manufacturer history:
    10,000 historical events
    150 different devices


Device history:
    320 historical events
    85 previous failures

The device-specific 320 events / 85 failures could be much more informative about this particular device than simply knowing that the manufacturer has 10,000 events overall.

But there's one major caution: data leakage.

You cannot calculate something like:

device_failure_count = total failures for this device

using the current row's outcome or future records. During training, it needs to be calculated only from information that would have been available before that prediction. The same logic is why your notebook uses a leave-one-out style manufacturer feature (mfr_loo_event_count).

So I would make your architecture:

Frontend
   ↓
Manufacturer Name
Device/Product Name
Classification
Description
   ↓
FastAPI Backend
   ↓
Database / Historical Data
   ↓
┌───────────────────────────────┐
│ Manufacturer-level aggregates│
│ Device-level aggregates      │
│ Description-derived features │
└───────────────────────────────┘
   ↓
Preprocessing Pipeline
   ↓
ML Model
   ↓
Failure Probability
   ↓
Frontend

And manufacturer name + device name on the frontend makes the system much easier to understand and much more realistic for your demo.