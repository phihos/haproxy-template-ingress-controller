# BackendBaseIgnorePersist

This field is deprecated in favor of ignore_persist_list, and will be removed in a future release

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cond** | **str** |  | 
**cond_test** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.backend_base_ignore_persist import BackendBaseIgnorePersist

# TODO update the JSON string below
json = "{}"
# create an instance of BackendBaseIgnorePersist from a JSON string
backend_base_ignore_persist_instance = BackendBaseIgnorePersist.from_json(json)
# print the JSON string representation of the object
print(BackendBaseIgnorePersist.to_json())

# convert the object into a dict
backend_base_ignore_persist_dict = backend_base_ignore_persist_instance.to_dict()
# create an instance of BackendBaseIgnorePersist from a dict
backend_base_ignore_persist_from_dict = BackendBaseIgnorePersist.from_dict(backend_base_ignore_persist_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


