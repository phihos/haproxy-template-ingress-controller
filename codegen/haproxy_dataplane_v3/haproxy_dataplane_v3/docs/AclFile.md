# AclFile

ACL File

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**description** | **str** |  | [optional] 
**id** | **str** |  | [optional] 
**storage_name** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.acl_file import AclFile

# TODO update the JSON string below
json = "{}"
# create an instance of AclFile from a JSON string
acl_file_instance = AclFile.from_json(json)
# print the JSON string representation of the object
print(AclFile.to_json())

# convert the object into a dict
acl_file_dict = acl_file_instance.to_dict()
# create an instance of AclFile from a dict
acl_file_from_dict = AclFile.from_dict(acl_file_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


