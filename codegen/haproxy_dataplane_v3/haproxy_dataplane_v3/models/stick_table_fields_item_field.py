from enum import Enum


class StickTableFieldsItemField(str, Enum):
    BYTES_IN_CNT = "bytes_in_cnt"
    BYTES_IN_RATE = "bytes_in_rate"
    BYTES_OUT_CNT = "bytes_out_cnt"
    BYTES_OUT_RATE = "bytes_out_rate"
    CONN_CNT = "conn_cnt"
    CONN_CUR = "conn_cur"
    CONN_RATE = "conn_rate"
    GLITCH_CNT = "glitch_cnt"
    GLITCH_RATE = "glitch_rate"
    GPC0 = "gpc0"
    GPC0_RATE = "gpc0_rate"
    GPC1 = "gpc1"
    GPC1_RATE = "gpc1_rate"
    GPT0 = "gpt0"
    HTTP_ERR_CNT = "http_err_cnt"
    HTTP_ERR_RATE = "http_err_rate"
    HTTP_REQ_CNT = "http_req_cnt"
    HTTP_REQ_RATE = "http_req_rate"
    SERVER_ID = "server_id"
    SESS_CNT = "sess_cnt"
    SESS_RATE = "sess_rate"

    def __str__(self) -> str:
        return str(self.value)
