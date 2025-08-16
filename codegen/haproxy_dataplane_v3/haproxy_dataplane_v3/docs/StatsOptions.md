# StatsOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**stats_admin** | **bool** |  | [optional] 
**stats_admin_cond** | **str** |  | [optional] 
**stats_admin_cond_test** | **str** |  | [optional] 
**stats_auths** | [**List[StatsAuth]**](StatsAuth.md) |  | [optional] 
**stats_enable** | **bool** |  | [optional] 
**stats_hide_version** | **bool** |  | [optional] 
**stats_http_requests** | [**List[StatsHttpRequest]**](StatsHttpRequest.md) |  | [optional] 
**stats_maxconn** | **int** |  | [optional] 
**stats_realm** | **bool** |  | [optional] 
**stats_realm_realm** | **str** |  | [optional] 
**stats_refresh_delay** | **int** |  | [optional] 
**stats_show_desc** | **str** |  | [optional] 
**stats_show_legends** | **bool** |  | [optional] 
**stats_show_modules** | **bool** |  | [optional] 
**stats_show_node_name** | **str** |  | [optional] 
**stats_uri_prefix** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.stats_options import StatsOptions

# TODO update the JSON string below
json = "{}"
# create an instance of StatsOptions from a JSON string
stats_options_instance = StatsOptions.from_json(json)
# print the JSON string representation of the object
print(StatsOptions.to_json())

# convert the object into a dict
stats_options_dict = stats_options_instance.to_dict()
# create an instance of StatsOptions from a dict
stats_options_from_dict = StatsOptions.from_dict(stats_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


