# SslCertificateId

SSL Certificate ID

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**certificate_id** | [**SslCertificateIdCertificateId**](SslCertificateIdCertificateId.md) |  | [optional] 
**certificate_id_key** | **str** |  | [optional] 
**certificate_path** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_certificate_id import SslCertificateId

# TODO update the JSON string below
json = "{}"
# create an instance of SslCertificateId from a JSON string
ssl_certificate_id_instance = SslCertificateId.from_json(json)
# print the JSON string representation of the object
print(SslCertificateId.to_json())

# convert the object into a dict
ssl_certificate_id_dict = ssl_certificate_id_instance.to_dict()
# create an instance of SslCertificateId from a dict
ssl_certificate_id_from_dict = SslCertificateId.from_dict(ssl_certificate_id_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


