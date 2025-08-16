# MailersSectionBase

A list of SMTP servers used by HAProxy to send emails.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 
**timeout** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.mailers_section_base import MailersSectionBase

# TODO update the JSON string below
json = "{}"
# create an instance of MailersSectionBase from a JSON string
mailers_section_base_instance = MailersSectionBase.from_json(json)
# print the JSON string representation of the object
print(MailersSectionBase.to_json())

# convert the object into a dict
mailers_section_base_dict = mailers_section_base_instance.to_dict()
# create an instance of MailersSectionBase from a dict
mailers_section_base_from_dict = MailersSectionBase.from_dict(mailers_section_base_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


