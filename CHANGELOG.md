# Changelog

## 1.34.3 (2026-10-16)

### Bug Fixes

- **runner:** set email templates only if config exists (7a4b7d3)

## 1.34.2 (2026-10-15)

### Bug Fixes

- Added missing staff in dev (9ca2312)

## 1.34.1 (2026-10-13)

### Bug Fixes

- **nats:** fixed python 3.14 error on asyncio.get_event_loop (e0d3430)

## 1.34.0 (2026-10-12)

### Documentation

- realign CHANGELOG with new format (e9d3bc3)

### Features

- **sellsy:** add readline package to allow interactive shell history navigation
  (2cec7ff)
- **runner:** adding interactive shell (a9d4359)

### Bug Fixes

- **api:** typo in promo-code 'scope' (58603e8)
- **sellsy:** incorrect result parsing getClientRef of v1 client (d1f5825)

## 1.33.2 (2026-10-07)

### Bug Fixes

- **sellsy:** wrong call to Individual on deleteFiles (31447f2)

## 1.33.1

Fix:

- sellsy: catch sellsy api error

## 1.33.0

Features:

- sellsy:
  - V2 connector is now operational
  - adding entrypoint to get service categories
  - adding support for File operations
  - task: affect task to common support staff by default

Quality:

- sellsy: add paymentId on stripe failure

## 1.32.1

Quality:

- operators: move bazile and phenix to opertos subfolder, and add typings

## 1.32.0

Features:

- upgrading dependencies
- nats: increase nats verbosity for received message
- bazile: improve Bazile API auth error
- runner: remove password from db connect string log
- toolbox: bazile add get-token command

Quality:

- sellsy: reorganize class field order
- sellsy: adding typing and logs

## 1.31.1

Featuresgg:

- sellsy: adding params in E_OBJ_NOT_LOADABLE logs
- sellsy: adding funnel New Line
- sellsy: raise error when cannot find opp status

Quality:

- operator: improve debug log

## 1.31.0

Feature:

- toolbox:selly: add tool to create opportunities

Quality:

- runner: move connectors from cli.py to common Runner
- sellsy: use common base class for v1 and v2 connectors

## 1.30.1

Fix:

- sellsy: add missing plan SerenPro

## 1.30.0

Feature:

- telecommown: adding new telecommown module

## 1.29.1

Feature

- runner: can now handle 'list' type in getArg

## 1.29.0

Feature

- sellsyV2: add function to link smartTags to objects in Sellsy

Quality

- sellsy: integrate unmaintained sellsyapi
- sellsy: split Sellsy v1 and v2
