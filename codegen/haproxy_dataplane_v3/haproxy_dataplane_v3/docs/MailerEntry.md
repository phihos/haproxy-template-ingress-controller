# MailerEntry

Mailer entry of a Mailers section

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **str** |  | 
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 
**port** | **int** |  | 

## Example

```python
from haproxy_dataplane_v3.models.mailer_entry import MailerEntry

# TODO update the JSON string below
json = "{}"
# create an instance of MailerEntry from a JSON string
mailer_entry_instance = MailerEntry.from_json(json)
# print the JSON string representation of the object
print(MailerEntry.to_json())

# convert the object into a dict
mailer_entry_dict = mailer_entry_instance.to_dict()
# create an instance of MailerEntry from a dict
mailer_entry_from_dict = MailerEntry.from_dict(mailer_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


