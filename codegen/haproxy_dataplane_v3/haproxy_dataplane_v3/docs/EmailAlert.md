# EmailAlert

Send emails for important log messages.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_from** | **str** |  | 
**level** | **str** |  | [optional] 
**mailers** | **str** |  | 
**metadata** | **object** |  | [optional] 
**myhostname** | **str** |  | [optional] 
**to** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.email_alert import EmailAlert

# TODO update the JSON string below
json = "{}"
# create an instance of EmailAlert from a JSON string
email_alert_instance = EmailAlert.from_json(json)
# print the JSON string representation of the object
print(EmailAlert.to_json())

# convert the object into a dict
email_alert_dict = email_alert_instance.to_dict()
# create an instance of EmailAlert from a dict
email_alert_from_dict = EmailAlert.from_dict(email_alert_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


