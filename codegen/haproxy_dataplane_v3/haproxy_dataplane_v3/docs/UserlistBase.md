# UserlistBase

HAProxy configuration of access control

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.userlist_base import UserlistBase

# TODO update the JSON string below
json = "{}"
# create an instance of UserlistBase from a JSON string
userlist_base_instance = UserlistBase.from_json(json)
# print the JSON string representation of the object
print(UserlistBase.to_json())

# convert the object into a dict
userlist_base_dict = userlist_base_instance.to_dict()
# create an instance of UserlistBase from a dict
userlist_base_from_dict = UserlistBase.from_dict(userlist_base_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


