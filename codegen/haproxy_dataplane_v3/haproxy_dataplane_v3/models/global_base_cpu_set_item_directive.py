from enum import Enum


class GlobalBaseCpuSetItemDirective(str, Enum):
    DROP_CLUSTER = "drop-cluster"
    DROP_CORE = "drop-core"
    DROP_CPU = "drop-cpu"
    DROP_NODE = "drop-node"
    DROP_THREAD = "drop-thread"
    ONLY_CLUSTER = "only-cluster"
    ONLY_CORE = "only-core"
    ONLY_CPU = "only-cpu"
    ONLY_NODE = "only-node"
    ONLY_THREAD = "only-thread"
    RESET = "reset"

    def __str__(self) -> str:
        return str(self.value)
