# BackendBase

HAProxy backend configuration

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**abortonclose** | **str** |  | [optional] 
**accept_invalid_http_response** | **str** |  | [optional] 
**accept_unsafe_violations_in_http_response** | **str** |  | [optional] 
**adv_check** | **str** |  | [optional] 
**allbackups** | **str** |  | [optional] 
**balance** | [**Balance**](Balance.md) |  | [optional] 
**check_timeout** | **int** |  | [optional] 
**checkcache** | **str** |  | [optional] 
**compression** | [**Compression**](Compression.md) |  | [optional] 
**connect_timeout** | **int** |  | [optional] 
**cookie** | [**Cookie**](Cookie.md) |  | [optional] 
**default_server** | [**DefaultServer**](DefaultServer.md) |  | [optional] 
**description** | **str** |  | [optional] 
**disabled** | **bool** |  | [optional] 
**dynamic_cookie_key** | **str** |  | [optional] 
**email_alert** | [**EmailAlert**](EmailAlert.md) |  | [optional] 
**enabled** | **bool** |  | [optional] 
**error_files** | [**List[Errorfile]**](Errorfile.md) |  | [optional] 
**errorfiles_from_http_errors** | [**List[Errorfiles]**](Errorfiles.md) |  | [optional] 
**errorloc302** | [**Errorloc**](Errorloc.md) |  | [optional] 
**errorloc303** | [**Errorloc**](Errorloc.md) |  | [optional] 
**external_check** | **str** |  | [optional] 
**external_check_command** | **str** |  | [optional] 
**external_check_path** | **str** |  | [optional] 
**force_persist** | [**BackendBaseForcePersist**](BackendBaseForcePersist.md) |  | [optional] 
**force_persist_list** | [**List[BackendBaseForcePersistListInner]**](BackendBaseForcePersistListInner.md) |  | [optional] 
**forwardfor** | [**Forwardfor**](Forwardfor.md) |  | [optional] 
**var_from** | **str** |  | [optional] 
**fullconn** | **int** |  | [optional] 
**guid** | **str** |  | [optional] 
**h1_case_adjust_bogus_server** | **str** |  | [optional] 
**hash_balance_factor** | **int** |  | [optional] 
**hash_preserve_affinity** | **str** |  | [optional] 
**hash_type** | [**HashType**](HashType.md) |  | [optional] 
**http_buffer_request** | **str** |  | [optional] 
**http_drop_request_trailers** | **str** |  | [optional] 
**http_no_delay** | **str** |  | [optional] 
**http_use_htx** | **str** |  | [optional] 
**http_connection_mode** | **str** |  | [optional] 
**http_keep_alive_timeout** | **int** |  | [optional] 
**http_pretend_keepalive** | **str** |  | [optional] 
**http_proxy** | **str** |  | [optional] 
**http_request_timeout** | **int** |  | [optional] 
**http_restrict_req_hdr_names** | **str** |  | [optional] 
**http_reuse** | **str** |  | [optional] 
**http_send_name_header** | **str** |  | [optional] 
**httpchk_params** | [**HttpchkParams**](HttpchkParams.md) |  | [optional] 
**id** | **int** |  | [optional] 
**ignore_persist** | [**BackendBaseIgnorePersist**](BackendBaseIgnorePersist.md) |  | [optional] 
**ignore_persist_list** | [**List[BackendBaseIgnorePersistListInner]**](BackendBaseIgnorePersistListInner.md) |  | [optional] 
**independent_streams** | **str** |  | [optional] 
**load_server_state_from_file** | **str** |  | [optional] 
**log_health_checks** | **str** |  | [optional] 
**log_tag** | **str** |  | [optional] 
**max_keep_alive_queue** | **int** |  | [optional] 
**metadata** | **object** |  | [optional] 
**mode** | **str** |  | [optional] 
**mysql_check_params** | [**MysqlCheckParams**](MysqlCheckParams.md) |  | [optional] 
**name** | **str** |  | 
**nolinger** | **str** |  | [optional] 
**originalto** | [**Originalto**](Originalto.md) |  | [optional] 
**persist** | **str** |  | [optional] 
**persist_rule** | [**PersistRule**](PersistRule.md) |  | [optional] 
**pgsql_check_params** | [**PgsqlCheckParams**](PgsqlCheckParams.md) |  | [optional] 
**prefer_last_server** | **str** |  | [optional] 
**queue_timeout** | **int** |  | [optional] 
**redispatch** | [**Redispatch**](Redispatch.md) |  | [optional] 
**retries** | **int** |  | [optional] 
**retry_on** | **str** |  | [optional] 
**server_fin_timeout** | **int** |  | [optional] 
**server_state_file_name** | **str** |  | [optional] 
**server_timeout** | **int** |  | [optional] 
**smtpchk_params** | [**SmtpchkParams**](SmtpchkParams.md) |  | [optional] 
**source** | [**Source**](Source.md) |  | [optional] 
**splice_auto** | **str** |  | [optional] 
**splice_request** | **str** |  | [optional] 
**splice_response** | **str** |  | [optional] 
**spop_check** | **str** |  | [optional] 
**srvtcpka** | **str** |  | [optional] 
**srvtcpka_cnt** | **int** |  | [optional] 
**srvtcpka_idle** | **int** |  | [optional] 
**srvtcpka_intvl** | **int** |  | [optional] 
**stats_options** | [**StatsOptions**](StatsOptions.md) |  | [optional] 
**stick_table** | [**ConfigStickTable**](ConfigStickTable.md) |  | [optional] 
**tarpit_timeout** | **int** |  | [optional] 
**tcp_smart_connect** | **str** |  | [optional] 
**tcpka** | **str** |  | [optional] 
**transparent** | **str** |  | [optional] 
**tunnel_timeout** | **int** |  | [optional] 
**use_fcgi_app** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.backend_base import BackendBase

# TODO update the JSON string below
json = "{}"
# create an instance of BackendBase from a JSON string
backend_base_instance = BackendBase.from_json(json)
# print the JSON string representation of the object
print(BackendBase.to_json())

# convert the object into a dict
backend_base_dict = backend_base_instance.to_dict()
# create an instance of BackendBase from a dict
backend_base_from_dict = BackendBase.from_dict(backend_base_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


