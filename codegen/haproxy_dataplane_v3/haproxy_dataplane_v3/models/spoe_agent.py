from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.spoe_agent_async import SPOEAgentAsync
from ..models.spoe_agent_continue_on_error import SPOEAgentContinueOnError
from ..models.spoe_agent_dontlog_normal import SPOEAgentDontlogNormal
from ..models.spoe_agent_force_set_var import SPOEAgentForceSetVar
from ..models.spoe_agent_pipelining import SPOEAgentPipelining
from ..models.spoe_agent_send_frag_payload import SPOEAgentSendFragPayload
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.log_target import LogTarget


T = TypeVar("T", bound="SPOEAgent")


@_attrs_define
class SPOEAgent:
    """SPOE agent configuration

    Attributes:
        name (str):
        async_ (Union[Unset, SPOEAgentAsync]):
        continue_on_error (Union[Unset, SPOEAgentContinueOnError]):
        dontlog_normal (Union[Unset, SPOEAgentDontlogNormal]):
        engine_name (Union[Unset, str]):
        force_set_var (Union[Unset, SPOEAgentForceSetVar]):
        groups (Union[Unset, str]):
        hello_timeout (Union[Unset, int]):
        idle_timeout (Union[Unset, int]):
        log (Union[Unset, list['LogTarget']]): HAProxy log target array (corresponds to log directives)
        max_frame_size (Union[Unset, int]):
        max_waiting_frames (Union[Unset, int]):
        maxconnrate (Union[Unset, int]):
        maxerrrate (Union[Unset, int]):
        messages (Union[Unset, str]):
        option_set_on_error (Union[Unset, str]):
        option_set_process_time (Union[Unset, str]):
        option_set_total_time (Union[Unset, str]):
        option_var_prefix (Union[Unset, str]):
        pipelining (Union[Unset, SPOEAgentPipelining]):
        processing_timeout (Union[Unset, int]):
        register_var_names (Union[Unset, str]):
        send_frag_payload (Union[Unset, SPOEAgentSendFragPayload]):
        use_backend (Union[Unset, str]):
    """

    name: str
    async_: Union[Unset, SPOEAgentAsync] = UNSET
    continue_on_error: Union[Unset, SPOEAgentContinueOnError] = UNSET
    dontlog_normal: Union[Unset, SPOEAgentDontlogNormal] = UNSET
    engine_name: Union[Unset, str] = UNSET
    force_set_var: Union[Unset, SPOEAgentForceSetVar] = UNSET
    groups: Union[Unset, str] = UNSET
    hello_timeout: Union[Unset, int] = UNSET
    idle_timeout: Union[Unset, int] = UNSET
    log: Union[Unset, list["LogTarget"]] = UNSET
    max_frame_size: Union[Unset, int] = UNSET
    max_waiting_frames: Union[Unset, int] = UNSET
    maxconnrate: Union[Unset, int] = UNSET
    maxerrrate: Union[Unset, int] = UNSET
    messages: Union[Unset, str] = UNSET
    option_set_on_error: Union[Unset, str] = UNSET
    option_set_process_time: Union[Unset, str] = UNSET
    option_set_total_time: Union[Unset, str] = UNSET
    option_var_prefix: Union[Unset, str] = UNSET
    pipelining: Union[Unset, SPOEAgentPipelining] = UNSET
    processing_timeout: Union[Unset, int] = UNSET
    register_var_names: Union[Unset, str] = UNSET
    send_frag_payload: Union[Unset, SPOEAgentSendFragPayload] = UNSET
    use_backend: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        async_: Union[Unset, str] = UNSET
        if not isinstance(self.async_, Unset):
            async_ = self.async_.value

        continue_on_error: Union[Unset, str] = UNSET
        if not isinstance(self.continue_on_error, Unset):
            continue_on_error = self.continue_on_error.value

        dontlog_normal: Union[Unset, str] = UNSET
        if not isinstance(self.dontlog_normal, Unset):
            dontlog_normal = self.dontlog_normal.value

        engine_name = self.engine_name

        force_set_var: Union[Unset, str] = UNSET
        if not isinstance(self.force_set_var, Unset):
            force_set_var = self.force_set_var.value

        groups = self.groups

        hello_timeout = self.hello_timeout

        idle_timeout = self.idle_timeout

        log: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.log, Unset):
            log = []
            for componentsschemaslog_targets_item_data in self.log:
                componentsschemaslog_targets_item = componentsschemaslog_targets_item_data.to_dict()
                log.append(componentsschemaslog_targets_item)

        max_frame_size = self.max_frame_size

        max_waiting_frames = self.max_waiting_frames

        maxconnrate = self.maxconnrate

        maxerrrate = self.maxerrrate

        messages = self.messages

        option_set_on_error = self.option_set_on_error

        option_set_process_time = self.option_set_process_time

        option_set_total_time = self.option_set_total_time

        option_var_prefix = self.option_var_prefix

        pipelining: Union[Unset, str] = UNSET
        if not isinstance(self.pipelining, Unset):
            pipelining = self.pipelining.value

        processing_timeout = self.processing_timeout

        register_var_names = self.register_var_names

        send_frag_payload: Union[Unset, str] = UNSET
        if not isinstance(self.send_frag_payload, Unset):
            send_frag_payload = self.send_frag_payload.value

        use_backend = self.use_backend

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if async_ is not UNSET:
            field_dict["async"] = async_
        if continue_on_error is not UNSET:
            field_dict["continue-on-error"] = continue_on_error
        if dontlog_normal is not UNSET:
            field_dict["dontlog-normal"] = dontlog_normal
        if engine_name is not UNSET:
            field_dict["engine-name"] = engine_name
        if force_set_var is not UNSET:
            field_dict["force-set-var"] = force_set_var
        if groups is not UNSET:
            field_dict["groups"] = groups
        if hello_timeout is not UNSET:
            field_dict["hello_timeout"] = hello_timeout
        if idle_timeout is not UNSET:
            field_dict["idle_timeout"] = idle_timeout
        if log is not UNSET:
            field_dict["log"] = log
        if max_frame_size is not UNSET:
            field_dict["max-frame-size"] = max_frame_size
        if max_waiting_frames is not UNSET:
            field_dict["max-waiting-frames"] = max_waiting_frames
        if maxconnrate is not UNSET:
            field_dict["maxconnrate"] = maxconnrate
        if maxerrrate is not UNSET:
            field_dict["maxerrrate"] = maxerrrate
        if messages is not UNSET:
            field_dict["messages"] = messages
        if option_set_on_error is not UNSET:
            field_dict["option_set-on-error"] = option_set_on_error
        if option_set_process_time is not UNSET:
            field_dict["option_set-process-time"] = option_set_process_time
        if option_set_total_time is not UNSET:
            field_dict["option_set-total-time"] = option_set_total_time
        if option_var_prefix is not UNSET:
            field_dict["option_var-prefix"] = option_var_prefix
        if pipelining is not UNSET:
            field_dict["pipelining"] = pipelining
        if processing_timeout is not UNSET:
            field_dict["processing_timeout"] = processing_timeout
        if register_var_names is not UNSET:
            field_dict["register-var-names"] = register_var_names
        if send_frag_payload is not UNSET:
            field_dict["send-frag-payload"] = send_frag_payload
        if use_backend is not UNSET:
            field_dict["use-backend"] = use_backend

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.log_target import LogTarget

        d = dict(src_dict)
        name = d.pop("name")

        _async_ = d.pop("async", UNSET)
        async_: Union[Unset, SPOEAgentAsync]
        if isinstance(_async_, Unset):
            async_ = UNSET
        else:
            async_ = SPOEAgentAsync(_async_)

        _continue_on_error = d.pop("continue-on-error", UNSET)
        continue_on_error: Union[Unset, SPOEAgentContinueOnError]
        if isinstance(_continue_on_error, Unset):
            continue_on_error = UNSET
        else:
            continue_on_error = SPOEAgentContinueOnError(_continue_on_error)

        _dontlog_normal = d.pop("dontlog-normal", UNSET)
        dontlog_normal: Union[Unset, SPOEAgentDontlogNormal]
        if isinstance(_dontlog_normal, Unset):
            dontlog_normal = UNSET
        else:
            dontlog_normal = SPOEAgentDontlogNormal(_dontlog_normal)

        engine_name = d.pop("engine-name", UNSET)

        _force_set_var = d.pop("force-set-var", UNSET)
        force_set_var: Union[Unset, SPOEAgentForceSetVar]
        if isinstance(_force_set_var, Unset):
            force_set_var = UNSET
        else:
            force_set_var = SPOEAgentForceSetVar(_force_set_var)

        groups = d.pop("groups", UNSET)

        hello_timeout = d.pop("hello_timeout", UNSET)

        idle_timeout = d.pop("idle_timeout", UNSET)

        _log = d.pop("log", UNSET)
        log: Union[Unset, list[LogTarget]] = UNSET
        if not isinstance(_log, Unset):
            log = []
            for componentsschemaslog_targets_item_data in _log:
                componentsschemaslog_targets_item = LogTarget.from_dict(componentsschemaslog_targets_item_data)

                log.append(componentsschemaslog_targets_item)

        max_frame_size = d.pop("max-frame-size", UNSET)

        max_waiting_frames = d.pop("max-waiting-frames", UNSET)

        maxconnrate = d.pop("maxconnrate", UNSET)

        maxerrrate = d.pop("maxerrrate", UNSET)

        messages = d.pop("messages", UNSET)

        option_set_on_error = d.pop("option_set-on-error", UNSET)

        option_set_process_time = d.pop("option_set-process-time", UNSET)

        option_set_total_time = d.pop("option_set-total-time", UNSET)

        option_var_prefix = d.pop("option_var-prefix", UNSET)

        _pipelining = d.pop("pipelining", UNSET)
        pipelining: Union[Unset, SPOEAgentPipelining]
        if isinstance(_pipelining, Unset):
            pipelining = UNSET
        else:
            pipelining = SPOEAgentPipelining(_pipelining)

        processing_timeout = d.pop("processing_timeout", UNSET)

        register_var_names = d.pop("register-var-names", UNSET)

        _send_frag_payload = d.pop("send-frag-payload", UNSET)
        send_frag_payload: Union[Unset, SPOEAgentSendFragPayload]
        if isinstance(_send_frag_payload, Unset):
            send_frag_payload = UNSET
        else:
            send_frag_payload = SPOEAgentSendFragPayload(_send_frag_payload)

        use_backend = d.pop("use-backend", UNSET)

        spoe_agent = cls(
            name=name,
            async_=async_,
            continue_on_error=continue_on_error,
            dontlog_normal=dontlog_normal,
            engine_name=engine_name,
            force_set_var=force_set_var,
            groups=groups,
            hello_timeout=hello_timeout,
            idle_timeout=idle_timeout,
            log=log,
            max_frame_size=max_frame_size,
            max_waiting_frames=max_waiting_frames,
            maxconnrate=maxconnrate,
            maxerrrate=maxerrrate,
            messages=messages,
            option_set_on_error=option_set_on_error,
            option_set_process_time=option_set_process_time,
            option_set_total_time=option_set_total_time,
            option_var_prefix=option_var_prefix,
            pipelining=pipelining,
            processing_timeout=processing_timeout,
            register_var_names=register_var_names,
            send_frag_payload=send_frag_payload,
            use_backend=use_backend,
        )

        spoe_agent.additional_properties = d
        return spoe_agent

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
