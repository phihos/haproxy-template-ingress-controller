# TuneOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**applet_zero_copy_forwarding** | **str** |  | [optional] 
**comp_maxlevel** | **int** |  | [optional] 
**disable_fast_forward** | **bool** |  | [optional] 
**disable_zero_copy_forwarding** | **bool** |  | [optional] 
**epoll_mask_events** | **List[str]** |  | [optional] 
**events_max_events_at_once** | **int** |  | [optional] 
**fail_alloc** | **bool** |  | [optional] 
**fd_edge_triggered** | **str** |  | [optional] 
**glitches_kill_cpu_usage** | **int** |  | [optional] 
**h1_zero_copy_fwd_recv** | **str** |  | [optional] 
**h1_zero_copy_fwd_send** | **str** |  | [optional] 
**h2_be_glitches_threshold** | **int** |  | [optional] 
**h2_be_initial_window_size** | **int** |  | [optional] 
**h2_be_max_concurrent_streams** | **int** |  | [optional] 
**h2_be_rxbuf** | **int** |  | [optional] 
**h2_fe_glitches_threshold** | **int** |  | [optional] 
**h2_fe_initial_window_size** | **int** |  | [optional] 
**h2_fe_max_concurrent_streams** | **int** |  | [optional] 
**h2_fe_max_total_streams** | **int** |  | [optional] 
**h2_fe_rxbuf** | **int** |  | [optional] 
**h2_header_table_size** | **int** |  | [optional] 
**h2_initial_window_size** | **int** |  | [optional] 
**h2_max_concurrent_streams** | **int** |  | [optional] 
**h2_max_frame_size** | **int** |  | [optional] 
**h2_zero_copy_fwd_send** | **str** |  | [optional] 
**http_cookielen** | **int** |  | [optional] 
**http_logurilen** | **int** |  | [optional] 
**http_maxhdr** | **int** |  | [optional] 
**idle_pool_shared** | **str** |  | [optional] 
**idletimer** | **int** |  | [optional] 
**listener_default_shards** | **str** |  | [optional] 
**listener_multi_queue** | **str** |  | [optional] 
**max_checks_per_thread** | **int** |  | [optional] 
**max_rules_at_once** | **int** |  | [optional] 
**maxaccept** | **int** |  | [optional] 
**maxpollevents** | **int** |  | [optional] 
**maxrewrite** | **int** |  | [optional] 
**memory_hot_size** | **int** |  | [optional] 
**notsent_lowat_client** | **int** |  | [optional] 
**notsent_lowat_server** | **int** |  | [optional] 
**pattern_cache_size** | **int** |  | [optional] 
**peers_max_updates_at_once** | **int** |  | [optional] 
**pool_high_fd_ratio** | **int** |  | [optional] 
**pool_low_fd_ratio** | **int** |  | [optional] 
**pt_zero_copy_forwarding** | **str** |  | [optional] 
**renice_runtime** | **int** |  | [optional] 
**renice_startup** | **int** |  | [optional] 
**ring_queues** | **int** |  | [optional] 
**runqueue_depth** | **int** |  | [optional] 
**sched_low_latency** | **str** |  | [optional] 
**stick_counters** | **int** |  | [optional] 
**takeover_other_tg_connections** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.tune_options import TuneOptions

# TODO update the JSON string below
json = "{}"
# create an instance of TuneOptions from a JSON string
tune_options_instance = TuneOptions.from_json(json)
# print the JSON string representation of the object
print(TuneOptions.to_json())

# convert the object into a dict
tune_options_dict = tune_options_instance.to_dict()
# create an instance of TuneOptions from a dict
tune_options_from_dict = TuneOptions.from_dict(tune_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


