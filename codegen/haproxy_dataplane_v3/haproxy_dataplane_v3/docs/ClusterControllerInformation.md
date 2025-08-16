# ClusterControllerInformation


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **str** |  | [optional] [readonly] 
**api_base_path** | **str** |  | [optional] [readonly] 
**cluster_id** | **str** |  | [optional] 
**description** | **str** |  | [optional] [readonly] 
**log_targets** | [**List[ClusterControllerInformationLogTargetsInner]**](ClusterControllerInformationLogTargetsInner.md) |  | [optional] 
**name** | **str** |  | [optional] [readonly] 
**port** | **int** |  | [optional] [readonly] 

## Example

```python
from haproxy_dataplane_v3.models.cluster_controller_information import ClusterControllerInformation

# TODO update the JSON string below
json = "{}"
# create an instance of ClusterControllerInformation from a JSON string
cluster_controller_information_instance = ClusterControllerInformation.from_json(json)
# print the JSON string representation of the object
print(ClusterControllerInformation.to_json())

# convert the object into a dict
cluster_controller_information_dict = cluster_controller_information_instance.to_dict()
# create an instance of ClusterControllerInformation from a dict
cluster_controller_information_from_dict = ClusterControllerInformation.from_dict(cluster_controller_information_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


