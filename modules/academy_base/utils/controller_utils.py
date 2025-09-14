from odoo.http import request, Response
import json
from odoo.tools import date_utils


def _delete_debug_information(error):
    if error and isinstance(error, dict) and "data" in error:
        if error["data"] and isinstance(error["data"], dict):
            if "debug" in error["data"]:
                del error["data"]["debug"]

    return False


def _update_error_code(error):
    if error and isinstance(error, dict) and "code" in error:
        if error["code"] == 200:
            error["code"] = -32603


def _patched_json_response(self, result=None, error=None):
    response = {"jsonrpc": "2.0", "id": self.jsonrequest.get("id")}

    if error is not None:
        _delete_debug_information(error)
        _update_error_code(error)
        response["error"] = error
    if result is not None:
        response["result"] = result

    mime = "application/json"
    body = json.dumps(response, default=date_utils.json_default)

    return Response(
        body,
        status=error and error.pop("http_status", 200) or 200,
        headers=[("Content-Type", mime), ("Content-Length", len(body))],
    )


def patch_json_response():
    request._json_response = _patched_json_response.__get__(request, object)


def make_json_response(
    data_dict, request_id=None, message=None, error_code=None, status_code=200
):
    return data_dict
