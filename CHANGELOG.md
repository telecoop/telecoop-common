# 1.32.1

Quality:

- operators: move bazile and phenix to opertos subfolder, and add typings

# 1.32.0

Features:

- upgrading dependencies
- nats: increase nats verbosity for received message
- bazile: improve Bazile API auth error
- runner: remove password from db connect string log
- toolbox: bazile add get-token command

Quality:

- sellsy: reorganize class field order
- sellsy: adding typing and logs

# 1.31.1

Features:

- sellsy: adding params in E_OBJ_NOT_LOADABLE logs
- sellsy: adding funnel New Line
- sellsy: raise error when cannot find opp status

Quality:

- operator: improve debug log

# 1.31.0

Feature:

- toolbox:selly: add tool to create opportunities

Quality:

- runner: move connectors from cli.py to common Runner
- sellsy: use common base class for v1 and v2 connectors

# 1.30.1

Fix:

- sellsy: add missing plan SerenPro

# 1.30.0

Feature:

- telecommown: adding new telecommown module

# 1.29.1

Feature

- runner: can now handle 'list' type in getArg

# 1.29.0

Feature

- sellsyV2: add function to link smartTags to objects in Sellsy

Quality

- sellsy: integrate unmaintained sellsyapi
- sellsy: split Sellsy v1 and v2
