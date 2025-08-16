# SpoeAgent

SPOE agent configuration

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_async** | **str** |  | [optional] 
**continue_on_error** | **str** |  | [optional] 
**dontlog_normal** | **str** |  | [optional] 
**engine_name** | **str** |  | [optional] 
**force_set_var** | **str** |  | [optional] 
**groups** | **str** |  | [optional] 
**hello_timeout** | **int** |  | [optional] 
**idle_timeout** | **int** |  | [optional] 
**log** | [**List[LogTarget]**](LogTarget.md) | HAProxy log target array (corresponds to log directives) | [optional] 
**max_frame_size** | **int** |  | [optional] 
**max_waiting_frames** | **int** |  | [optional] 
**maxconnrate** | **int** |  | [optional] 
**maxerrrate** | **int** |  | [optional] 
**messages** | **str** |  | [optional] 
**name** | **str** |  | 
**option_set_on_error** | **str** |  | [optional] 
**option_set_process_time** | **str** |  | [optional] 
**option_set_total_time** | **str** |  | [optional] 
**option_var_prefix** | **str** |  | [optional] 
**pipelining** | **str** |  | [optional] 
**processing_timeout** | **int** |  | [optional] 
**register_var_names** | **str** |  | [optional] 
**send_frag_payload** | **str** |  | [optional] 
**use_backend** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.spoe_agent import SpoeAgent

# TODO update the JSON string below
json = "{}"
# create an instance of SpoeAgent from a JSON string
spoe_agent_instance = SpoeAgent.from_json(json)
# print the JSON string representation of the object
print(SpoeAgent.to_json())

# convert the object into a dict
spoe_agent_dict = spoe_agent_instance.to_dict()
# create an instance of SpoeAgent from a dict
spoe_agent_from_dict = SpoeAgent.from_dict(spoe_agent_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


