commands = {
    "link-smarttags-to-object": lambda runner: (
        runner.getSellsyConnectorV2().linkSmartTagToOpportunity(
            runner.getArg("objectType"),
            runner.getArg("opportunityId"),
            runner.getArg("smartTagLabel"),
        )
    )
}


def execute(runner, command):  # pragma: no cover
    if command in commands:
        commands[command](runner)
