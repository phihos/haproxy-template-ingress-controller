# Kubernetes Operator Core Logic
# This package contains the main operator functionality split by concern:
# resource watching, template rendering, pod management, and synchronization
#
# Note: Package exports intentionally minimal to avoid circular imports.
# Most imports are done directly from submodules to prevent dependency cycles
# between operator modules, models, and other core components.
