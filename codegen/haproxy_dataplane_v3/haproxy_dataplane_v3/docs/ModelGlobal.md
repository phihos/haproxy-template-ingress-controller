# ModelGlobal

Frontend with all it's children resources

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**chroot** | **str** |  | [optional] 
**close_spread_time** | **int** |  | [optional] 
**cluster_secret** | **str** |  | [optional] 
**cpu_maps** | [**List[GlobalBaseCpuMapsInner]**](GlobalBaseCpuMapsInner.md) |  | [optional] 
**cpu_policy** | **str** |  | [optional] 
**cpu_set** | [**List[GlobalBaseCpuSetInner]**](GlobalBaseCpuSetInner.md) |  | [optional] 
**daemon** | **bool** |  | [optional] 
**debug_options** | [**DebugOptions**](DebugOptions.md) |  | [optional] 
**default_path** | [**GlobalBaseDefaultPath**](GlobalBaseDefaultPath.md) |  | [optional] 
**description** | **str** |  | [optional] 
**device_atlas_options** | [**DeviceAtlasOptions**](DeviceAtlasOptions.md) |  | [optional] 
**dns_accept_family** | **str** |  | [optional] 
**environment_options** | [**EnvironmentOptions**](EnvironmentOptions.md) |  | [optional] 
**expose_deprecated_directives** | **bool** |  | [optional] 
**expose_experimental_directives** | **bool** |  | [optional] 
**external_check** | **bool** |  | [optional] 
**fifty_one_degrees_options** | [**FiftyOneDegreesOptions**](FiftyOneDegreesOptions.md) |  | [optional] 
**force_cfg_parser_pause** | **int** |  | [optional] 
**gid** | **int** |  | [optional] 
**grace** | **int** |  | [optional] 
**group** | **str** |  | [optional] 
**h1_accept_payload_with_any_method** | **bool** |  | [optional] 
**h1_case_adjust** | [**List[GlobalBaseH1CaseAdjustInner]**](GlobalBaseH1CaseAdjustInner.md) |  | [optional] 
**h1_case_adjust_file** | **str** |  | [optional] 
**h1_do_not_close_on_insecure_transfer_encoding** | **bool** |  | [optional] 
**h2_workaround_bogus_websocket_clients** | **bool** |  | [optional] 
**hard_stop_after** | **int** |  | [optional] 
**harden** | [**GlobalBaseHarden**](GlobalBaseHarden.md) |  | [optional] 
**http_client_options** | [**HttpClientOptions**](HttpClientOptions.md) |  | [optional] 
**http_err_codes** | [**List[HttpCodes]**](HttpCodes.md) |  | [optional] 
**http_fail_codes** | [**List[HttpCodes]**](HttpCodes.md) |  | [optional] 
**insecure_fork_wanted** | **bool** |  | [optional] 
**insecure_setuid_wanted** | **bool** |  | [optional] 
**limited_quic** | **bool** |  | [optional] 
**localpeer** | **str** |  | [optional] 
**log_send_hostname** | [**GlobalBaseLogSendHostname**](GlobalBaseLogSendHostname.md) |  | [optional] 
**lua_options** | [**LuaOptions**](LuaOptions.md) |  | [optional] 
**master_worker** | **bool** |  | [optional] 
**metadata** | **object** |  | [optional] 
**mworker_max_reloads** | **int** |  | [optional] 
**nbthread** | **int** |  | [optional] 
**no_quic** | **bool** |  | [optional] 
**node** | **str** |  | [optional] 
**numa_cpu_mapping** | **str** |  | [optional] 
**ocsp_update_options** | [**OcspUpdateOptions**](OcspUpdateOptions.md) |  | [optional] 
**performance_options** | [**PerformanceOptions**](PerformanceOptions.md) |  | [optional] 
**pidfile** | **str** |  | [optional] 
**pp2_never_send_local** | **bool** |  | [optional] 
**prealloc_fd** | **bool** |  | [optional] 
**runtime_apis** | [**List[GlobalBaseRuntimeApisInner]**](GlobalBaseRuntimeApisInner.md) |  | [optional] 
**set_dumpable** | **bool** |  | [optional] 
**set_var** | [**List[GlobalBaseSetVarInner]**](GlobalBaseSetVarInner.md) |  | [optional] 
**set_var_fmt** | [**List[GlobalBaseSetVarFmtInner]**](GlobalBaseSetVarFmtInner.md) |  | [optional] 
**setcap** | **str** |  | [optional] 
**ssl_options** | [**SslOptions**](SslOptions.md) |  | [optional] 
**stats_file** | **str** |  | [optional] 
**stats_maxconn** | **int** |  | [optional] 
**stats_timeout** | **int** |  | [optional] 
**strict_limits** | **bool** |  | [optional] 
**thread_group_lines** | [**List[GlobalBaseThreadGroupLinesInner]**](GlobalBaseThreadGroupLinesInner.md) |  | [optional] 
**thread_groups** | **int** |  | [optional] 
**tune_buffer_options** | [**TuneBufferOptions**](TuneBufferOptions.md) |  | [optional] 
**tune_lua_options** | [**TuneLuaOptions**](TuneLuaOptions.md) |  | [optional] 
**tune_options** | [**TuneOptions**](TuneOptions.md) |  | [optional] 
**tune_quic_options** | [**TuneQuicOptions**](TuneQuicOptions.md) |  | [optional] 
**tune_ssl_options** | [**TuneSslOptions**](TuneSslOptions.md) |  | [optional] 
**tune_vars_options** | [**TuneVarsOptions**](TuneVarsOptions.md) |  | [optional] 
**tune_zlib_options** | [**TuneZlibOptions**](TuneZlibOptions.md) |  | [optional] 
**uid** | **int** |  | [optional] 
**ulimit_n** | **int** |  | [optional] 
**user** | **str** |  | [optional] 
**warn_blocked_traffic_after** | **int** |  | [optional] 
**wurfl_options** | [**WurflOptions**](WurflOptions.md) |  | [optional] 
**log_target_list** | [**List[LogTarget]**](LogTarget.md) | HAProxy log target array (corresponds to log directives) | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.model_global import ModelGlobal

# TODO update the JSON string below
json = "{}"
# create an instance of ModelGlobal from a JSON string
model_global_instance = ModelGlobal.from_json(json)
# print the JSON string representation of the object
print(ModelGlobal.to_json())

# convert the object into a dict
model_global_dict = model_global_instance.to_dict()
# create an instance of ModelGlobal from a dict
model_global_from_dict = ModelGlobal.from_dict(model_global_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


