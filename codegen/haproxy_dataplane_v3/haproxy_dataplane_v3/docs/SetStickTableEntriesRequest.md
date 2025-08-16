# SetStickTableEntriesRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**data_type** | [**StickTableEntry**](StickTableEntry.md) |  | 
**key** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.set_stick_table_entries_request import SetStickTableEntriesRequest

# TODO update the JSON string below
json = "{}"
# create an instance of SetStickTableEntriesRequest from a JSON string
set_stick_table_entries_request_instance = SetStickTableEntriesRequest.from_json(json)
# print the JSON string representation of the object
print(SetStickTableEntriesRequest.to_json())

# convert the object into a dict
set_stick_table_entries_request_dict = set_stick_table_entries_request_instance.to_dict()
# create an instance of SetStickTableEntriesRequest from a dict
set_stick_table_entries_request_from_dict = SetStickTableEntriesRequest.from_dict(set_stick_table_entries_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


