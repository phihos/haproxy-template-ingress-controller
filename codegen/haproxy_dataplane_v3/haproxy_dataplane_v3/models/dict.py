# coding: utf-8

"""
Compatibility shim for OpenAPI Generator v7.14.0 bug.

The generator incorrectly imports Dict from models.dict instead of using typing.Dict
in maps_api.py and storage_api.py. This shim provides the Dict type to make the
generated code work without modification.

This file can be removed when the generator bug is fixed in a future version.

See: https://github.com/OpenAPITools/openapi-generator/issues (Dict import bug)
"""

from typing import Dict

__all__ = ['Dict']