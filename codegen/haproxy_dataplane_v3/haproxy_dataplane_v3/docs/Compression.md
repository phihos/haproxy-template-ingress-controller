# Compression


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**algo_req** | **str** |  | [optional] 
**algorithms** | **List[str]** |  | [optional] 
**algos_res** | **List[str]** |  | [optional] 
**direction** | **str** |  | [optional] 
**minsize_req** | **int** |  | [optional] 
**minsize_res** | **int** |  | [optional] 
**offload** | **bool** |  | [optional] 
**types** | **List[str]** |  | [optional] 
**types_req** | **List[str]** |  | [optional] 
**types_res** | **List[str]** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.compression import Compression

# TODO update the JSON string below
json = "{}"
# create an instance of Compression from a JSON string
compression_instance = Compression.from_json(json)
# print the JSON string representation of the object
print(Compression.to_json())

# convert the object into a dict
compression_dict = compression_instance.to_dict()
# create an instance of Compression from a dict
compression_from_dict = Compression.from_dict(compression_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


