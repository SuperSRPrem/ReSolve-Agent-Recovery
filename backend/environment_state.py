DEFAULT_ENVIRONMENT_STATE = {
    "databaseRunning": False,
    "backendRunning": True,
    "apiHealthy": False,
    "cacheHealthy": True,
    "connectionPoolHealthy": False,
    "replicaHealthy": False,
    "configurationHealthy": False,
    "credentialsHealthy": True,
    "errorSignature": "unknown",
}


def createEnvironmentState(overrides=None):
    """
    Creates a new ReSolve environment-state snapshot.

    Every environment implementation should expose state using
    this common shape whenever possible.

    MockEnvironment may simulate these values.

    Docker/API environments will later derive these values from
    actual infrastructure observations.
    """

    state = DEFAULT_ENVIRONMENT_STATE.copy()

    if overrides:
        state.update(overrides)

    return state


def copyEnvironmentState(state):
    """
    Returns a defensive copy of an environment state.

    Recovery components should consume snapshots instead of
    receiving direct access to mutable environment internals.
    """

    if state is None:
        return createEnvironmentState()

    return dict(state)