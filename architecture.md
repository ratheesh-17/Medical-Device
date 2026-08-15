Medical Device Risk Prediction System — Updated Architecture

The complete idea is:

3 CSV Files
    ↓
Clean the data
    ↓
Select reliable risk_class labels
    ↓
Join + aggregate related information
    ↓
Create useful ML features
    ↓
Train multiple classification models
    ↓
Evaluate using Macro-F1, Precision, Recall, etc.
    ↓
Select best model
    ↓
Save model
    ↓
FastAPI prediction API
    ↓
User enters new device information
    ↓
Predict Risk Class I / II / III
    ↓
Show probability + explanation

Now let's understand each stage.

1. Data Sources

We have three linked CSV files.

devices.csv

This is the main dataset.

One row represents one medical device.

It contains things such as:

device_id
name
category/classification
description
manufacturer_id
risk_class
...

The most important thing here is:

risk_class

This is our target variable.

1 → Class I
2 → Class II
3 → Class III
events.csv

This contains historical events such as recalls/safety-related events.

One device can have multiple events.

For example:

Device A
   ↓
Event 1
Event 2
Event 3
Event 4

It connects to the device using:

device_id

It may contain information such as:

event_id
device_id
type
reason
date
action_classification
...

action_classification is not our target.

It describes the classification/severity of the recall action.

manufacturers.csv

This contains manufacturer information.

It connects using:

manufacturer_id

For example:

manufacturer_id = 105


Manufacturer:
ABC Medical Devices
Country:
USA
2. Data Preprocessing

Now we clean the raw data.

There are several things to do.

Missing values

For example:

description = NULL
category = NULL

We decide how to handle them depending on the column.

Standardization

The data can have inconsistent formats.

For example, in action_classification:

Class 1
I
1
class i

These can be standardized to:

1

Similarly:

Class 2
II
2

becomes:

2
Target validation

This is particularly important for our project.

We don't blindly use every value in risk_class.

We keep clean:

1
2
3

and exclude things such as:

Unclassified
HDE
II
other invalid/inconsistent values

depending on the actual normalization rules we establish.

The resulting dataset is our reliable labeled dataset.

3. Why are we training mainly on the USA records?

This is one of the most important parts of our architecture.

We discovered that the clean risk_class labels are essentially available only for the U.S. records.

Therefore:

118,249 devices
       ↓
clean risk_class
       ↓
~32,600 usable labeled records
       ↓
Training dataset

We should not artificially create labels for the other countries.

Instead, we train the supervised model using the reliable labeled records.

4. Data Integration

This is where we connect the three datasets.

But we shouldn't simply say:

"Merge all three CSVs."

Because events.csv can contain multiple events for one device.

Instead, we do:

Join + Aggregate

Think of it like this:

             devices
                │
                │ device_id
                ↓
             events
                │
                │ aggregate
                ↓
       Event History Features
                │
                │
manufacturers ──┘

For example, suppose:

Device A

has:

5 historical events

Instead of putting all five event rows directly into the training table, we can create features such as:

total_events = 5

and possibly:

distinct_event_types = 3
recent_event_count = 2

Similarly, manufacturer information is connected using:

manufacturer_id

Eventually we create something like:

Final Feature Table
────────────────────────────────────
device_id
category
description
manufacturer_country
event_count
recall_count
distinct_event_types
...
risk_class
────────────────────────────────────
5. Feature Engineering

Now we convert raw information into information the ML model can understand.

We can divide the features into five groups.

A. Device Features

Information directly about the device.

For example:

category
device type
description length
name-related information
B. Event History Features

Information obtained by aggregating historical events.

For example:

total_event_count
recall_count
number_of_event_types
historical_action_classification counts
C. Manufacturer Features

Information about the manufacturer.

For example:

manufacturer event count
number of affected devices
number of countries
repeat-offender indicator

Example:

Manufacturer X


Previous events = 18
Affected devices = 12
Countries = 4
Repeat offender = Yes

This becomes numerical/categorical information that the model can use.

6. Text / NLP Features

