from enum import Enum


class GlobalBaseCpuPolicy(str, Enum):
    EFFICIENCY = "efficiency"
    FIRST_USABLE_NODE = "first-usable-node"
    GROUP_BY_2_CCX = "group-by-2-ccx"
    GROUP_BY_2_CLUSTERS = "group-by-2-clusters"
    GROUP_BY_3_CCX = "group-by-3-ccx"
    GROUP_BY_3_CLUSTERS = "group-by-3-clusters"
    GROUP_BY_4_CCX = "group-by-4-ccx"
    GROUP_BY_4_CLUSTER = "group-by-4-cluster"
    GROUP_BY_CCX = "group-by-ccx"
    GROUP_BY_CLUSTER = "group-by-cluster"
    NONE = "none"
    PERFORMANCE = "performance"
    RESOURCE = "resource"

    def __str__(self) -> str:
        return str(self.value)
