# LuaOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**load_per_thread** | **str** |  | [optional] 
**loads** | [**List[LuaOptionsLoadsInner]**](LuaOptionsLoadsInner.md) |  | [optional] 
**prepend_path** | [**List[LuaOptionsPrependPathInner]**](LuaOptionsPrependPathInner.md) |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.lua_options import LuaOptions

# TODO update the JSON string below
json = "{}"
# create an instance of LuaOptions from a JSON string
lua_options_instance = LuaOptions.from_json(json)
# print the JSON string representation of the object
print(LuaOptions.to_json())

# convert the object into a dict
lua_options_dict = lua_options_instance.to_dict()
# create an instance of LuaOptions from a dict
lua_options_from_dict = LuaOptions.from_dict(lua_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


