# TuneBufferOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**buffers_limit** | **int** |  | [optional] 
**buffers_reserve** | **int** |  | [optional] 
**bufsize** | **int** |  | [optional] 
**bufsize_small** | **int** |  | [optional] 
**pipesize** | **int** |  | [optional] 
**rcvbuf_backend** | **int** |  | [optional] 
**rcvbuf_client** | **int** |  | [optional] 
**rcvbuf_frontend** | **int** |  | [optional] 
**rcvbuf_server** | **int** |  | [optional] 
**recv_enough** | **int** |  | [optional] 
**sndbuf_backend** | **int** |  | [optional] 
**sndbuf_client** | **int** |  | [optional] 
**sndbuf_frontend** | **int** |  | [optional] 
**sndbuf_server** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.tune_buffer_options import TuneBufferOptions

# TODO update the JSON string below
json = "{}"
# create an instance of TuneBufferOptions from a JSON string
tune_buffer_options_instance = TuneBufferOptions.from_json(json)
# print the JSON string representation of the object
print(TuneBufferOptions.to_json())

# convert the object into a dict
tune_buffer_options_dict = tune_buffer_options_instance.to_dict()
# create an instance of TuneBufferOptions from a dict
tune_buffer_options_from_dict = TuneBufferOptions.from_dict(tune_buffer_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


