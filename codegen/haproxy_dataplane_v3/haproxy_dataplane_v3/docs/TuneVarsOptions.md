# TuneVarsOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**global_max_size** | **int** |  | [optional] 
**proc_max_size** | **int** |  | [optional] 
**reqres_max_size** | **int** |  | [optional] 
**sess_max_size** | **int** |  | [optional] 
**txn_max_size** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.tune_vars_options import TuneVarsOptions

# TODO update the JSON string below
json = "{}"
# create an instance of TuneVarsOptions from a JSON string
tune_vars_options_instance = TuneVarsOptions.from_json(json)
# print the JSON string representation of the object
print(TuneVarsOptions.to_json())

# convert the object into a dict
tune_vars_options_dict = tune_vars_options_instance.to_dict()
# create an instance of TuneVarsOptions from a dict
tune_vars_options_from_dict = TuneVarsOptions.from_dict(tune_vars_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