This is an important part because the device description contains valuable information.

For example:

"Implantable cardiac monitoring device
used for continuous cardiac rhythm monitoring..."

A machine-learning model cannot directly understand this sentence.

So we convert the text into numerical representation.

For the first version, we can use:

TF-IDF

For example:

Description
     ↓
Text preprocessing
     ↓
TF-IDF
     ↓
Numerical feature vectors
     ↓
ML model

Later, if time permits, we can experiment with embeddings.

But TF-IDF is a very reasonable and defendable starting point for a 7-day hackathon.

7. Temporal Features

We can also extract time-related information from events.

For example:

event dates
      ↓
event frequency
recent event count
time since previous event

This can help capture historical patterns.

But there's a very important rule:

Don't use future information that wouldn't have been available at the time of prediction.

Otherwise we create data leakage.

For example, if we're pretending to predict a device's risk based on information available at an earlier point, we cannot use events that happened afterward.

8. Final Training Dataset

After preprocessing, joining, and feature engineering, we have something like:

                FEATURES
                   ↓
 ┌────────────────────────────────────┐
 │ Device features                    │
 │ Manufacturer features              │
 │ Event-history features             │
 │ Text features                      │
 │ Temporal features                  │
 └──────────────────┬─────────────────┘
                    ↓
               TARGET
                    ↓
              risk_class
              /    |    \
             1     2     3

Now we're ready for machine learning.

9. Train / Validation / Test Split

We don't train the model on everything.

We divide the labeled data into:

Training data
      ↓
used to learn patterns


Validation data
      ↓
used for tuning/model selection


Test data
      ↓
used for final unbiased evaluation

For example, conceptually:

70% → Training
15% → Validation
15% → Test

The exact split can be decided during implementation.

Because the classes are imbalanced, we should use stratified splitting, so each split maintains approximately the same Class I/II/III proportions.

10. Train Multiple Models

Instead of immediately choosing one algorithm, we compare several.

Logistic Regression

Our simple baseline.

It tells us:

"How well can a relatively simple model perform?"

Random Forest

Handles nonlinear relationships and mixed features well.

XGBoost

A strong tabular ML model that can capture complex relationships.

We can compare:

Logistic Regression
        ↓
Random Forest
        ↓
XGBoost
11. Hyperparameter Tuning

Each model has settings called hyperparameters.

For example, Random Forest has:

number of trees
maximum depth
minimum samples

XGBoost has things like:

learning rate
number of estimators
maximum depth

We try different combinations to find a good configuration.

12. Evaluation

Now we evaluate the models.

Our main metric is:

Macro-F1

Why?

Because our classes are imbalanced:

Class II ≈ 76%
Class I  ≈ 17%
Class III ≈ 7%

Accuracy could look good simply because Class II dominates.

So we use:

Macro-F1
Precision
Recall
Per-class F1
Confusion Matrix

We can still report accuracy, but it isn't our main decision metric.

13. Selecting the Best Model

Suppose we get:

                 Macro-F1
Logistic Reg.      0.71
Random Forest      0.78
XGBoost            0.82

Then XGBoost would be our candidate best model.

But we shouldn't blindly choose based on one number.

We also inspect:

Class I performance
Class II performance
Class III performance
Confusion matrix
Precision
Recall

Especially Class III because it's the minority class.

14. Save the Best Model

Once we've selected the model, we save:

trained_model
+
preprocessing pipeline
+
TF-IDF/vectorizer
+
encoders

This is important.

We don't want the API to retrain the model every time someone asks for a prediction.

Instead:

Training
    ↓
Best model
    ↓
Save
    ↓
Deployment
15. FastAPI Prediction API

Now we create the backend.

For example:

POST /predict

The user sends:

{
    "description": "...",
    "category": "...",
    "manufacturer": "..."
}

The API performs:

Input
 ↓
Same preprocessing
 ↓
Feature transformation
 ↓
Saved ML model
 ↓
Prediction
16. Model Output

The API returns something like:

Predicted Risk Class:
Class II


