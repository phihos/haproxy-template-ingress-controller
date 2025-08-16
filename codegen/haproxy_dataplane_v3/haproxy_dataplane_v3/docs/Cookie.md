# Cookie


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**attr** | [**List[CookieAttrInner]**](CookieAttrInner.md) |  | [optional] 
**domain** | [**List[CookieDomainInner]**](CookieDomainInner.md) |  | [optional] 
**dynamic** | **bool** |  | [optional] 
**httponly** | **bool** |  | [optional] 
**indirect** | **bool** |  | [optional] 
**maxidle** | **int** |  | [optional] 
**maxlife** | **int** |  | [optional] 
**name** | **str** |  | 
**nocache** | **bool** |  | [optional] 
**postonly** | **bool** |  | [optional] 
**preserve** | **bool** |  | [optional] 
**secure** | **bool** |  | [optional] 
**type** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.cookie import Cookie

# TODO update the JSON string below
json = "{}"
# create an instance of Cookie from a JSON string
cookie_instance = Cookie.from_json(json)
# print the JSON string representation of the object
print(Cookie.to_json())

# convert the object into a dict
cookie_dict = cookie_instance.to_dict()
# create an instance of Cookie from a dict
cookie_from_dict = Cookie.from_dict(cookie_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


