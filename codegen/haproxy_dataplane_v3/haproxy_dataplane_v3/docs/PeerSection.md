# PeerSection

Peer Section with all it's children resources

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
**binds** | **object** |  | [optional] 
**log_target_list** | [**List[LogTarget]**](LogTarget.md) | HAProxy log target array (corresponds to log directives) | [optional] 
**peer_entries** | **object** |  | [optional] 
**servers** | **object** |  | [optional] 
**tables** | **object** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.peer_section import PeerSection

# TODO update the JSON string below
json = "{}"
# create an instance of PeerSection from a JSON string
peer_section_instance = PeerSection.from_json(json)
# print the JSON string representation of the object
print(PeerSection.to_json())

# convert the object into a dict
peer_section_dict = peer_section_instance.to_dict()
# create an instance of PeerSection from a dict
peer_section_from_dict = PeerSection.from_dict(peer_section_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


