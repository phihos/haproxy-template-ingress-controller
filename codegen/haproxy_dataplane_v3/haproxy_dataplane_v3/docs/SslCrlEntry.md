# SslCrlEntry

A certificate revocation list entry.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**issuer** | **str** |  | [optional] 
**last_update** | **date** |  | [optional] 
**next_update** | **date** |  | [optional] 
**revoked_certificates** | [**List[SslCrlEntryRevokedCertificatesInner]**](SslCrlEntryRevokedCertificatesInner.md) |  | [optional] 
**signature_algorithm** | **str** |  | [optional] 
**status** | **str** |  | [optional] 
**storage_name** | **str** |  | [optional] 
**version** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_crl_entry import SslCrlEntry

# TODO update the JSON string below
json = "{}"
# create an instance of SslCrlEntry from a JSON string
ssl_crl_entry_instance = SslCrlEntry.from_json(json)
# print the JSON string representation of the object
print(SslCrlEntry.to_json())

# convert the object into a dict
ssl_crl_entry_dict = ssl_crl_entry_instance.to_dict()
# create an instance of SslCrlEntry from a dict
ssl_crl_entry_from_dict = SslCrlEntry.from_dict(ssl_crl_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


