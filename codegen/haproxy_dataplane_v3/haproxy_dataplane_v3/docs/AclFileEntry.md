# AclFileEntry

One ACL File Entry

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | [optional] [readonly] 
**value** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.acl_file_entry import AclFileEntry

# TODO update the JSON string below
json = "{}"
# create an instance of AclFileEntry from a JSON string
acl_file_entry_instance = AclFileEntry.from_json(json)
# print the JSON string representation of the object
print(AclFileEntry.to_json())

# convert the object into a dict
acl_file_entry_dict = acl_file_entry_instance.to_dict()
# create an instance of AclFileEntry from a dict
acl_file_entry_from_dict = AclFileEntry.from_dict(acl_file_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


