# BackendSwitchingRule

HAProxy backend switching rule configuration (corresponds to use_backend directive)

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cond** | **str** |  | [optional] 
**cond_test** | **str** |  | [optional] 
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.backend_switching_rule import BackendSwitchingRule

# TODO update the JSON string below
json = "{}"
# create an instance of BackendSwitchingRule from a JSON string
backend_switching_rule_instance = BackendSwitchingRule.from_json(json)
# print the JSON string representation of the object
print(BackendSwitchingRule.to_json())

# convert the object into a dict
backend_switching_rule_dict = backend_switching_rule_instance.to_dict()
# create an instance of BackendSwitchingRule from a dict
backend_switching_rule_from_dict = BackendSwitchingRule.from_dict(backend_switching_rule_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


