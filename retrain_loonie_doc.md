# FPDAA Retrain Plan and Summary

## Purpose
Build a labeled training dataset from model response JSONs and SQL labels, evaluate the current AutoGluon model on that dataset, then retrain and report AUC using leakage-safe splits.

## Data Sources
- **Model response JSONs**: `/Users/starsrain/nov2025_concord/loonie_bankuity_rerun/rerun_output_JSONs_V3`
- **SQL labels (FPDAA)**: LMS + Bankuity tables joined via IBV token
- **Exported dataset**: `/Users/starsrain/jan2026_concord/jan2026_loonie_customize/retrain_data/features_with_fpdaa.parquet`

## SQL Label Extraction + Join Concept
1. Pull approved loans and their FPDAA outcomes from `LF_LMSMASTER`.
2. Map those records to IBV tokens from `BankuityPostOnboarding.dbo.SpeedyAnalysis` using experiment name `loonie_rerun_V3`.
3. Deduplicate by IBV token to get a single labeled row per IBV status.
4. Output `IBVStatusID`, `FPDAA`, `FPDAA_matured` for joining with extracted features.

## Feature Extraction (JSON)
**Primary path**:
- Read features from `customerInfo.scores.features` with priority for `accountLevel` and `customerLevel`.
**Fallback**:
- If scores are missing, fall back to `accounts[].features`.
**Required fields**:
- Include `currentBalance` from `accounts` if missing in feature rows.
- Add `IBVStatusID` from the JSON top-level (from `ibv_status_id`) for joining.

Implementation lives in `notebooks/01_extract_features.ipynb`:
- Helpers: `_get_score_feature_rows`, `_get_account_feature_rows`, `extract_features_from_output`.
- Join: `features_df` ⨝ `df_perf_orig` on `IBVStatusID` (inner join).
- Export: `features_with_fpdaa.parquet`.

## Dataset Construction
- Each JSON may have multiple accounts → multiple feature rows per file.
- Post-join labeled rows are filtered to those with `FPDAA` available.
- The exported parquet is the single source of truth for training and evaluation.

## Current Model AUC
- Notebook: `notebooks/02_auc_current_model.ipynb`
- Loads the production model at `src/model/autogluon_models_FPDAA_20250904_010918`.
- Aligns features to the model’s expected schema and computes ROC AUC on the labeled dataset.
- Baseline AUC observed on labeled rerun data: `0.5972375560469769`.

## Retraining Pipeline
- Notebook: `notebooks/03_retrain_model.ipynb`
- Data split: 70/15/15 with **grouped splitting by `IBVStatusID`** to prevent leakage across accounts.
- Leakage-safe feature set excludes `FPDAA`, `FPDAA_matured`, and `IBVStatusID`.
- Trains AutoGluon with default `medium` preset and evaluates AUC on validation and test splits.
- Summary tables are produced for both retrained and production model leaderboards.

## Model Consumption (Current Repo)
- **Runtime path**: `config.REDZONE_MODEL_FILE_PATH_V2` points to `src/model/autogluon_models_FPDAA_20250904_010918`.
- **Scoring flow**: `alerts_and_insights.py` calls `auto_gluon_prediction(...)` from `auto_gluon_scoring.py`.
- **Loader**: `TabularPredictor.load(model_path, require_py_version_match=False)`.
- **Prediction**: `predict_proba(..., model="CatBoost_r137_BAG_L1_FULL")` is used by default.
- **Calibration**: scores are calibrated via `Calibrator(config.CALIBRATOR_DATA_PATH)`.
- **Containers**: Docker builds include the `src/model` directory, so the model folder used in config is packaged into the image.

## Implementation Notes
- Group-aware splits are essential due to multiple accounts per IBV token.
- AUC values near 1.0 are a leakage red flag; ensure grouping and feature exclusion are applied.
- If replicating the production model, use the production leaderboard and model params as reference for hyperparameters.

## Next Steps
- Re-run `notebooks/03_retrain_model.ipynb` after any data updates.
- Decide whether to lock retraining to the production model family/hyperparameters.
- If promoting the retrained model:
  - Copy the chosen model folder into `src/model/` (or update `REDZONE_MODEL_FILE_PATH_V2` to the new folder).
  - Ensure `auto_gluon_scoring.py` uses the intended model name (or switch to `model_best`).
  - Rebuild the Docker image so the new model is shipped in the container.
- Archive results (AUC + leaderboard) in the Confluence report.
