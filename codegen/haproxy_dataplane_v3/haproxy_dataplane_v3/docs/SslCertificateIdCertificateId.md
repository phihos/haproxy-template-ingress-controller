# SslCertificateIdCertificateId


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**hash_algorithm** | **str** |  | [optional] 
**issuer_key_hash** | **str** |  | [optional] 
**issuer_name_hash** | **str** |  | [optional] 
**serial_number** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_certificate_id_certificate_id import SslCertificateIdCertificateId

# TODO update the JSON string below
json = "{}"
# create an instance of SslCertificateIdCertificateId from a JSON string
ssl_certificate_id_certificate_id_instance = SslCertificateIdCertificateId.from_json(json)
# print the JSON string representation of the object
print(SslCertificateIdCertificateId.to_json())

# convert the object into a dict
ssl_certificate_id_certificate_id_dict = ssl_certificate_id_certificate_id_instance.to_dict()
# create an instance of SslCertificateIdCertificateId from a dict
ssl_certificate_id_certificate_id_from_dict = SslCertificateIdCertificateId.from_dict(ssl_certificate_id_certificate_id_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


