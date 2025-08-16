# TuneQuicOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**frontend_conn_tx_buffers_limit** | **int** |  | [optional] 
**frontend_max_idle_timeout** | **int** |  | [optional] 
**frontend_max_streams_bidi** | **int** |  | [optional] 
**frontend_max_tx_memory** | **int** |  | [optional] 
**max_frame_loss** | **int** |  | [optional] 
**reorder_ratio** | **int** |  | [optional] 
**retry_threshold** | **int** |  | [optional] 
**socket_owner** | **str** |  | [optional] 
**zero_copy_fwd_send** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.tune_quic_options import TuneQuicOptions

# TODO update the JSON string below
json = "{}"
# create an instance of TuneQuicOptions from a JSON string
tune_quic_options_instance = TuneQuicOptions.from_json(json)
# print the JSON string representation of the object
print(TuneQuicOptions.to_json())

# convert the object into a dict
tune_quic_options_dict = tune_quic_options_instance.to_dict()
# create an instance of TuneQuicOptions from a dict
tune_quic_options_from_dict = TuneQuicOptions.from_dict(tune_quic_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


