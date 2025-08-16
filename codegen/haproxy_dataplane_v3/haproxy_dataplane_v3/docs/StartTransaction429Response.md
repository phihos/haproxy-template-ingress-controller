# StartTransaction429Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **int** |  | [optional] 
**message** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.start_transaction429_response import StartTransaction429Response

# TODO update the JSON string below
json = "{}"
# create an instance of StartTransaction429Response from a JSON string
start_transaction429_response_instance = StartTransaction429Response.from_json(json)
# print the JSON string representation of the object
print(StartTransaction429Response.to_json())

# convert the object into a dict
start_transaction429_response_dict = start_transaction429_response_instance.to_dict()
# create an instance of StartTransaction429Response from a dict
start_transaction429_response_from_dict = StartTransaction429Response.from_dict(start_transaction429_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


