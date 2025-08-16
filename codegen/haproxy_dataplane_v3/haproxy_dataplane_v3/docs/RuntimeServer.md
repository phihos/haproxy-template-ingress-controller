# RuntimeServer

Runtime transient server properties

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **str** |  | [optional] [readonly] 
**admin_state** | **str** |  | [optional] 
**id** | **str** |  | [optional] [readonly] 
**name** | **str** |  | [optional] [readonly] 
**operational_state** | **str** |  | [optional] 
**port** | **int** |  | [optional] [readonly] 

## Example

```python
from haproxy_dataplane_v3.models.runtime_server import RuntimeServer

# TODO update the JSON string below
json = "{}"
# create an instance of RuntimeServer from a JSON string
runtime_server_instance = RuntimeServer.from_json(json)
# print the JSON string representation of the object
print(RuntimeServer.to_json())

# convert the object into a dict
runtime_server_dict = runtime_server_instance.to_dict()
# create an instance of RuntimeServer from a dict
runtime_server_from_dict = RuntimeServer.from_dict(runtime_server_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