Probabilities:
Class I   → 12%
Class II  → 81%
Class III → 7%

We can also return explanation information.

For example:

Important factors:
- Device category
- Description terms
- Manufacturer history
- Historical event pattern

Be careful with the word explanation here.

If we use XGBoost, we can use something like SHAP to provide model explanations rather than simply claiming that those features caused the prediction.

17. Dashboard / User Interface

The frontend communicates with FastAPI.

The flow becomes:

User
 ↓
Frontend
 ↓
FastAPI
 ↓
ML Model
 ↓
Prediction
 ↓
FastAPI
 ↓
Frontend
 ↓
User

The dashboard can show:

┌──────────────────────────────┐
│ Medical Device Risk Predictor│
├──────────────────────────────┤
│ Description:                 │
│ [........................]   │
│                              │
│ Category:                    │
│ [ Cardiovascular ]           │
│                              │
│       [ Predict ]            │
└──────────────────────────────┘

Result:

Predicted Risk Class
       CLASS II


Class I      12%
Class II     81%
Class III     7%


Top contributing features
• Device category
• Description
• Manufacturer history
18. What about other countries?

This is where your earlier question becomes interesting.

After training on the reliable U.S. labeled data:

USA labeled devices
       ↓
     TRAIN
       ↓
   ML MODEL
       ↓
Other-country devices
with missing risk_class
       ↓
   PREDICTION
       ↓
Estimated Class I/II/III

Yes, technically we can generate predictions for them.

But we should label them as:

Model-predicted risk class

not:

Official FDA risk classification

And we should validate how well the model generalizes to other countries before making strong claims.

19. Monitoring & Retraining

This is the final production-level part.

Suppose new data arrives later.

We can monitor:

Data quality
Are values missing?
Are formats changing?
Are categories changing?
Data drift
Has the distribution of input data changed?
Prediction drift
Are we suddenly predicting Class II for almost everything?
Model performance

Once new ground-truth labels become available:

Macro-F1
Precision
Recall

can be recalculated.

If performance significantly drops:

New labeled data
      ↓
Retraining
      ↓
New model
      ↓
Validation
      ↓
Deployment

For your hackathon, this can be presented as a production/future enhancement unless you actually implement it.

The complete architecture in one simple story

When presenting, you can explain the entire architecture like this:

"First, we collect device, event, and manufacturer information from the three linked datasets. We clean and standardize the data and retain reliable Class I, II, and III risk_class labels for supervised learning. We then connect the datasets using device_id and manufacturer_id, while aggregating the one-to-many event history instead of directly duplicating device records. From this integrated data, we create device, manufacturer, event-history, text, and temporal features. We split the labeled data into training, validation, and test sets and train multiple classification models such as Logistic Regression, Random Forest, and XGBoost. We evaluate them mainly using Macro-F1 because our classes are imbalanced, along with precision, recall, per-class F1, and the confusion matrix. We select the best-performing model, save it together with the preprocessing pipeline, and expose it through a FastAPI prediction service. The frontend sends new device information to the API, and the model returns the predicted Class I, II, or III along with class probabilities and model explanations."

The most important flow to remember
CSV DATA
   ↓
CLEAN
   ↓
VALIDATE risk_class
   ↓
JOIN + AGGREGATE
   ↓
FEATURE ENGINEERING
   ↓
TRAIN
   ↓
EVALUATE
   ↓
BEST MODEL
   ↓
FASTAPI
   ↓
USER INPUT
   ↓
RISK CLASS I / II / III
   ↓
PROBABILITY + EXPLANATION

That is the actual core architecture of your project. Everything else—alerts, real-time streams, automated retraining, hospital integration—is secondary/future functionality.

but I think database part is misiing

Yes. You're absolutely right. The current architecture is missing an explicit database layer.

And for your project, adding a database makes the architecture much more complete because your CSVs are the initial data source, while the database can become the system's persistent storage.

Where the database should go

