# BindParams


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**accept_netscaler_cip** | **int** |  | [optional] 
**accept_proxy** | **bool** |  | [optional] 
**allow_0rtt** | **bool** |  | [optional] 
**alpn** | **str** |  | [optional] 
**backlog** | **str** |  | [optional] 
**ca_ignore_err** | **str** |  | [optional] 
**ca_sign_file** | **str** |  | [optional] 
**ca_sign_pass** | **str** |  | [optional] 
**ca_verify_file** | **str** |  | [optional] 
**ciphers** | **str** |  | [optional] 
**ciphersuites** | **str** |  | [optional] 
**client_sigalgs** | **str** |  | [optional] 
**crl_file** | **str** |  | [optional] 
**crt_ignore_err** | **str** |  | [optional] 
**crt_list** | **str** |  | [optional] 
**curves** | **str** |  | [optional] 
**default_crt_list** | **List[str]** |  | [optional] 
**defer_accept** | **bool** |  | [optional] 
**ecdhe** | **str** |  | [optional] 
**expose_fd_listeners** | **bool** |  | [optional] 
**force_sslv3** | **bool** | This field is deprecated in favor of sslv3, and will be removed in a future release | [optional] 
**force_strict_sni** | **str** |  | [optional] 
**force_tlsv10** | **bool** | This field is deprecated in favor of tlsv10, and will be removed in a future release | [optional] 
**force_tlsv11** | **bool** | This field is deprecated in favor of tlsv11, and will be removed in a future release | [optional] 
**force_tlsv12** | **bool** | This field is deprecated in favor of tlsv12, and will be removed in a future release | [optional] 
**force_tlsv13** | **bool** | This field is deprecated in favor of tlsv13, and will be removed in a future release | [optional] 
**generate_certificates** | **bool** |  | [optional] 
**gid** | **int** |  | [optional] 
**group** | **str** |  | [optional] 
**guid_prefix** | **str** |  | [optional] 
**id** | **str** |  | [optional] 
**idle_ping** | **int** |  | [optional] 
**interface** | **str** |  | [optional] 
**level** | **str** |  | [optional] 
**maxconn** | **int** |  | [optional] 
**mode** | **str** |  | [optional] 
**mss** | **str** |  | [optional] 
**name** | **str** |  | [optional] 
**namespace** | **str** |  | [optional] 
**nbconn** | **int** |  | [optional] 
**nice** | **int** |  | [optional] 
**no_alpn** | **bool** |  | [optional] 
**no_ca_names** | **bool** |  | [optional] 
**no_sslv3** | **bool** | This field is deprecated in favor of sslv3, and will be removed in a future release | [optional] 
**no_strict_sni** | **bool** |  | [optional] 
**no_tls_tickets** | **bool** | This field is deprecated in favor of tls_tickets, and will be removed in a future release | [optional] 
**no_tlsv10** | **bool** | This field is deprecated in favor of tlsv10, and will be removed in a future release | [optional] 
**no_tlsv11** | **bool** | This field is deprecated in favor of tlsv11, and will be removed in a future release | [optional] 
**no_tlsv12** | **bool** | This field is deprecated in favor of tlsv12, and will be removed in a future release | [optional] 
**no_tlsv13** | **bool** | This field is deprecated in favor of tlsv13, and will be removed in a future release | [optional] 
**npn** | **str** |  | [optional] 
**prefer_client_ciphers** | **bool** |  | [optional] 
**proto** | **str** |  | [optional] 
**quic_cc_algo** | **str** |  | [optional] 
**quic_force_retry** | **bool** |  | [optional] 
**quic_socket** | **str** |  | [optional] 
**quic_cc_algo_burst_size** | **int** |  | [optional] 
**quic_cc_algo_max_window** | **int** |  | [optional] 
**severity_output** | **str** |  | [optional] 
**sigalgs** | **str** |  | [optional] 
**ssl** | **bool** |  | [optional] 
**ssl_cafile** | **str** |  | [optional] 
**ssl_certificate** | **str** |  | [optional] 
**ssl_max_ver** | **str** |  | [optional] 
**ssl_min_ver** | **str** |  | [optional] 
**sslv3** | **str** |  | [optional] 
**strict_sni** | **bool** |  | [optional] 
**tcp_user_timeout** | **int** |  | [optional] 
**tfo** | **bool** |  | [optional] 
**thread** | **str** |  | [optional] 
**tls_ticket_keys** | **str** |  | [optional] 
**tls_tickets** | **str** |  | [optional] 
**tlsv10** | **str** |  | [optional] 
**tlsv11** | **str** |  | [optional] 
**tlsv12** | **str** |  | [optional] 
**tlsv13** | **str** |  | [optional] 
**transparent** | **bool** |  | [optional] 
**uid** | **str** |  | [optional] 
**user** | **str** |  | [optional] 
**v4v6** | **bool** |  | [optional] 
**v6only** | **bool** |  | [optional] 
**verify** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.bind_params import BindParams

# TODO update the JSON string below
json = "{}"
# create an instance of BindParams from a JSON string
bind_params_instance = BindParams.from_json(json)
# print the JSON string representation of the object
print(BindParams.to_json())

# convert the object into a dict
bind_params_dict = bind_params_instance.to_dict()
# create an instance of BindParams from a dict
bind_params_from_dict = BindParams.from_dict(bind_params_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


