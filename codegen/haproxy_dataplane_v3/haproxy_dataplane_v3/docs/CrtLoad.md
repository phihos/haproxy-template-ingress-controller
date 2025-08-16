# CrtLoad

Loads a certificate from a store with options

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**acme** | **str** | ACME section name to use | [optional] 
**alias** | **str** | Certificate alias | [optional] 
**certificate** | **str** | Certificate filename | 
**domains** | **List[str]** | List of domains used to generate the certificate with ACME | [optional] 
**issuer** | **str** | OCSP issuer filename | [optional] 
**key** | **str** | Private key filename | [optional] 
**metadata** | **object** |  | [optional] 
**ocsp** | **str** | OCSP response filename | [optional] 
**ocsp_update** | **str** | Automatic OCSP response update | [optional] 
**sctl** | **str** | Signed Certificate Timestamp List filename | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.crt_load import CrtLoad

# TODO update the JSON string below
json = "{}"
# create an instance of CrtLoad from a JSON string
crt_load_instance = CrtLoad.from_json(json)
# print the JSON string representation of the object
print(CrtLoad.to_json())

# convert the object into a dict
crt_load_dict = crt_load_instance.to_dict()
# create an instance of CrtLoad from a dict
crt_load_from_dict = CrtLoad.from_dict(crt_load_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


