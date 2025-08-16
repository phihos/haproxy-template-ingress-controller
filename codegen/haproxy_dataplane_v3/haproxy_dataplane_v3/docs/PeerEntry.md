# PeerEntry

Peer Entry from peers table

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **str** |  | 
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 
**port** | **int** |  | 
**shard** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.peer_entry import PeerEntry

# TODO update the JSON string below
json = "{}"
# create an instance of PeerEntry from a JSON string
peer_entry_instance = PeerEntry.from_json(json)
# print the JSON string representation of the object
print(PeerEntry.to_json())

# convert the object into a dict
peer_entry_dict = peer_entry_instance.to_dict()
# create an instance of PeerEntry from a dict
peer_entry_from_dict = PeerEntry.from_dict(peer_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


