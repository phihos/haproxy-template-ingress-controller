# SslFrontUse

Assign a certificate to the current frontend

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**allow_0rtt** | **bool** |  | [optional] 
**alpn** | **str** |  | [optional] 
**ca_file** | **str** |  | [optional] 
**certificate** | **str** | Certificate filename | 
**ciphers** | **str** |  | [optional] 
**ciphersuites** | **str** |  | [optional] 
**client_sigalgs** | **str** |  | [optional] 
**crl_file** | **str** |  | [optional] 
**curves** | **str** |  | [optional] 
**ecdhe** | **str** |  | [optional] 
**issuer** | **str** | OCSP issuer filename | [optional] 
**key** | **str** | Private key filename | [optional] 
**metadata** | **object** |  | [optional] 
**no_alpn** | **bool** |  | [optional] 
**no_ca_names** | **bool** |  | [optional] 
**npn** | **str** |  | [optional] 
**ocsp** | **str** | OCSP response filename | [optional] 
**ocsp_update** | **str** | Automatic OCSP response update | [optional] 
**sctl** | **str** | Signed Certificate Timestamp List filename | [optional] 
**sigalgs** | **str** |  | [optional] 
**ssl_max_ver** | **str** |  | [optional] 
**ssl_min_ver** | **str** |  | [optional] 
**verify** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_front_use import SslFrontUse

# TODO update the JSON string below
json = "{}"
# create an instance of SslFrontUse from a JSON string
ssl_front_use_instance = SslFrontUse.from_json(json)
# print the JSON string representation of the object
print(SslFrontUse.to_json())

# convert the object into a dict
ssl_front_use_dict = ssl_front_use_instance.to_dict()
# create an instance of SslFrontUse from a dict
ssl_front_use_from_dict = SslFrontUse.from_dict(ssl_front_use_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