I would change the architecture to:

                ┌─────────────────────┐
                │     CSV DATA        │
                │                     │
                │ devices.csv         │
                │ events.csv          │
                │ manufacturers.csv   │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │ DATA PREPROCESSING   │
                │ Cleaning             │
                │ Standardization     │
                │ Target validation    │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │      DATABASE       │
                │                     │
                │ Devices             │
                │ Events              │
                │ Manufacturers       │
                │ Predictions         │
                │ Model information   │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │ JOIN & AGGREGATION  │
                │ + FEATURE ENGINEERING│
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │    ML PIPELINE      │
                │ Train / Validate    │
                │ Test / Tune         │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │     BEST MODEL      │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │      FastAPI        │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │     DASHBOARD       │
                └─────────────────────┘

But there's an even better way to structure it.

What exactly should the database store?

I wouldn't put everything into one giant table.

We can have tables like:

1. devices
device_id
name
category
description
manufacturer_id
country
risk_class
2. manufacturers
manufacturer_id
name
country
...
3. events
event_id
device_id
event_type
reason
event_date
action_classification
...

This preserves the original relationships.

Manufacturer
      │
      │ manufacturer_id
      ↓
   Device
      │
      │ device_id
      ↓
    Events
Then we can have a prediction table

This is where the database becomes particularly useful for your application.

predictions
prediction_id
device_id
predicted_risk_class
class_1_probability
class_2_probability
class_3_probability
model_version
prediction_timestamp

For example:

prediction_id = 1024


device_id = D4587


predicted_risk_class = II


class_1_probability = 0.12
class_2_probability = 0.81
class_3_probability = 0.07


model_version = xgboost_v2


prediction_timestamp = 2026-08-14 ...

Now every prediction made through your application can be stored.

How the actual application works

Suppose a user enters a new device.

User
 ↓
Frontend
 ↓
FastAPI
 ↓
Database
 ↓
Retrieve device/manufacturer/event information
 ↓
Feature Engineering
 ↓
ML Model
 ↓
Prediction
 ↓
Database
 ↓
Frontend

So the database isn't just sitting there.

It becomes the persistent storage layer of the application.

There are actually TWO different flows

This is important for your architecture.

Training flow
CSV files
    ↓
Preprocessing
    ↓
Database
    ↓
Feature Engineering
    ↓
Training
    ↓
Evaluation
    ↓
Best Model
    ↓
Model Storage
Prediction flow
User
 ↓
Frontend
 ↓
FastAPI
 ↓
Database
 ↓
Feature preparation
 ↓
Saved ML Model
 ↓
Prediction
 ↓
Store prediction in DB
 ↓
Return result
 ↓
Frontend

This separation makes your architecture much clearer.

One more thing: don't force the database into ML training unnecessarily

There's an important architectural decision here.

You can load the cleaned CSV data into MySQL/PostgreSQL and train from the database.

But for your 7-day hackathon, I would recommend:

Raw CSV
   ↓
Python preprocessing
   ↓
Cleaned data
   ↓
Database

Then use Python/Pandas/SQL to create the training dataset.

For example:

MySQL/PostgreSQL
       ↓
SQL query
       ↓
Pandas
       ↓
Feature engineering
       ↓
ML model

This gives you both:

Database knowledge
Proper ML pipeline

without unnecessarily complicating the project.

Where does FastAPI fit?

FastAPI becomes the bridge between the frontend, database and model:

                  ┌──────────────┐
                  │   Frontend   │
                  └──────┬───────┘
                         │
                         ↓
                  ┌──────────────┐
                  │   FastAPI    │
                  └───┬──────┬───┘
                      │      │
              ┌───────┘      └────────┐
              ↓                        ↓
        ┌───────────┐            ┌──────────┐
        │ Database  │            │ ML Model │
        └───────────┘            └──────────┘

FastAPI can:

receive device information
query the database
prepare features
call the trained model
return prediction
save prediction history
So yes — your observation is correct.

Your architecture should have:

CSV → Preprocessing → Database → Feature Engineering → ML → Model → FastAPI → UI

and, importantly, the prediction result should also go back into the database.

That gives you a proper end-to-end AI application architecture, rather than just an ML notebook with a UI attached.