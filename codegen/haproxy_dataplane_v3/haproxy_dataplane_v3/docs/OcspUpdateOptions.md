# OcspUpdateOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**disable** | **bool** |  | [optional] [default to False]
**httpproxy** | [**OcspUpdateOptionsHttpproxy**](OcspUpdateOptionsHttpproxy.md) |  | [optional] 
**maxdelay** | **int** | Sets the maximum interval between two automatic updates of the same OCSP response.This time is expressed in seconds | [optional] 
**mindelay** | **int** | Sets the minimum interval between two automatic updates of the same OCSP response. This time is expressed in seconds | [optional] 
**mode** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ocsp_update_options import OcspUpdateOptions

# TODO update the JSON string below
json = "{}"
# create an instance of OcspUpdateOptions from a JSON string
ocsp_update_options_instance = OcspUpdateOptions.from_json(json)
# print the JSON string representation of the object
print(OcspUpdateOptions.to_json())

# convert the object into a dict
ocsp_update_options_dict = ocsp_update_options_instance.to_dict()
# create an instance of OcspUpdateOptions from a dict
ocsp_update_options_from_dict = OcspUpdateOptions.from_dict(ocsp_update_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


