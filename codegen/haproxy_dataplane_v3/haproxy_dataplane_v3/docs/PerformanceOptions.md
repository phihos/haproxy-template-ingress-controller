# PerformanceOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**busy_polling** | **bool** |  | [optional] 
**max_spread_checks** | **int** |  | [optional] 
**maxcompcpuusage** | **int** |  | [optional] 
**maxcomprate** | **int** |  | [optional] 
**maxconn** | **int** |  | [optional] 
**maxconnrate** | **int** |  | [optional] 
**maxpipes** | **int** |  | [optional] 
**maxsessrate** | **int** |  | [optional] 
**maxzlibmem** | **int** |  | [optional] 
**noepoll** | **bool** |  | [optional] 
**noevports** | **bool** |  | [optional] 
**nogetaddrinfo** | **bool** |  | [optional] 
**nokqueue** | **bool** |  | [optional] 
**nopoll** | **bool** |  | [optional] 
**noreuseport** | **bool** |  | [optional] 
**nosplice** | **bool** |  | [optional] 
**profiling_memory** | **str** |  | [optional] 
**profiling_tasks** | **str** |  | [optional] 
**server_state_base** | **str** |  | [optional] 
**server_state_file** | **str** |  | [optional] 
**spread_checks** | **int** |  | [optional] 
**thread_hard_limit** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.performance_options import PerformanceOptions

# TODO update the JSON string below
json = "{}"
# create an instance of PerformanceOptions from a JSON string
performance_options_instance = PerformanceOptions.from_json(json)
# print the JSON string representation of the object
print(PerformanceOptions.to_json())

# convert the object into a dict
performance_options_dict = performance_options_instance.to_dict()
# create an instance of PerformanceOptions from a dict
performance_options_from_dict = PerformanceOptions.from_dict(performance_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


