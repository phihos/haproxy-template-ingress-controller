# StatsHttpRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cond** | **str** |  | [optional] 
**cond_test** | **str** |  | [optional] 
**realm** | **str** |  | [optional] 
**type** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.stats_http_request import StatsHttpRequest

# TODO update the JSON string below
json = "{}"
# create an instance of StatsHttpRequest from a JSON string
stats_http_request_instance = StatsHttpRequest.from_json(json)
# print the JSON string representation of the object
print(StatsHttpRequest.to_json())

# convert the object into a dict
stats_http_request_dict = stats_http_request_instance.to_dict()
# create an instance of StatsHttpRequest from a dict
stats_http_request_from_dict = StatsHttpRequest.from_dict(stats_http_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


