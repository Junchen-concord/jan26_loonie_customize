# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [16.15.7] - 2025-12-10

### Updated
Updated the path for red zone score using the V2 version of redzone

## [16.15.4] - 2025-12-10

### fixed
Fixed the balance transfer sourceID encoding logic to affect only transfers and deposits

## [16.15.4] - 2025-12-03

### Updated
-- Add logic for ignoring smaller amount (30% less than medium) in frequency and monthly income calculation

## [16.15.3] - 2025-11-28

### Updated
-- Add one more ignore word "salary"
-- Expand the logic for clustering two transactions whereone is a duplication of another in clustering for all categories and including check the WHO value as well
-- Add logic to make sure same who are clustered together (if they are ignored by stopwords)

## [16.15.2] - 2025-11-20

### Updated
-- Add more ignore words in payroll clustering, and force group more payrolls together if they have the same processed_clustering column value or one is a duplication of another
-- Add inferring payday logic for semi-monthly payrolls considering payday shift
-- Overwrite the logic for determining frequency between biweekly and semimonthly payrolls based on consistency checks with payment shifts
-- Add more occurance requirements for irregular income to be considered active

## [16.15.1] - 2025-11-17

### Updated
- Loose the active score logic for payrolls that both payroll and benefit has a 40 day leniency in check active core
- Logic update for payday prediction when regular payday and last payday doesn't align on W/B payrolls
### Updated

