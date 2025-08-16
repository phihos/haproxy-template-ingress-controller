# AcmeCertificateStatus

Status of a single ACME certificate from runtime.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**acme_section** | **str** | ACME section which generated the certificate. | [optional] 
**certificate** | **str** | Certificate name | [optional] 
**expiries_in** | **str** | Duration until certificate expiry. | [optional] 
**expiry_date** | **datetime** | Certificate expiration date. | [optional] 
**renewal_in** | **str** | Duration until the next planned renewal. | [optional] 
**scheduled_renewal** | **datetime** | Planned date for certificate renewal. | [optional] 
**state** | **str** | State of the ACME task, either \&quot;Running\&quot; or \&quot;Scheduled\&quot;. | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.acme_certificate_status import AcmeCertificateStatus

# TODO update the JSON string below
json = "{}"
# create an instance of AcmeCertificateStatus from a JSON string
acme_certificate_status_instance = AcmeCertificateStatus.from_json(json)
# print the JSON string representation of the object
print(AcmeCertificateStatus.to_json())

# convert the object into a dict
acme_certificate_status_dict = acme_certificate_status_instance.to_dict()
# create an instance of AcmeCertificateStatus from a dict
acme_certificate_status_from_dict = AcmeCertificateStatus.from_dict(acme_certificate_status_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


