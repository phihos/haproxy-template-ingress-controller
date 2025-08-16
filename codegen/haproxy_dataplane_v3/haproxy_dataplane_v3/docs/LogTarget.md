# LogTarget

Per-instance logging of events and traffic.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **str** |  | [optional] 
**facility** | **str** |  | [optional] 
**format** | **str** |  | [optional] 
**var_global** | **bool** |  | [optional] 
**length** | **int** |  | [optional] 
**level** | **str** |  | [optional] 
**metadata** | **object** |  | [optional] 
**minlevel** | **str** |  | [optional] 
**nolog** | **bool** |  | [optional] 
**profile** | **str** |  | [optional] 
**sample_range** | **str** |  | [optional] 
**sample_size** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.log_target import LogTarget

# TODO update the JSON string below
json = "{}"
# create an instance of LogTarget from a JSON string
log_target_instance = LogTarget.from_json(json)
# print the JSON string representation of the object
print(LogTarget.to_json())

# convert the object into a dict
log_target_dict = log_target_instance.to_dict()
# create an instance of LogTarget from a dict
log_target_from_dict = LogTarget.from_dict(log_target_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


