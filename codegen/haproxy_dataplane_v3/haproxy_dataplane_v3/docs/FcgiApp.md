# FcgiApp

App with all it's children resources

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**docroot** | **str** | Defines the document root on the remote host. The parameter serves to build the default value of FastCGI parameters SCRIPT_FILENAME and PATH_TRANSLATED. It is a mandatory setting. | 
**get_values** | **str** | Enables or disables the retrieval of variables related to connection management. | [optional] 
**index** | **str** | Defines the script name to append after a URI that ends with a slash (\&quot;/\&quot;) to set the default value for the FastCGI parameter SCRIPT_NAME. It is an optional setting. | [optional] 
**keep_conn** | **str** | Tells the FastCGI application whether or not to keep the connection open after it sends a response. If disabled, the FastCGI application closes the connection after responding to this request. | [optional] 
**log_stderrs** | [**List[FcgiLogStderr]**](FcgiLogStderr.md) |  | [optional] 
**max_reqs** | **int** | Defines the maximum number of concurrent requests this application can accept. If the FastCGI application retrieves the variable FCGI_MAX_REQS during connection establishment, it can override this option. Furthermore, if the application does not do multiplexing, it will ignore this option. | [optional] 
**metadata** | **object** |  | [optional] 
**mpxs_conns** | **str** | Enables or disables the support of connection multiplexing. If the FastCGI application retrieves the variable FCGI_MPXS_CONNS during connection establishment, it can override this option. | [optional] 
**name** | **str** | Declares a FastCGI application | 
**pass_headers** | [**List[FcgiPassHeader]**](FcgiPassHeader.md) |  | [optional] 
**path_info** | **str** | Defines a regular expression to extract the script-name and the path-info from the URI. Thus, &lt;regex&gt; must have two captures: the first to capture the script name, and the second to capture the path- info. If not defined, it does not perform matching on the URI, and does not fill the FastCGI parameters PATH_INFO and PATH_TRANSLATED. | [optional] 
**set_params** | [**List[FcgiSetParam]**](FcgiSetParam.md) |  | [optional] 
**acl_list** | [**List[Acl]**](Acl.md) | HAProxy ACL lines array (corresponds to acl directives) | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.fcgi_app import FcgiApp

# TODO update the JSON string below
json = "{}"
# create an instance of FcgiApp from a JSON string
fcgi_app_instance = FcgiApp.from_json(json)
# print the JSON string representation of the object
print(FcgiApp.to_json())

# convert the object into a dict
fcgi_app_dict = fcgi_app_instance.to_dict()
# create an instance of FcgiApp from a dict
fcgi_app_from_dict = FcgiApp.from_dict(fcgi_app_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


