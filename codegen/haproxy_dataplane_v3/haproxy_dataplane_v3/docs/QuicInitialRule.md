# QuicInitialRule

QUIC Initial configuration

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cond** | **str** |  | [optional] 
**cond_test** | **str** |  | [optional] 
**metadata** | **object** |  | [optional] 
**type** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.quic_initial_rule import QuicInitialRule

# TODO update the JSON string below
json = "{}"
# create an instance of QuicInitialRule from a JSON string
quic_initial_rule_instance = QuicInitialRule.from_json(json)
# print the JSON string representation of the object
print(QuicInitialRule.to_json())

# convert the object into a dict
quic_initial_rule_dict = quic_initial_rule_instance.to_dict()
# create an instance of QuicInitialRule from a dict
quic_initial_rule_from_dict = QuicInitialRule.from_dict(quic_initial_rule_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