- [IA-2149](https://dmaassociates.atlassian.net/browse/IA-2149) - Reverted change from 16.14.15. Changed `StackingPrediction` to `stackingPrediction` in output.


## [16.15.0]

### Updated

- [IA-2149](https://dmaassociates.atlassian.net/browse/IA-2149) - Reverted change from 16.14.15. Changed `StackingPrediction` to `stackingPrediction` in output.

## [16.14.16]

### Updated

- Update preprocessing regex to improve clustering quality

## [16.14.15]

### Updated

- Updated NER logic to ensure its preprocessing logic is consistent with the Redis knowledge base (@Sai)

## [16.14.14] - 2025-11-11

### Updated

- Fine tune regular payday estimation for regular paydays for semimonthly payrolls that do not have a perfect match

## [16.14.13] - 2025-11-07

### Updated

- [IA-2122](https://dmaassociates.atlassian.net/browse/IA-2122) - Make `PAYMENT_AMOUNT_MIN/MAX` configurable as env var

## [16.14.12]

### Fixed

- [IA-2120](https://dmaassociates.atlassian.net/browse/IA-2120) - Add a hardcode logic that if the processed description (first level of cleaning) is the same, they should have same cluster label


## [16.14.11]

### Fixed

- [IA-2073](https://dmaassociates.atlassian.net/browse/IA-2073) - Fix bug where accounts without transactions could be the `recommendedBankAccount`

## [16.14.10]

### Updated

- [IA-2055](https://dmaassociates.atlassian.net/browse/IA-2055) - Add more tests for IA-2048

## [16.14.9]

### Fixed

- [IA-2048](https://dmaassociates.atlassian.net/browse/IA-2048) - Change Logic for app checker in using the standardized payday input from application

## [16.14.8]

### Added

- [IA-1804](https://dmaassociates.atlassian.net/browse/IA-1804) - Add more reasons to redzone

## [16.14.7]

### Added

- [IA-2017](https://dmaassociates.atlassian.net/browse/IA-2017) - Added test for agent label code path

## [16.14.6]

### Fixed

- [IA-1968](https://dmaassociates.atlassian.net/browse/IA-2036) - Default value bugfix for nextPayDay to make it consistent with older logic
 
## [16.14.5]

### Fixed

- [IA-1968](https://dmaassociates.atlassian.net/browse/IA-2029) - Fixed bug where bank check skipped to return "None" when only bank names are missing


## [16.14.4]

### Fixed

- [IA-1968](https://dmaassociates.atlassian.net/browse/IA-2029) - Fixed bug where bank check skipped to return "None" when only bank names are missing

## [16.14.3]

### Updated

- [IA-1961](https://dmaassociates.atlassian.net/browse/IA-1961) - Added scores section in v2 model output


## [16.14.0]

### Added

- [IA-1952](https://dmaassociates.atlassian.net/browse/IA-1952) - Added `RedisKnowledgeBase` labels in `fromModel` output

### Updated

- [IA-1961](https://dmaassociates.atlassian.net/browse/IA-1961) - Updated version of redzone models

## [16.13.7] - 2025-09-02

### Added

- [IA-1944](https://dmaassociates.atlassian.net/browse/IA-1944) - Added Redis KB support behind `REDIS_KB_ENABLED` environment variable (default off)
- [IA-1950](https://dmaassociates.atlassian.net/browse/IA-1950) - Added `executionTime` to model output

### Fixed

- [IA-1955](https://dmaassociates.atlassian.net/browse/IA-1955) - Fixed truthiness bug in `check_bank_from_chase`

## [16.13.4]

### Updated

- [IA-1854](https://dmaassociates.atlassian.net/browse/IA-1854) - Updated `ner_prediction` to use batches and thread for ~10% speedup

## [16.13.3]

### Added

- [IA-1532](https://dmaassociates.atlassian.net/browse/IA-1532) - Added input json tests for `model/v3/analyze`
- [IA-1855](https://dmaassociates.atlassian.net/browse/IA-1855) - Added FastAPI support 

### Updated

- [IA-1848](https://dmaassociates.atlassian.net/browse/IA-1848) - Updated regex to be precompiled, **lowering runtime by up to ~100ms**

## [16.13.0] - 2025-07-31

### Added

- [IA-1838](https://dmaassociates.atlassian.net/browse/IA-1838) - Added `model/v3/analyze` endpoint not requiring stringified input json 

## [16.12.7] - 2025-07-23

### Fixed

- [IA-1859](https://dmaassociates.atlassian.net/browse/IA-1859) - Fixed issue where `incomeSources.isDominant` could be boolean instead of integer

### Added

- [IA-1662](https://dmaassociates.atlassian.net/browse/IA-1662) - Added support for external model endpoints in `xgboost_scoring` (e.g. to support custom Hive model)

### Updated

- [IA-1799](https://dmaassociates.atlassian.net/browse/IA-1799) - Updated to preload `multi_cat_model.pkl` file on application startup

## [16.12.4] - 2025-07-11

### Fixed

numpy objects are now converted to native Python types in the output JSON instead of str. Changes `"True"` to `true` in `ApplicationChecker` output nodes.

## [16.12.3] - 2025-07-02

### Added

- [TDS-172](https://dmaassociates.atlassian.net/browse/TDS-172) - Added `overdraftFeeIncidents` and `nsfFeeIncidents` to output.

### Updated

- Remove some contradiction checks for additional reasons added
- [IA-1654](https://dmaassociates.atlassian.net/browse/IA-1654) - Updated `ibvCategory` logic to parse stringified lists

## [16.12.0] - 2025-06-19

### Updated

- [IA-1627](https://dmaassociates.atlassian.net/browse/IA-1627) - Split `assessmentReasons` to good reasons and bad reasons

## [16.11.5] - 2025-06-16

### Fixed

- [IA-1665](https://dmaassociates.atlassian.net/browse/IA-1665) - Fixed bug when knowledge base dfs were both empty
- Fix issue where `fNameMatchRate` and `lNameMatchRate` were `NaN`, convert to `null` with `simplejson` package

## [16.11.2] - 2025-06-11

### Updated

- Remove refund transactions from `inflowExcludeLoan` filed
- [IA-1660](https://dmaassociates.atlassian.net/browse/IA-1660) - Hard code `activeScore` of balance transfer to 0, they are not income.

### Added

- Added another few regex in regex kb for goodbread demo

## [16.10.6] - 2025-06-09

### Added

- Added a few regex in regex kb for goodbread demo

## [16.10.5] - 2025-05-29

### Fixed

- [IA-1625](https://dmaassociates.atlassian.net/browse/IA-1625) - Fixed issue with sourceID mismatch, regression from [IA-1419](https://dmaassociates.atlassian.net/browse/IA-1419)

## [16.10.4] - 2025-05-28

### Changed

- [IA-1566](https://dmaassociates.atlassian.net/browse/IA-1566) - Increased `gunicorn` timeout to 240 seconds

## [16.10.3] - 2025-05-19

### Added

### Fixed

- [IA-1576](https://dmaassociates.atlassian.net/browse/IA-1576) - Fixed issue where `overdraftIncidents` could be decimal return type

### Changed

### Removed

## [16.10.2] - 2025-05-16

### Added

### Fixed

- [IA-1419](https://dmaassociates.atlassian.net/browse/IA-1419) - Resolved many deprecation warnings from pandas, xgboost, apispec, etc. (350+ warnings resolved)
- [IA-1565](https://dmaassociates.atlassian.net/browse/IA-1565) - Fixed bug in `check_routing` function

### Changed

### Removed

- [IA-1536](https://dmaassociates.atlassian.net/browse/IA-1536) - Drops `"None"` or `null` values from `transactions` node in output

## [16.9.8] - 2025-04-21

### Added

### Fixed

### Changed

- [IA-1265](https://dmaassociates.atlassian.net/browse/IA-1265) - Changed maximum number of assessment reasons for 3-5, and feature value now needs to be in certain range to pop up as assessment reason.

### Removed

- [IA-1312](https://dmaassociates.atlassian.net/browse/IA-1312) - Fixed bug where `lendingGuide` recommended amount can go above maximum or below minimum


## [16.9.6] - 2025-04-08

### Added

- [IA-1232](https://dmaassociates.atlassian.net/browse/IA-1232) - Added check to discard any transactions after the `as_of_date`

### Fixed

### Changed

- [IA-1292](https://dmaassociates.atlassian.net/browse/IA-1292) - Renamed `sourceName` to `lenderName` in `loanSources`
- [IA-1294](https://dmaassociates.atlassian.net/browse/IA-1294) - Cast integer-like fields in `features` to be actual integers

### Removed

## [16.9.3] - 2025-03-26

### Added

- [IA-1258](https://dmaassociates.atlassian.net/browse/IA-1258) - Added checks for application data and IBV auth data
- [IA-1258](https://dmaassociates.atlassian.net/browse/IA-1258) - Added `features` output field with all the used redzone features

### Fixed

### Changed

### Removed

## [16.8.10] - 2025-03-13

### Added

- [IA-1140](https://dmaassociates.atlassian.net/browse/IA-1140) - Added support for using `id` transaction field when present

- [IA-1213](https://dmaassociates.atlassian.net/browse/IA-1213) - Added `asOfDate` to v2 output

### Fixed

### Changed

- [IA-1212](https://dmaassociates.atlassian.net/browse/IA-1212) - Updated `/model/v2/analyze` to support agent labeling inputs, removed `/model/v2/label/agent`

### Removed

## [16.8.8] - 2025-03-04

### Added

### Fixed

- [IA-1209](https://dmaassociates.atlassian.net/browse/IA-1209) - Fixed runError bug + NaNs in cashflow

### Changed

### Removed

## [16.8.7] - 2025-02-26

### Added

### Fixed

- [IA-1139](https://dmaassociates.atlassian.net/browse/IA-1139) - Fixed `transactions` with all `NaNs` and `errorDetails`

### Changed

- [IA-1111](https://dmaassociates.atlassian.net/browse/IA-1111) Updated `predict_transaction` to use previous IA output to ensure labeling stability for refreshes
- [IA-1141](https://dmaassociates.atlassian.net/browse/IA-1141) - Updated the agent label endpoint to accept new payload at `model/v2/label/agent`

### Removed

## [16.8.4] - 2025-02-14

### Added

- [IA-940](https://dmaassociates.atlassian.net/browse/IA-940) - Added Dapr integration for Redis knowledge base
- [IA-1106](https://dmaassociates.atlassian.net/browse/IA-1106) - Added API tests for each endpoint with sample payloads

### Fixed

### Changed

- [IA-1103](https://dmaassociates.atlassian.net/browse/IA-1103) - Updated endpoints that need `balance_df` to generate it from the `accounts` node

### Removed

## [16.8.0] - 2025-01-23

### Added

### Fixed

### Changed

- [IA-1088](https://dmaassociates.atlassian.net/browse/IA-1088) - Updated Swagger documentation to reflect latest API spec

### Removed

## [16.7.12] - 2025-01-22

### Added

- [IA-1073](https://dmaassociates.atlassian.net/browse/IA-1073) - Added `gunicorn` WSGI server to support concurrent execution within a replica

### Fixed

### Changed

- [IA-1034](https://dmaassociates.atlassian.net/browse/IA-1034) - Updated field names after 2nd round of iteration

### Removed

## [16.7.10] - 2025-01-15

### Added

- [PR-1044](https://dmaassociates.atlassian.net/browse/TDS-116) - Added Frequency, Frequency_pattern, Transaction_amount, Transaction_consistency, to create Redis KB keys
- [PR-1057](https://dmaassociates.atlassian.net/browse/IA-738) - Added logic to calculate `repeatOpportunity` field based off updated `repeat` score

### Fixed

### Changed

- [PR-1058](https://dmaassociates.atlassian.net/browse/IA-1034) - Updated v2 output for optimized API Integration
- [PR-1056](https://dmaassociates.atlassian.net/browse/IA-1040) - Updated to default to `CHECKING` for `accountType`
- [PR-1028](https://dmaassociates.atlassian.net/browse/IA-995) - Updated builds to use `poetry`, modern solution for dependency management


### Removed

## [16.7.5] - 2024-12-30

### Added

- [PR-989](https://dmaassociates.atlassian.net/browse/IA-978) - Added `/model/v1/transactions/analyze` endpoint
- [PR-989](https://dmaassociates.atlassian.net/browse/IA-464) - Added code for `RedisKnowledgeBase` implementation
- [PR-991](https://dmaassociates.atlassian.net/browse/IA-948) - Added endpoints to support Bankuity API Menu, cleaned up api files

### Fixed

### Changed

- [PR-1006](https://dmaassociates.atlassian.net/browse/IA-895) - Changed assessment reasons for ATP
- [PR-1021](https://dmaassociates.atlassian.net/browse/IA-903) - Updated account recommendation algorithm to be based on both regular income and red zone score

### Removed

## [16.7.0] - 2024-12-12

### Added

- [PR-916](https://dmaassociates.atlassian.net/browse/IA-812) - Added `/v1/label/change` endpoint to support agent label correction feature
- [PR-956](https://dmaassociates.atlassian.net/browse/IA-885) - Added `/v2/model/analyze` endpoint to support new streamlined output

### Fixed

### Changed

### Removed

## [16.6.6] - 2024-11-26

### Added

### Fixed

- [PR-927](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/927) - Fix `lendingGuide` error output to be `{}` instead of `[]`

### Changed

### Removed

## [16.6.5] - 2024-11-16

### Added

### Fixed

- [PR-894](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/894) - Resolve several warnings and pandas deprecations, decreased pipeline warnings by 75%
- [PR-893](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/893) - Fixed customerLevel scores not showing up when there is only one account

### Changed

- [PR-900](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/900) - Update `ModelPostProcessor` to remove `alertsAndInsights`, `redZoneBehavior` and add `scores`, `accounts`, and new sub-fields under `summaryInfo`, `additionalInfo`.

### Removed

- [PR-902](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/902) - Remove `accountGuid` in customer level red zone, cast to string in `paymentOnHoliday`

## [16.6.1] - 2024-11-08

### Added
- [PR-863](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/863) - Added OpenAPI spec with `marshmellow` and `apispec`
- [PR-873](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/873) - Added `scores` to ouptut, containing payin ratio score (`isBad`), repeat score (`repeat`), and loan paid off score (`loanPaidOff`)
- [PR-880](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/880) - Added support for toggling `OUTPUT_ATP_FEATURES` and `OUTPUT_REDZONE_EXPLANATION`

### Fixed

### Changed
- [PR-854](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/854) - Updated clustering algorithm for labeling related to `WHO` person's and organizations
- [PR-887](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/887) - Updated schema location of `redZoneBehavior` and `alertsAndInsights`

### Removed

## [16.5.12] - 2024-10-25

### Added

- [PR-844](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/844) Added `experimental` flag so that endpoints can airgap base model fields and API response

### Fixed

### Changed

- [PR-845](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/845) Refactor `ModelPostProcessor` to use newly added constant field names, move IAResponseFields enum to `src/api/types/enums`, changed error output (`additionalInfo`) to `{}`
- [PR-850](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/850) Split labeling and analysis into separate functions
- [PR-853](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/853) Replaced stable endpoints w/ singular stable endpoint (`/model/v1/analyze`). Includes functionality for an optional query param (`timeframe`) to truncate transactions to a requested timeframe (one_month, two_month, etc. up to six_month or all).

### Removed

- [PR-848](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/848) Removed redundant `recommendedAccount` from model output

## [16.5.7] - 2024-10-18

### Added

- [PR-838](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/838) Added account level `lendingGuide` in new `"accounts"` output field
- [PR-808](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/808) Added payment behavior near holidays

### Fixed

- [PR-827](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/827) Fixed issue where `runError` response not being sent

### Changed

- [PR-826](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/826) Updated `verbose` argument to `verbosity` and accept a list of fields to return back to caller (also preserving existing `"true"/"false"` behavior)
- [PR-822](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/822) Updated output to be fully camel-case

### Removed

## [16.5.2] - 2024-10-08

### Added

- [PR-780](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/780) Added unit tests for lending guide
- [PR-794](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/794) Added `model_version` to health_check endpoint

### Fixed

- [PR-785](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/785) Small fix to ensure max amount is at least min amount for lending guide

### Changed

- [PR-751](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/751) Updated loan labeling to not pass through xgboost model to be exclusively handled by knowledge base (and adds obvious loans to the knowledge base to compensate)
- [PR-793](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/793) Updated green zone reason text

### Removed

## [16.4.2] - 2024-09-26

### Added

- [PR-765](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/765) Added `lendingGuide` output field
- [PR-765](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/765) Added `green_zone_reasons` to the `alertsAndInsightsCustomer` field
- [PR-765](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/765) Added `WHO_CAT` to `creditTrans` and `debitTrans`

### Fixed

### Changed

### Removed

## [16.4.1] - 2024-09-16

### Added

- [PR-742](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/742) Added deployment instructions to `README.md`

### Fixed

### Changed

- [PR-742](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/742) Un-stringified API response

### Removed

## [16.4.0] - 2024-09-05

### Added

- [PR-716](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/716) Added `ibvCategory` to model output
- [PR-657](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/657) Read version from `version.txt` and use for image tags  
- [PR-650](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/650) Support threshold as a parameter from request, abstract code  
- [PR-643](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/643) Add `docker-compose.yaml` for local service development

### Fixed

### Changed

- [PR-643](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/643) Aligns `requirements.txt` with what is in MDLV16 conda environment on Dev server

### Removed

## [16.3.0] - 2024-08-05

### Added

- [PR-635](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/635) Add `—-no-cache` in docker build
- [PR-631](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/631) Merged in containerized repo to support both script and service runs. Pipeline now pushes to ACR with `RUN_TYPE='service'`.
- [PR-627](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/627) Add environment variables (`LOW_REDZONE_SCORE_CM`) to allow threshold to be toggled without code changes
- [PR-626](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/626) Use `create_app` to pre-load assets on service startup
- [PR-623](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/623) Add support for running model on 90, 180 day timeframes, add fastapi file
- [PR-571](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/571) Add Dockerfile, add flask server w/ standalone model execution endpoint

### Fixed

### Changed

- [PR-439](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/613) Optimization: De-dupe descriptions prior to `ner_prediction`, optimize `build_cluster_level_features`, increased line-length in linter to 120
- [PR-444](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/444) Code cleanup: Added `@staticmethod` where appropriate, replaced print statements with `@timer` decorator, removed `test_scripts` from code coverage report, added types to function args and return type

### Removed

- [PR-439](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/613) Removed logic associated with customerized cashmax model

## [16.2.0] - 2024-05-16

### Added


### Fixed


### Changed

- [PR-439](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/439) Optimization: stream text in ner prediction (`nlp.pipe()`), other minor optimizations.

### Removed

- [PR-439](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/439) Optimization: Remove all `read_csv` calls, replace with static python variables.

## [16.1.0] - 2024-05-13 

### Added

- [PR-430](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/430) Add `modelVersion` to output.
- [PR-424](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/424) Add `/labeling` directory to encapsulate labeling functionality in single package.
- [PR-423](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/423) Optimization: loading stopwords and uscities.

### Fixed

- [PR-421](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/421) Optimization (and bug fix): `good_to_debit_by_peak` and `make_time_series` functions.
- [PR-422](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/422) Fix [IA-395](https://dmaassociates.atlassian.net/browse/IA-395) by formatting `currentBalanceDate` consistently.

### Changed

- [PR-429](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/429) Refactor `/postprocess` directory to map to model output.
- [PR-428](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/428) Updated `requirements.txt` to reflect the V16 environment.
- [PR-428](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/428) Removed modules saved in `multi_cat_model.pkl` so that it does not require the modules in IA to load.

### Removed

## [16.0.1] - 2024-04-23

### Added

- [PR-390](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/390) Add `pull_request_template.md`
- [IA-306](https://dmaassociates.atlassian.net/browse/IA-306) V16.1 model development
- [IA-31O](https://dmaassociates.atlassian.net/browse/IA-310) Add WHO, HOW, WHY based knowledgebase prior to model prediction
- [IA-308](https://dmaassociates.atlassian.net/browse/IA-308) Add Named Entity Recognition model to process transactions
- Analyzer model (old income_analyzer, loan_analyzer, transfer_analyzer) retrain using the corrected handlabel data and NER label. Red zone model is also retrained because xgboost version changed.
- [PR 379](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/379): Add keys for customer level red zone and account recommendation in the key `additionalInfo`
- [PR 360](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/360): Add `CHANGELOG.md`
- [PR 353](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/353): Add keys for customer level red zone (`redZone_multi`, `alertsInsights_multi`, `redZoneExplanation_multi`) and key for recommended account (`recommend_acc`)

### Fixed

- [PR-401](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/401) Fixed test pipeline to reflect model updates

### Changed

- [PR-393](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16/pullrequest/393) Change linter from `flake8` to `ruff`
- [PR 356](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/356): Wrap redzone explanation code to output only when config variable `OUTPUT_REDZONE_EXPLANATION` is set to True. Default to False.

- [PR 355](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/355): Decrease red zone model score thresholds for Speedy, CashMax, and customized model.

- [PR 351](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/351): Wrap all of the customized CashMax model code to only execute if `RUN_CASHMAX_REDZONEMODEL` config variable is set to True. Default to False. (ref: [IA-349](https://dmaassociates.atlassian.net/browse/IA-349))

### Removed

- [IA-309](https://dmaassociates.atlassian.net/browse/IA-309) Changed clustering algorithm logic. All old analyzer py files have been removed, a new multiclass classification xgboost model will replace the functionalities of all previous analyzers and the stacking model and predict the model in one step. This will reduce the redundency in the model execution, as well as helping explain the model's decision.

## [15.5.2] - 2024-03-19

### Added

- [PR 326](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/326): Add CashMax customized red zone model, calculates separate score as `riskScore_CM` (ref: [IA-329](https://dmaassociates.atlassian.net/browse/IA-329))

### Fixed

- [PR 332](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/332): Fix bug that allowed `NaN` to show up in `accountGuid`  (ref: [IA-344](https://dmaassociates.atlassian.net/browse/IA-344))

### Changed

### Removed

## [15.5.0] - 2024-02-26

### Added

- [PR 304](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/304): Add knowledge base to the model

### Fixed

### Changed

- [PR 301](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/301): Optimize pre-processing of city names, now removes city only if it is followed by a state abbreviation (e.g. Dallas, TX) 

### Removed

## [15.4.5] - 2024-02-06

### Added

### Fixed

- [PR 288](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/288): Fix local test issue with multiple `TestData` classes

### Changed

- [PR 289](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/289): Improve redzone explanation wording

### Removed

## [15.4.4] - 2024-01-30

### Added

- [PR 279](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/279): Add red zone explanation reads directly into alerts
- [PR 277](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/277): Add red zone explanation using [shap](https://shap.readthedocs.io/en/latest/)
### Fixed

- [PR 273](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/273): Handle `KeyError` on empty data input, return 501

### Changed

- [PR 286](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/286): Update frequency calculation logic so regular payday will not show "None" if the frequency is not "I"
- [PR 283](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/283): Fix linting error by adding E402 to ignore script
- [PR 279](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/279): Change no income detected to no active income detected
- [PR 193](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/193): Checks hostname to add debug statements only if on `MDLTESTBED01` or `NJ-CB-DEV-VH1`

### Removed

- [PR 285](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/285): Remove "None" from alerts

## [15.4.3] - 2024-01-18

### Added

### Fixed

### Changed

- [PR 261](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/261): Changes `Retirements & Benefits` label to `Benefit`
- [PR 250](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/250): Bank card report update
- [PR 257](https://dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer/pullrequest/257): active income logic change for benefit

### Removed

## [15.4.2] - 2024-01-04

### Added

### Fixed

### Changed

### Removed

## [15.3.1] - 2023-12-19

### Added

### Fixed

### Changed

### Removed

## [15.2.0] - 2023-11-17

### Added

### Fixed

### Changed

### Removed
