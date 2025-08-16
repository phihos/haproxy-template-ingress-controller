# Consul

Consul server configuration

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **str** |  | 
**defaults** | **str** | Name of the defaults section to be used in backends created by this service | [optional] 
**description** | **str** |  | [optional] 
**enabled** | **bool** |  | 
**health_check_policy** | **str** | Defines the health check conditions required for each node to be considered valid for the service.   none: all nodes are considered valid   any: a node is considered valid if any one health check is &#39;passing&#39;   all: a node is considered valid if all health checks are &#39;passing&#39;   min: a node is considered valid if the number of &#39;passing&#39; checks is greater or equal to the &#39;health_check_policy_min&#39; value.     If the node has less health checks configured then &#39;health_check_policy_min&#39; it is considered invalid. | [optional] [default to 'none']
**health_check_policy_min** | **int** |  | [optional] 
**id** | **str** | Auto generated ID. | [optional] 
**mode** | **str** |  | [optional] [default to 'http']
**name** | **str** |  | [optional] 
**namespace** | **str** |  | [optional] 
**port** | **int** |  | 
**retry_timeout** | **int** | Duration in seconds in-between data pulling requests to the consul server | 
**server_slots_base** | **int** |  | [optional] 
**server_slots_growth_increment** | **int** |  | [optional] 
**server_slots_growth_type** | **str** |  | [optional] [default to 'exponential']
**service_allowlist** | **List[str]** |  | [optional] 
**service_denylist** | **List[str]** |  | [optional] 
**service_name_regexp** | **str** | Regular expression used to filter services by name. | [optional] 
**token** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.consul import Consul

# TODO update the JSON string below
json = "{}"
# create an instance of Consul from a JSON string
consul_instance = Consul.from_json(json)
# print the JSON string representation of the object
print(Consul.to_json())

# convert the object into a dict
consul_dict = consul_instance.to_dict()
# create an instance of Consul from a dict
consul_from_dict = Consul.from_dict(consul_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


