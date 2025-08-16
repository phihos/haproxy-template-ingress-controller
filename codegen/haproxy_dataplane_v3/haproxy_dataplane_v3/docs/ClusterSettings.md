# ClusterSettings

Settings related to a cluster.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**bootstrap_key** | **str** |  | [optional] 
**cluster** | [**ClusterControllerInformation**](ClusterControllerInformation.md) |  | [optional] 
**mode** | **str** |  | [optional] 
**status** | **str** |  | [optional] [readonly] 

## Example

```python
from haproxy_dataplane_v3.models.cluster_settings import ClusterSettings

# TODO update the JSON string below
json = "{}"
# create an instance of ClusterSettings from a JSON string
cluster_settings_instance = ClusterSettings.from_json(json)
# print the JSON string representation of the object
print(ClusterSettings.to_json())

# convert the object into a dict
cluster_settings_dict = cluster_settings_instance.to_dict()
# create an instance of ClusterSettings from a dict
cluster_settings_from_dict = ClusterSettings.from_dict(cluster_settings_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


