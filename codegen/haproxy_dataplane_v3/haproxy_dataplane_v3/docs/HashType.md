# HashType


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function** | **str** |  | [optional] 
**method** | **str** |  | [optional] 
**modifier** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.hash_type import HashType

# TODO update the JSON string below
json = "{}"
# create an instance of HashType from a JSON string
hash_type_instance = HashType.from_json(json)
# print the JSON string representation of the object
print(HashType.to_json())

# convert the object into a dict
hash_type_dict = hash_type_instance.to_dict()
# create an instance of HashType from a dict
hash_type_from_dict = HashType.from_dict(hash_type_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


