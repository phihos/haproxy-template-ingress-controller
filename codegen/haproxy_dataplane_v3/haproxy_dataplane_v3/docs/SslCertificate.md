# SslCertificate

A file containing one or more SSL/TLS certificates and keys

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**algorithm** | **str** |  | [optional] 
**authority_key_id** | **str** |  | [optional] 
**chain_issuer** | **str** |  | [optional] 
**chain_subject** | **str** |  | [optional] 
**description** | **str** |  | [optional] 
**domains** | **str** |  | [optional] [readonly] 
**file** | **str** |  | [optional] 
**ip_addresses** | **str** |  | [optional] [readonly] 
**issuers** | **str** |  | [optional] [readonly] 
**not_after** | **datetime** |  | [optional] [readonly] 
**not_before** | **datetime** |  | [optional] [readonly] 
**serial** | **str** |  | [optional] 
**sha1_finger_print** | **str** |  | [optional] 
**sha256_finger_print** | **str** |  | [optional] 
**size** | **int** | File size in bytes. | [optional] [readonly] 
**status** | **str** | Only set when using the runtime API. | [optional] [readonly] 
**storage_name** | **str** |  | [optional] 
**subject** | **str** |  | [optional] 
**subject_alternative_names** | **str** |  | [optional] 
**subject_key_id** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_certificate import SslCertificate

# TODO update the JSON string below
json = "{}"
# create an instance of SslCertificate from a JSON string
ssl_certificate_instance = SslCertificate.from_json(json)
# print the JSON string representation of the object
print(SslCertificate.to_json())

# convert the object into a dict
ssl_certificate_dict = ssl_certificate_instance.to_dict()
# create an instance of SslCertificate from a dict
ssl_certificate_from_dict = SslCertificate.from_dict(ssl_certificate_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


