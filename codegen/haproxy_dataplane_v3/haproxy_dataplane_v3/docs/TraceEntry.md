# TraceEntry

Configure a trace event

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | **object** |  | [optional] 
**trace** | **str** | Trace parameters | 

## Example

```python
from haproxy_dataplane_v3.models.trace_entry import TraceEntry

# TODO update the JSON string below
json = "{}"
# create an instance of TraceEntry from a JSON string
trace_entry_instance = TraceEntry.from_json(json)
# print the JSON string representation of the object
print(TraceEntry.to_json())

# convert the object into a dict
trace_entry_dict = trace_entry_instance.to_dict()
# create an instance of TraceEntry from a dict
trace_entry_from_dict = TraceEntry.from_dict(trace_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


