# SpoeMessage

SPOE message section configuration

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**acl** | [**List[Acl]**](Acl.md) | HAProxy ACL lines array (corresponds to acl directives) | [optional] 
**args** | **str** |  | [optional] 
**event** | [**SpoeMessageEvent**](SpoeMessageEvent.md) |  | [optional] 
**name** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.spoe_message import SpoeMessage

# TODO update the JSON string below
json = "{}"
# create an instance of SpoeMessage from a JSON string
spoe_message_instance = SpoeMessage.from_json(json)
# print the JSON string representation of the object
print(SpoeMessage.to_json())

# convert the object into a dict
spoe_message_dict = spoe_message_instance.to_dict()
# create an instance of SpoeMessage from a dict
spoe_message_from_dict = SpoeMessage.from_dict(spoe_message_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


