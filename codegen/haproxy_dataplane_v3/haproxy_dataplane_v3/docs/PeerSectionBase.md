# PeerSectionBase

HAProxy peer_section configuration

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**default_bind** | [**DefaultBind**](DefaultBind.md) |  | [optional] 
**default_server** | [**DefaultServer**](DefaultServer.md) |  | [optional] 
**disabled** | **bool** |  | [optional] 
**enabled** | **bool** |  | [optional] 
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 
**shards** | **int** | In some configurations, one would like to distribute the stick-table contents to some peers in place of sending all the stick-table contents to each peer declared in the \&quot;peers\&quot; section. In such cases, \&quot;shards\&quot; specifies the number of peer involved in this stick-table contents distribution. | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.peer_section_base import PeerSectionBase

# TODO update the JSON string below
json = "{}"
# create an instance of PeerSectionBase from a JSON string
peer_section_base_instance = PeerSectionBase.from_json(json)
# print the JSON string representation of the object
print(PeerSectionBase.to_json())

# convert the object into a dict
peer_section_base_dict = peer_section_base_instance.to_dict()
# create an instance of PeerSectionBase from a dict
peer_section_base_from_dict = PeerSectionBase.from_dict(peer_section_base_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


