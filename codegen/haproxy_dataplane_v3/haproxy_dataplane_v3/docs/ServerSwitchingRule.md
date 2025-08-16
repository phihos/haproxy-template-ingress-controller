# ServerSwitchingRule

HAProxy server switching rule configuration (corresponds to use-server directive)

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cond** | **str** |  | [optional] 
**cond_test** | **str** |  | [optional] 
**metadata** | **object** |  | [optional] 
**target_server** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.server_switching_rule import ServerSwitchingRule

# TODO update the JSON string below
json = "{}"
# create an instance of ServerSwitchingRule from a JSON string
server_switching_rule_instance = ServerSwitchingRule.from_json(json)
# print the JSON string representation of the object
print(ServerSwitchingRule.to_json())

# convert the object into a dict
server_switching_rule_dict = server_switching_rule_instance.to_dict()
# create an instance of ServerSwitchingRule from a dict
server_switching_rule_from_dict = ServerSwitchingRule.from_dict(server_switching_rule_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


