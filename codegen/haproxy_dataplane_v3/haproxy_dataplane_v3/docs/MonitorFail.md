# MonitorFail


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cond** | **str** |  | 
**cond_test** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.monitor_fail import MonitorFail

# TODO update the JSON string below
json = "{}"
# create an instance of MonitorFail from a JSON string
monitor_fail_instance = MonitorFail.from_json(json)
# print the JSON string representation of the object
print(MonitorFail.to_json())

# convert the object into a dict
monitor_fail_dict = monitor_fail_instance.to_dict()
# create an instance of MonitorFail from a dict
monitor_fail_from_dict = MonitorFail.from_dict(monitor_fail_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


