# OcspUpdateOptionsHttpproxy


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **str** |  | [optional] 
**port** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ocsp_update_options_httpproxy import OcspUpdateOptionsHttpproxy

# TODO update the JSON string below
json = "{}"
# create an instance of OcspUpdateOptionsHttpproxy from a JSON string
ocsp_update_options_httpproxy_instance = OcspUpdateOptionsHttpproxy.from_json(json)
# print the JSON string representation of the object
print(OcspUpdateOptionsHttpproxy.to_json())

# convert the object into a dict
ocsp_update_options_httpproxy_dict = ocsp_update_options_httpproxy_instance.to_dict()
# create an instance of OcspUpdateOptionsHttpproxy from a dict
ocsp_update_options_httpproxy_from_dict = OcspUpdateOptionsHttpproxy.from_dict(ocsp_update_options_httpproxy_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


