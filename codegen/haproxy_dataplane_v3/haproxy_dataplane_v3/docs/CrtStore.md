# CrtStore

Storage mechanism to load and store certificates used in the configuration

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**crt_base** | **str** | Default directory to fetch SSL certificates from | [optional] 
**key_base** | **str** | Default directory to fetch SSL private keys from | [optional] 
**loads** | [**List[CrtLoad]**](CrtLoad.md) | List of certificates to load from a Certificate Store | [optional] 
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.crt_store import CrtStore

# TODO update the JSON string below
json = "{}"
# create an instance of CrtStore from a JSON string
crt_store_instance = CrtStore.from_json(json)
# print the JSON string representation of the object
print(CrtStore.to_json())

# convert the object into a dict
crt_store_dict = crt_store_instance.to_dict()
# create an instance of CrtStore from a dict
crt_store_from_dict = CrtStore.from_dict(crt_store_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


