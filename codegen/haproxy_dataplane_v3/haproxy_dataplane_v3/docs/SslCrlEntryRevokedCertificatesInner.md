# SslCrlEntryRevokedCertificatesInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**revocation_date** | **date** |  | [optional] 
**serial_number** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_crl_entry_revoked_certificates_inner import SslCrlEntryRevokedCertificatesInner

# TODO update the JSON string below
json = "{}"
# create an instance of SslCrlEntryRevokedCertificatesInner from a JSON string
ssl_crl_entry_revoked_certificates_inner_instance = SslCrlEntryRevokedCertificatesInner.from_json(json)
# print the JSON string representation of the object
print(SslCrlEntryRevokedCertificatesInner.to_json())

# convert the object into a dict
ssl_crl_entry_revoked_certificates_inner_dict = ssl_crl_entry_revoked_certificates_inner_instance.to_dict()
# create an instance of SslCrlEntryRevokedCertificatesInner from a dict
ssl_crl_entry_revoked_certificates_inner_from_dict = SslCrlEntryRevokedCertificatesInner.from_dict(ssl_crl_entry_revoked_certificates_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


