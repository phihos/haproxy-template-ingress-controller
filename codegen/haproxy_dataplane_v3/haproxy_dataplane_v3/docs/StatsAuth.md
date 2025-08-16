# StatsAuth


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**passwd** | **str** |  | 
**user** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.stats_auth import StatsAuth

# TODO update the JSON string below
json = "{}"
# create an instance of StatsAuth from a JSON string
stats_auth_instance = StatsAuth.from_json(json)
# print the JSON string representation of the object
print(StatsAuth.to_json())

# convert the object into a dict
stats_auth_dict = stats_auth_instance.to_dict()
# create an instance of StatsAuth from a dict
stats_auth_from_dict = StatsAuth.from_dict(stats_auth_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


