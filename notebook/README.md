# Notebook

This folder contains the Jupyter notebook for data preprocessing, feature engineering, model training, and evaluation.

## Files

| File | Purpose |
|------|---------|
| `model_training.ipynb` | Full ML pipeline — EDA → preprocessing → feature engineering → training → evaluation → export |

## Output

After running the notebook, two files are exported to `backend/app/ml/`:

- `pipeline.pkl` — fitted preprocessor (scaler + encoder + TF-IDF vectorizer)
- `model.pkl` — trained XGBoost classifier

## Order of Execution

1. Run all cells top to bottom
2. Final cells export `pipeline.pkl` and `model.pkl`
3. Start the FastAPI backend — it loads these files at startup
