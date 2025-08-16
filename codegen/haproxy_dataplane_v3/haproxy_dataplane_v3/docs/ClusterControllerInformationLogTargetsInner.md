# ClusterControllerInformationLogTargetsInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **str** |  | 
**log_format** | **str** |  | [optional] 
**port** | **int** |  | 
**protocol** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.cluster_controller_information_log_targets_inner import ClusterControllerInformationLogTargetsInner

# TODO update the JSON string below
json = "{}"
# create an instance of ClusterControllerInformationLogTargetsInner from a JSON string
cluster_controller_information_log_targets_inner_instance = ClusterControllerInformationLogTargetsInner.from_json(json)
# print the JSON string representation of the object
print(ClusterControllerInformationLogTargetsInner.to_json())

# convert the object into a dict
cluster_controller_information_log_targets_inner_dict = cluster_controller_information_log_targets_inner_instance.to_dict()
# create an instance of ClusterControllerInformationLogTargetsInner from a dict
cluster_controller_information_log_targets_inner_from_dict = ClusterControllerInformationLogTargetsInner.from_dict(cluster_controller_information_log_targets_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


