# ServerTemplate

Set a template to initialize servers with shared parameters.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**agent_addr** | **str** |  | [optional] 
**agent_check** | **str** |  | [optional] 
**agent_inter** | **int** |  | [optional] 
**agent_port** | **int** |  | [optional] 
**agent_send** | **str** |  | [optional] 
**allow_0rtt** | **bool** |  | [optional] 
**alpn** | **str** |  | [optional] 
**backup** | **str** |  | [optional] 
**check** | **str** |  | [optional] 
**check_pool_conn_name** | **str** |  | [optional] 
**check_reuse_pool** | **str** |  | [optional] 
**check_send_proxy** | **str** |  | [optional] 
**check_sni** | **str** |  | [optional] 
**check_ssl** | **str** |  | [optional] 
**check_alpn** | **str** |  | [optional] 
**check_proto** | **str** |  | [optional] 
**check_via_socks4** | **str** |  | [optional] 
**ciphers** | **str** |  | [optional] 
**ciphersuites** | **str** |  | [optional] 
**client_sigalgs** | **str** |  | [optional] 
**cookie** | **str** |  | [optional] 
**crl_file** | **str** |  | [optional] 
**curves** | **str** |  | [optional] 
**downinter** | **int** |  | [optional] 
**error_limit** | **int** |  | [optional] 
**fall** | **int** |  | [optional] 
**fastinter** | **int** |  | [optional] 
**force_sslv3** | **str** | This field is deprecated in favor of sslv3, and will be removed in a future release | [optional] 
**force_tlsv10** | **str** | This field is deprecated in favor of tlsv10, and will be removed in a future release | [optional] 
**force_tlsv11** | **str** | This field is deprecated in favor of tlsv11, and will be removed in a future release | [optional] 
**force_tlsv12** | **str** | This field is deprecated in favor of tlsv12, and will be removed in a future release | [optional] 
**force_tlsv13** | **str** | This field is deprecated in favor of tlsv13, and will be removed in a future release | [optional] 
**guid** | **str** |  | [optional] 
**hash_key** | **str** |  | [optional] 
**health_check_address** | **str** |  | [optional] 
**health_check_port** | **int** |  | [optional] 
**idle_ping** | **int** |  | [optional] 
**init_addr** | **str** |  | [optional] 
**init_state** | **str** |  | [optional] 
**inter** | **int** |  | [optional] 
**log_bufsize** | **int** |  | [optional] 
**log_proto** | **str** |  | [optional] 
**maintenance** | **str** |  | [optional] 
**max_reuse** | **int** |  | [optional] 
**maxconn** | **int** |  | [optional] 
**maxqueue** | **int** |  | [optional] 
**minconn** | **int** |  | [optional] 
**namespace** | **str** |  | [optional] 
**no_sslv3** | **str** | This field is deprecated in favor of sslv3, and will be removed in a future release | [optional] 
**no_tlsv10** | **str** | This field is deprecated in favor of tlsv10, and will be removed in a future release | [optional] 
**no_tlsv11** | **str** | This field is deprecated in favor of tlsv11, and will be removed in a future release | [optional] 
**no_tlsv12** | **str** | This field is deprecated in favor of tlsv12, and will be removed in a future release | [optional] 
**no_tlsv13** | **str** | This field is deprecated in favor of force_tlsv13, and will be removed in a future release | [optional] 
**no_verifyhost** | **str** |  | [optional] 
**npn** | **str** |  | [optional] 
**observe** | **str** |  | [optional] 
**on_error** | **str** |  | [optional] 
**on_marked_down** | **str** |  | [optional] 
**on_marked_up** | **str** |  | [optional] 
**pool_conn_name** | **str** |  | [optional] 
**pool_low_conn** | **int** |  | [optional] 
**pool_max_conn** | **int** |  | [optional] 
**pool_purge_delay** | **int** |  | [optional] 
**proto** | **str** |  | [optional] 
**proxy_v2_options** | **List[str]** |  | [optional] 
**redir** | **str** |  | [optional] 
**resolve_net** | **str** |  | [optional] 
**resolve_prefer** | **str** |  | [optional] 
**resolve_opts** | **str** |  | [optional] 
**resolvers** | **str** |  | [optional] 
**rise** | **int** |  | [optional] 
**send_proxy** | **str** |  | [optional] 
**send_proxy_v2** | **str** |  | [optional] 
**send_proxy_v2_ssl** | **str** |  | [optional] 
**send_proxy_v2_ssl_cn** | **str** |  | [optional] 
**set_proxy_v2_tlv_fmt** | [**ServerParamsSetProxyV2TlvFmt**](ServerParamsSetProxyV2TlvFmt.md) |  | [optional] 
**shard** | **int** |  | [optional] 
**sigalgs** | **str** |  | [optional] 
**slowstart** | **int** |  | [optional] 
**sni** | **str** |  | [optional] 
**socks4** | **str** |  | [optional] 
**source** | **str** |  | [optional] 
**ssl** | **str** |  | [optional] 
**ssl_cafile** | **str** |  | [optional] 
**ssl_certificate** | **str** |  | [optional] 
**ssl_max_ver** | **str** |  | [optional] 
**ssl_min_ver** | **str** |  | [optional] 
**ssl_reuse** | **str** |  | [optional] 
**sslv3** | **str** |  | [optional] 
**stick** | **str** |  | [optional] 
**strict_maxconn** | **bool** |  | [optional] 
**tcp_ut** | **int** |  | [optional] 
**tfo** | **str** |  | [optional] 
**tls_tickets** | **str** |  | [optional] 
**tlsv10** | **str** |  | [optional] 
**tlsv11** | **str** |  | [optional] 
**tlsv12** | **str** |  | [optional] 
**tlsv13** | **str** |  | [optional] 
**track** | **str** |  | [optional] 
**verify** | **str** |  | [optional] 
**verifyhost** | **str** |  | [optional] 
**weight** | **int** |  | [optional] 
**ws** | **str** |  | [optional] 
**fqdn** | **str** |  | 
**id** | **int** |  | [optional] 
**metadata** | **object** |  | [optional] 
**num_or_range** | **str** |  | 
**port** | **int** |  | [optional] 
**prefix** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.server_template import ServerTemplate

# TODO update the JSON string below
json = "{}"
# create an instance of ServerTemplate from a JSON string
server_template_instance = ServerTemplate.from_json(json)
# print the JSON string representation of the object
print(ServerTemplate.to_json())

# convert the object into a dict
server_template_dict = server_template_instance.to_dict()
# create an instance of ServerTemplate from a dict
server_template_from_dict = ServerTemplate.from_dict(server_template_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


