# SpoeMessageEvent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cond** | **str** |  | [optional] 
**cond_test** | **str** |  | [optional] 
**name** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.spoe_message_event import SpoeMessageEvent

# TODO update the JSON string below
json = "{}"
# create an instance of SpoeMessageEvent from a JSON string
spoe_message_event_instance = SpoeMessageEvent.from_json(json)
# print the JSON string representation of the object
print(SpoeMessageEvent.to_json())

# convert the object into a dict
spoe_message_event_dict = spoe_message_event_instance.to_dict()
# create an instance of SpoeMessageEvent from a dict
spoe_message_event_from_dict = SpoeMessageEvent.from_dict(spoe_message_event_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


