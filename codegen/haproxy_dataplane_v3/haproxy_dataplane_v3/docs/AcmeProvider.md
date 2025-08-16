# AcmeProvider

Define an ACME provider to generate certificates automatically

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**account_key** | **str** | Path where the the ACME account key is stored | [optional] 
**bits** | **int** | Number of bits to generate an RSA certificate | [optional] 
**challenge** | **str** | ACME challenge type. Only HTTP-01 and DNS-01 are supported. | [optional] 
**contact** | **str** | Contact email for the ACME account | [optional] 
**curves** | **str** | Curves used with the ECDSA key type | [optional] 
**directory** | **str** | URL to the ACME provider&#39;s directory. For example: https://acme-staging-v02.api.letsencrypt.org/directory  | 
**keytype** | **str** | Type of key to generate | [optional] 
**map** | **str** | The map which will be used to store the ACME token (key) and thumbprint | [optional] 
**metadata** | **object** |  | [optional] 
**name** | **str** | ACME provider&#39;s name | 

## Example

```python
from haproxy_dataplane_v3.models.acme_provider import AcmeProvider

# TODO update the JSON string below
json = "{}"
# create an instance of AcmeProvider from a JSON string
acme_provider_instance = AcmeProvider.from_json(json)
# print the JSON string representation of the object
print(AcmeProvider.to_json())

# convert the object into a dict
acme_provider_dict = acme_provider_instance.to_dict()
# create an instance of AcmeProvider from a dict
acme_provider_from_dict = AcmeProvider.from_dict(acme_provider_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


