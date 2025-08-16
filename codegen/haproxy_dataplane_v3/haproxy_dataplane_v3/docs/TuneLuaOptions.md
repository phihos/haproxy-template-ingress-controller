# TuneLuaOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**bool_sample_conversion** | **str** |  | [optional] 
**burst_timeout** | **int** |  | [optional] 
**forced_yield** | **int** |  | [optional] 
**log_loggers** | **str** |  | [optional] 
**log_stderr** | **str** |  | [optional] 
**maxmem** | **int** |  | [optional] 
**service_timeout** | **int** |  | [optional] 
**session_timeout** | **int** |  | [optional] 
**task_timeout** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.tune_lua_options import TuneLuaOptions

# TODO update the JSON string below
json = "{}"
# create an instance of TuneLuaOptions from a JSON string
tune_lua_options_instance = TuneLuaOptions.from_json(json)
# print the JSON string representation of the object
print(TuneLuaOptions.to_json())

# convert the object into a dict
tune_lua_options_dict = tune_lua_options_instance.to_dict()
# create an instance of TuneLuaOptions from a dict
tune_lua_options_from_dict = TuneLuaOptions.from_dict(tune_lua_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


