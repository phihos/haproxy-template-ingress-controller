# LuaOptionsPrependPathInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**path** | **str** |  | 
**type** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.lua_options_prepend_path_inner import LuaOptionsPrependPathInner

# TODO update the JSON string below
json = "{}"
# create an instance of LuaOptionsPrependPathInner from a JSON string
lua_options_prepend_path_inner_instance = LuaOptionsPrependPathInner.from_json(json)
# print the JSON string representation of the object
print(LuaOptionsPrependPathInner.to_json())

# convert the object into a dict
lua_options_prepend_path_inner_dict = lua_options_prepend_path_inner_instance.to_dict()
# create an instance of LuaOptionsPrependPathInner from a dict
lua_options_prepend_path_inner_from_dict = LuaOptionsPrependPathInner.from_dict(lua_options_prepend_path_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


