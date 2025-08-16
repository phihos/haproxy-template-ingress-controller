# RuntimeAddServer

Settable properties when adding a new server using HAProxy's runtime.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **str** |  | [optional] [readonly] 
**agent_addr** | **str** |  | [optional] 
**agent_check** | **str** |  | [optional] 
**agent_inter** | **int** |  | [optional] 
**agent_port** | **int** |  | [optional] 
**agent_send** | **str** |  | [optional] 
**allow_0rtt** | **bool** |  | [optional] 
**alpn** | **str** |  | [optional] 
**backup** | **str** |  | [optional] 
**check** | **str** |  | [optional] 
**check_send_proxy** | **str** |  | [optional] 
**check_sni** | **str** |  | [optional] 
**check_ssl** | **str** |  | [optional] 
**check_alpn** | **str** |  | [optional] 
**check_proto** | **str** |  | [optional] 
**check_via_socks4** | **str** |  | [optional] 
**ciphers** | **str** |  | [optional] 
**ciphersuites** | **str** |  | [optional] 
**crl_file** | **str** |  | [optional] 
**downinter** | **int** |  | [optional] 
**error_limit** | **int** |  | [optional] 
**fall** | **int** |  | [optional] 
**fastinter** | **int** |  | [optional] 
**force_sslv3** | **str** |  | [optional] 
**force_tlsv10** | **str** |  | [optional] 
**force_tlsv11** | **str** |  | [optional] 
**force_tlsv12** | **str** |  | [optional] 
**force_tlsv13** | **str** |  | [optional] 
**health_check_address** | **str** |  | [optional] 
**health_check_port** | **int** |  | [optional] 
**id** | **str** |  | [optional] [readonly] 
**inter** | **int** |  | [optional] 
**maintenance** | **str** |  | [optional] 
**maxconn** | **int** |  | [optional] 
**maxqueue** | **int** |  | [optional] 
**minconn** | **int** |  | [optional] 
**name** | **str** |  | [optional] [readonly] 
**no_sslv3** | **str** |  | [optional] 
**no_tlsv10** | **str** |  | [optional] 
**no_tlsv11** | **str** |  | [optional] 
**no_tlsv12** | **str** |  | [optional] 
**no_tlsv13** | **str** |  | [optional] 
**npn** | **str** |  | [optional] 
**observe** | **str** |  | [optional] 
**on_error** | **str** |  | [optional] 
**on_marked_down** | **str** |  | [optional] 
**on_marked_up** | **str** |  | [optional] 
**pool_low_conn** | **int** |  | [optional] 
**pool_max_conn** | **int** |  | [optional] 
**pool_purge_delay** | **int** |  | [optional] 
**port** | **int** |  | [optional] [readonly] 
**proto** | **str** |  | [optional] 
**proxy_v2_options** | **List[str]** |  | [optional] 
**rise** | **int** |  | [optional] 
**send_proxy** | **str** |  | [optional] 
**send_proxy_v2** | **str** |  | [optional] 
**send_proxy_v2_ssl** | **str** |  | [optional] 
**send_proxy_v2_ssl_cn** | **str** |  | [optional] 
**slowstart** | **int** |  | [optional] 
**sni** | **str** |  | [optional] 
**source** | **str** |  | [optional] 
**ssl** | **str** |  | [optional] 
**ssl_cafile** | **str** |  | [optional] 
**ssl_certificate** | **str** |  | [optional] 
**ssl_max_ver** | **str** |  | [optional] 
**ssl_min_ver** | **str** |  | [optional] 
**ssl_reuse** | **str** |  | [optional] 
**tfo** | **str** |  | [optional] 
**tls_tickets** | **str** |  | [optional] 
**track** | **str** |  | [optional] 
**verify** | **str** |  | [optional] 
**verifyhost** | **str** |  | [optional] 
**weight** | **int** |  | [optional] 
**ws** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.runtime_add_server import RuntimeAddServer

# TODO update the JSON string below
json = "{}"
# create an instance of RuntimeAddServer from a JSON string
runtime_add_server_instance = RuntimeAddServer.from_json(json)
# print the JSON string representation of the object
print(RuntimeAddServer.to_json())

# convert the object into a dict
runtime_add_server_dict = runtime_add_server_instance.to_dict()
# create an instance of RuntimeAddServer from a dict
runtime_add_server_from_dict = RuntimeAddServer.from_dict(runtime_add_server_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


