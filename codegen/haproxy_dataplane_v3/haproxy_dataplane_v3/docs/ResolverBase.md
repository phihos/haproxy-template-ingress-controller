# ResolverBase

Runtime DNS configuration

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**accepted_payload_size** | **int** |  | [optional] 
**hold_nx** | **int** |  | [optional] 
**hold_obsolete** | **int** |  | [optional] 
**hold_other** | **int** |  | [optional] 
**hold_refused** | **int** |  | [optional] 
**hold_timeout** | **int** |  | [optional] 
**hold_valid** | **int** |  | [optional] 
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 
**parse_resolv_conf** | **bool** |  | [optional] 
**resolve_retries** | **int** |  | [optional] 
**timeout_resolve** | **int** |  | [optional] 
**timeout_retry** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.resolver_base import ResolverBase

# TODO update the JSON string below
json = "{}"
# create an instance of ResolverBase from a JSON string
resolver_base_instance = ResolverBase.from_json(json)
# print the JSON string representation of the object
print(ResolverBase.to_json())

# convert the object into a dict
resolver_base_dict = resolver_base_instance.to_dict()
# create an instance of ResolverBase from a dict
resolver_base_from_dict = ResolverBase.from_dict(resolver_base_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


