# SslOcspUpdate

SSL OCSP Update

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cert_id** | **str** |  | [optional] 
**failures** | **int** |  | [optional] 
**last_update** | **str** |  | [optional] 
**last_update_status** | **int** |  | [optional] 
**last_update_status_str** | **str** |  | [optional] 
**next_update** | **str** |  | [optional] 
**path** | **str** |  | [optional] 
**successes** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_ocsp_update import SslOcspUpdate

# TODO update the JSON string below
json = "{}"
# create an instance of SslOcspUpdate from a JSON string
ssl_ocsp_update_instance = SslOcspUpdate.from_json(json)
# print the JSON string representation of the object
print(SslOcspUpdate.to_json())

# convert the object into a dict
ssl_ocsp_update_dict = ssl_ocsp_update_instance.to_dict()
# create an instance of SslOcspUpdate from a dict
ssl_ocsp_update_from_dict = SslOcspUpdate.from_dict(ssl_ocsp_update_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


