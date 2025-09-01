from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.fcgi_application_base_get_values import FCGIApplicationBaseGetValues
from ..models.fcgi_application_base_keep_conn import FCGIApplicationBaseKeepConn
from ..models.fcgi_application_base_mpxs_conns import FCGIApplicationBaseMpxsConns
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.acl_lines import ACLLines
    from ..models.fcgi_log_stderr import FcgiLogStderr
    from ..models.fcgi_pass_header import FcgiPassHeader
    from ..models.fcgi_set_param import FcgiSetParam


T = TypeVar("T", bound="FcgiApp")


@_attrs_define
class FcgiApp:
    """App with all it's children resources

    Attributes:
        docroot (str): Defines the document root on the remote host. The parameter serves to build the default value of
            FastCGI parameters SCRIPT_FILENAME and PATH_TRANSLATED. It is a mandatory setting.
        name (str): Declares a FastCGI application
        get_values (Union[Unset, FCGIApplicationBaseGetValues]): Enables or disables the retrieval of variables related
            to connection management.
        index (Union[Unset, str]): Defines the script name to append after a URI that ends with a slash ("/") to set the
            default value for the FastCGI parameter SCRIPT_NAME. It is an optional setting.
        keep_conn (Union[Unset, FCGIApplicationBaseKeepConn]): Tells the FastCGI application whether or not to keep the
            connection open after it sends a response. If disabled, the FastCGI application closes the connection after
            responding to this request.
        log_stderrs (Union[Unset, list['FcgiLogStderr']]):
        max_reqs (Union[Unset, int]): Defines the maximum number of concurrent requests this application can accept. If
            the FastCGI application retrieves the variable FCGI_MAX_REQS during connection establishment, it can override
            this option. Furthermore, if the application does not do multiplexing, it will ignore this option. Default: 1.
        metadata (Union[Unset, Any]):
        mpxs_conns (Union[Unset, FCGIApplicationBaseMpxsConns]): Enables or disables the support of connection
            multiplexing. If the FastCGI application retrieves the variable FCGI_MPXS_CONNS during connection establishment,
            it can override this option.
        pass_headers (Union[Unset, list['FcgiPassHeader']]):
        path_info (Union[Unset, str]): Defines a regular expression to extract the script-name and the path-info from
            the URI.
            Thus, <regex> must have two captures: the first to capture the script name, and the second to capture the path-
            info.
            If not defined, it does not perform matching on the URI, and does not fill the FastCGI parameters PATH_INFO and
            PATH_TRANSLATED.
        set_params (Union[Unset, list['FcgiSetParam']]):
        acl_list (Union[Unset, list['ACLLines']]): HAProxy ACL lines array (corresponds to acl directives)
    """

    docroot: str
    name: str
    get_values: Union[Unset, FCGIApplicationBaseGetValues] = UNSET
    index: Union[Unset, str] = UNSET
    keep_conn: Union[Unset, FCGIApplicationBaseKeepConn] = UNSET
    log_stderrs: Union[Unset, list["FcgiLogStderr"]] = UNSET
    max_reqs: Union[Unset, int] = 1
    metadata: Union[Unset, Any] = UNSET
    mpxs_conns: Union[Unset, FCGIApplicationBaseMpxsConns] = UNSET
    pass_headers: Union[Unset, list["FcgiPassHeader"]] = UNSET
    path_info: Union[Unset, str] = UNSET
    set_params: Union[Unset, list["FcgiSetParam"]] = UNSET
    acl_list: Union[Unset, list["ACLLines"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        docroot = self.docroot

        name = self.name

        get_values: Union[Unset, str] = UNSET
        if not isinstance(self.get_values, Unset):
            get_values = self.get_values.value

        index = self.index

        keep_conn: Union[Unset, str] = UNSET
        if not isinstance(self.keep_conn, Unset):
            keep_conn = self.keep_conn.value

        log_stderrs: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.log_stderrs, Unset):
            log_stderrs = []
            for log_stderrs_item_data in self.log_stderrs:
                log_stderrs_item = log_stderrs_item_data.to_dict()
                log_stderrs.append(log_stderrs_item)

        max_reqs = self.max_reqs

        metadata = self.metadata

        mpxs_conns: Union[Unset, str] = UNSET
        if not isinstance(self.mpxs_conns, Unset):
            mpxs_conns = self.mpxs_conns.value

        pass_headers: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.pass_headers, Unset):
            pass_headers = []
            for pass_headers_item_data in self.pass_headers:
                pass_headers_item = pass_headers_item_data.to_dict()
                pass_headers.append(pass_headers_item)

        path_info = self.path_info

        set_params: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.set_params, Unset):
            set_params = []
            for set_params_item_data in self.set_params:
                set_params_item = set_params_item_data.to_dict()
                set_params.append(set_params_item)

        acl_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.acl_list, Unset):
            acl_list = []
            for componentsschemasacls_item_data in self.acl_list:
                componentsschemasacls_item = componentsschemasacls_item_data.to_dict()
                acl_list.append(componentsschemasacls_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "docroot": docroot,
                "name": name,
            }
        )
        if get_values is not UNSET:
            field_dict["get_values"] = get_values
        if index is not UNSET:
            field_dict["index"] = index
        if keep_conn is not UNSET:
            field_dict["keep_conn"] = keep_conn
        if log_stderrs is not UNSET:
            field_dict["log_stderrs"] = log_stderrs
        if max_reqs is not UNSET:
            field_dict["max_reqs"] = max_reqs
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if mpxs_conns is not UNSET:
            field_dict["mpxs_conns"] = mpxs_conns
        if pass_headers is not UNSET:
            field_dict["pass_headers"] = pass_headers
        if path_info is not UNSET:
            field_dict["path_info"] = path_info
        if set_params is not UNSET:
            field_dict["set_params"] = set_params
        if acl_list is not UNSET:
            field_dict["acl_list"] = acl_list

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.acl_lines import ACLLines
        from ..models.fcgi_log_stderr import FcgiLogStderr
        from ..models.fcgi_pass_header import FcgiPassHeader
        from ..models.fcgi_set_param import FcgiSetParam

        d = dict(src_dict)
        docroot = d.pop("docroot")

        name = d.pop("name")

        _get_values = d.pop("get_values", UNSET)
        get_values: Union[Unset, FCGIApplicationBaseGetValues]
        if isinstance(_get_values, Unset):
            get_values = UNSET
        else:
            get_values = FCGIApplicationBaseGetValues(_get_values)

        index = d.pop("index", UNSET)

        _keep_conn = d.pop("keep_conn", UNSET)
        keep_conn: Union[Unset, FCGIApplicationBaseKeepConn]
        if isinstance(_keep_conn, Unset):
            keep_conn = UNSET
        else:
            keep_conn = FCGIApplicationBaseKeepConn(_keep_conn)

        _log_stderrs = d.pop("log_stderrs", UNSET)
        log_stderrs: Union[Unset, list[FcgiLogStderr]] = UNSET
        if not isinstance(_log_stderrs, Unset):
            log_stderrs = []
            for log_stderrs_item_data in _log_stderrs:
                log_stderrs_item = FcgiLogStderr.from_dict(log_stderrs_item_data)

                log_stderrs.append(log_stderrs_item)

        max_reqs = d.pop("max_reqs", UNSET)

        metadata = d.pop("metadata", UNSET)

        _mpxs_conns = d.pop("mpxs_conns", UNSET)
        mpxs_conns: Union[Unset, FCGIApplicationBaseMpxsConns]
        if isinstance(_mpxs_conns, Unset):
            mpxs_conns = UNSET
        else:
            mpxs_conns = FCGIApplicationBaseMpxsConns(_mpxs_conns)

        _pass_headers = d.pop("pass_headers", UNSET)
        pass_headers: Union[Unset, list[FcgiPassHeader]] = UNSET
        if not isinstance(_pass_headers, Unset):
            pass_headers = []
            for pass_headers_item_data in _pass_headers:
                pass_headers_item = FcgiPassHeader.from_dict(pass_headers_item_data)

                pass_headers.append(pass_headers_item)

        path_info = d.pop("path_info", UNSET)

        _set_params = d.pop("set_params", UNSET)
        set_params: Union[Unset, list[FcgiSetParam]] = UNSET
        if not isinstance(_set_params, Unset):
            set_params = []
            for set_params_item_data in _set_params:
                set_params_item = FcgiSetParam.from_dict(set_params_item_data)

                set_params.append(set_params_item)

        _acl_list = d.pop("acl_list", UNSET)
        acl_list: Union[Unset, list[ACLLines]] = UNSET
        if not isinstance(_acl_list, Unset):
            acl_list = []
            for componentsschemasacls_item_data in _acl_list:
                componentsschemasacls_item = ACLLines.from_dict(componentsschemasacls_item_data)

                acl_list.append(componentsschemasacls_item)

        fcgi_app = cls(
            docroot=docroot,
            name=name,
            get_values=get_values,
            index=index,
            keep_conn=keep_conn,
            log_stderrs=log_stderrs,
            max_reqs=max_reqs,
            metadata=metadata,
            mpxs_conns=mpxs_conns,
            pass_headers=pass_headers,
            path_info=path_info,
            set_params=set_params,
            acl_list=acl_list,
        )

        fcgi_app.additional_properties = d
        return fcgi_app

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
