# Frontend

Frontend with all it's children resources

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**accept_invalid_http_request** | **str** |  | [optional] 
**accept_unsafe_violations_in_http_request** | **str** |  | [optional] 
**backlog** | **int** |  | [optional] 
**clflog** | **bool** |  | [optional] 
**client_fin_timeout** | **int** |  | [optional] 
**client_timeout** | **int** |  | [optional] 
**clitcpka** | **str** |  | [optional] 
**clitcpka_cnt** | **int** |  | [optional] 
**clitcpka_idle** | **int** |  | [optional] 
**clitcpka_intvl** | **int** |  | [optional] 
**compression** | [**Compression**](Compression.md) |  | [optional] 
**contstats** | **str** |  | [optional] 
**default_backend** | **str** |  | [optional] 
**description** | **str** |  | [optional] 
**disable_h2_upgrade** | **str** |  | [optional] 
**disabled** | **bool** |  | [optional] 
**dontlog_normal** | **str** |  | [optional] 
**dontlognull** | **str** |  | [optional] 
**email_alert** | [**EmailAlert**](EmailAlert.md) |  | [optional] 
**enabled** | **bool** |  | [optional] 
**error_files** | [**List[Errorfile]**](Errorfile.md) |  | [optional] 
**error_log_format** | **str** |  | [optional] 
**errorfiles_from_http_errors** | [**List[Errorfiles]**](Errorfiles.md) |  | [optional] 
**errorloc302** | [**Errorloc**](Errorloc.md) |  | [optional] 
**errorloc303** | [**Errorloc**](Errorloc.md) |  | [optional] 
**forwardfor** | [**Forwardfor**](Forwardfor.md) |  | [optional] 
**var_from** | **str** |  | [optional] 
**guid** | **str** |  | [optional] 
**h1_case_adjust_bogus_client** | **str** |  | [optional] 
**http_buffer_request** | **str** |  | [optional] 
**http_drop_response_trailers** | **str** |  | [optional] 
**http_use_htx** | **str** |  | [optional] 
**http_connection_mode** | **str** |  | [optional] 
**http_ignore_probes** | **str** |  | [optional] 
**http_keep_alive_timeout** | **int** |  | [optional] 
**http_no_delay** | **str** |  | [optional] 
**http_request_timeout** | **int** |  | [optional] 
**http_restrict_req_hdr_names** | **str** |  | [optional] 
**http_use_proxy_header** | **str** |  | [optional] 
**httplog** | **bool** |  | [optional] 
**httpslog** | **str** |  | [optional] 
**id** | **int** |  | [optional] 
**idle_close_on_response** | **str** |  | [optional] 
**independent_streams** | **str** |  | [optional] 
**log_format** | **str** |  | [optional] 
**log_format_sd** | **str** |  | [optional] 
**log_separate_errors** | **str** |  | [optional] 
**log_steps** | **List[str]** |  | [optional] 
**log_tag** | **str** |  | [optional] 
**logasap** | **str** |  | [optional] 
**maxconn** | **int** |  | [optional] 
**metadata** | **object** |  | [optional] 
**mode** | **str** |  | [optional] 
**monitor_fail** | [**MonitorFail**](MonitorFail.md) |  | [optional] 
**monitor_uri** | **str** |  | [optional] 
**name** | **str** |  | 
**nolinger** | **str** |  | [optional] 
**originalto** | [**Originalto**](Originalto.md) |  | [optional] 
**socket_stats** | **str** |  | [optional] 
**splice_auto** | **str** |  | [optional] 
**splice_request** | **str** |  | [optional] 
**splice_response** | **str** |  | [optional] 
**stats_options** | [**StatsOptions**](StatsOptions.md) |  | [optional] 
**stick_table** | [**ConfigStickTable**](ConfigStickTable.md) |  | [optional] 
**tarpit_timeout** | **int** |  | [optional] 
**tcp_smart_accept** | **str** |  | [optional] 
**tcpka** | **str** |  | [optional] 
**tcplog** | **bool** |  | [optional] 
**unique_id_format** | **str** |  | [optional] 
**unique_id_header** | **str** |  | [optional] 
**acl_list** | [**List[Acl]**](Acl.md) | HAProxy ACL lines array (corresponds to acl directives) | [optional] 
**backend_switching_rule_list** | [**List[BackendSwitchingRule]**](BackendSwitchingRule.md) | HAProxy backend switching rules array (corresponds to use_backend directives) | [optional] 
**binds** | **object** |  | [optional] 
**capture_list** | [**List[Capture]**](Capture.md) |  | [optional] 
**filter_list** | [**List[Filter]**](Filter.md) | HAProxy filters array (corresponds to filter directive) | [optional] 
**http_after_response_rule_list** | [**List[HttpAfterResponseRule]**](HttpAfterResponseRule.md) | HAProxy HTTP after response rules array (corresponds to http-after-response directives) | [optional] 
**http_error_rule_list** | [**List[HttpErrorRule]**](HttpErrorRule.md) | HAProxy HTTP error rules array (corresponds to http-error directives) | [optional] 
**http_request_rule_list** | [**List[HttpRequestRule]**](HttpRequestRule.md) | HAProxy HTTP request rules array (corresponds to http-request directives) | [optional] 
**http_response_rule_list** | [**List[HttpResponseRule]**](HttpResponseRule.md) | HAProxy HTTP response rules array (corresponds to http-response directives) | [optional] 
**log_target_list** | [**List[LogTarget]**](LogTarget.md) | HAProxy log target array (corresponds to log directives) | [optional] 
**quic_initial_rule_list** | [**List[QuicInitialRule]**](QuicInitialRule.md) |  | [optional] 
**ssl_front_use_list** | [**List[SslFrontUse]**](SslFrontUse.md) |  | [optional] 
**tcp_request_rule_list** | [**List[TcpRequestRule]**](TcpRequestRule.md) | HAProxy TCP request rules array (corresponds to tcp-request directive) | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.frontend import Frontend

# TODO update the JSON string below
json = "{}"
# create an instance of Frontend from a JSON string
frontend_instance = Frontend.from_json(json)
# print the JSON string representation of the object
print(Frontend.to_json())

# convert the object into a dict
frontend_dict = frontend_instance.to_dict()
# create an instance of Frontend from a dict
frontend_from_dict = Frontend.from_dict(frontend_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


