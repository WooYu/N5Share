"""Strict JSON action client; credentials never enter public state or exceptions."""
import ctypes
import json
import os
from pathlib import Path

MODEL = "deepseek-flash"
ENDPOINT = "https://api.deepseek.com/chat/completions"


class ModelError(Exception):
    pass


def load_key():
    candidate = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if candidate:
        return candidate
    location = os.environ.get("LOCALAPPDATA")
    if os.name != "nt" or not location:
        return None
    path = Path(location) / "N5AI" / "deepseek.key.dpapi"
    if not path.is_file():
        return None
    encrypted = path.read_bytes()
    if not encrypted or len(encrypted) > 65536:
        raise ModelError("本机凭据文件无效，请重新配置。")

    class DataBlob(ctypes.Structure):
        _fields_ = [("size", ctypes.c_ulong), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    storage = (ctypes.c_ubyte * len(encrypted)).from_buffer_copy(encrypted)
    source = DataBlob(len(encrypted), storage)
    output = DataBlob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    crypt.CryptUnprotectData.argtypes = [ctypes.POINTER(DataBlob), ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(DataBlob)]
    crypt.CryptUnprotectData.restype = ctypes.c_int
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if not crypt.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output)):
        raise ModelError("无法解密本机凭据，请用同一 Windows 账户重新配置。")
    try:
        key = ctypes.string_at(output.data, output.size).decode("utf-8").strip()
        if not key:
            raise ModelError("本机凭据为空。")
        return key
    finally:
        kernel.LocalFree(output.data)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON property")
        result[key] = value
    return result


def parse_json(raw):
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("invalid JSON number")))


def validate_action(value):
    keys = {"summary", "calls", "plan", "reflection", "next_actor", "result"}
    if not isinstance(value, dict) or set(value) != keys:
        raise ModelError("模型输出必须只包含 summary/calls/plan/reflection/next_actor/result。")
    for field in ("summary", "reflection", "next_actor"):
        if not isinstance(value[field], str) or len(value[field]) > (120 if field == "next_actor" else 1200):
            raise ModelError("模型摘要、反思或角色字段无效。")
    if not value["summary"].strip():
        raise ModelError("模型必须提供简短公开决策摘要。")
    if not isinstance(value["plan"], list) or len(value["plan"]) > 12 or any(
            not isinstance(item, str) or not item.strip() or len(item) > 240 for item in value["plan"]):
        raise ModelError("模型计划结构无效。")
    if not isinstance(value["calls"], list) or len(value["calls"]) > 6:
        raise ModelError("单次模型输出最多六个工具请求。")
    for call in value["calls"]:
        if not isinstance(call, dict) or set(call) != {"name", "arguments"} or not isinstance(
                call["name"], str) or not isinstance(call["arguments"], dict):
            raise ModelError("工具请求结构无效。")
    result = value["result"]
    if result is not None:
        if not isinstance(result, dict):
            raise ModelError("模型 result 必须为对象或 null。")
        status = result.get("status")
        expected = {"completed": {"status", "venue", "total"},
                    "candidate": {"status", "venue"},
                    "needs_human": {"status"}, "report": {"status", "findings", "revision"},
                    "arbitrated": {"status", "resolutions"}, "review_passed": {"status"}}
        if status not in expected or set(result) != expected[status]:
            raise ModelError("模型 result 状态或字段不符合契约。")
        if status == "completed" and (not isinstance(result["venue"], str) or
                type(result["total"]) is not int or result["total"] < 0):
            raise ModelError("场馆与费用必须是确定类型。")
        if status == "candidate" and result["venue"] not in ("P01", "P02", "P03", "P04"):
            raise ModelError("候选场馆编号无效。")
        if status == "report" and (type(result["revision"]) is not int or
                not isinstance(result["findings"], list) or len(result["findings"]) > 12 or
                any(not isinstance(item, str) for item in result["findings"])):
            raise ModelError("审查报告字段无效。")
        if status == "arbitrated" and (not isinstance(result["resolutions"], dict) or
                any(not isinstance(k, str) or not isinstance(v, str) for k, v in result["resolutions"].items())):
            raise ModelError("仲裁决议字段无效。")
    return value


SYSTEM = """你是 N5 课程本地模拟系统中的一个角色。仅返回 JSON 对象，不使用 Markdown。
所有工具只读取课程合成资料。不得伪造 Observation，不得把建议当作已执行结果。
summary 是供学员阅读的简短决策摘要（最多两句），不要输出思维链或隐藏推理。
必须且只能输出六个字段：summary 字符串，calls 数组（每项只有 name 和 arguments），
plan 字符串数组，reflection 字符串，next_actor 字符串，result 对象或 null。
只可使用当前角色允许的工具和本阶段规定的交接角色。工具按 calls 数组顺序由宿主执行。
next_actor 必须逐字复制用户 JSON 中 expected_next_actor 的值，包括空字符串 ""。
expected_next_actor="" 表示本轮没有角色交接；此时 next_actor 也必须是 ""，
不可填当前 actor、host、supervisor、end 或 null。非空时同样必须原样复制，不得自行改换接收角色。
费用与场馆以宿主观察为准，验收由宿主检查。不要在 result 中输出观察或擅自写共享状态。
result 可用结构：候选 {status:'candidate',venue:'P03'}；完成出游 {status:'completed',venue:'P03',total:210}；无可行方案 {status:'needs_human'}；
代码报告 {status:'report',findings:['F-AUTHZ'],revision:0}；仲裁 {status:'arbitrated',resolutions:{...}}；
代码最终通过 {status:'review_passed'}。以上单引号只是结构说明，实际必须标准 JSON 双引号。
本课程场馆：P01 城市公园120元；P02 植物园270元；P03 科技馆210元；P04 美术馆200元。
雨天只能室内。优先科技馆，预算不足选美术馆；晴天按任务计划选，预算不足可选城市公园。
若本阶段仅要求读取资料或调用工具，result 使用 null。"""


class DeepSeekClient:
    def __init__(self, key):
        self.key = key

    async def complete(self, context):
        import httpx
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(65, connect=12),
                                         follow_redirects=False, trust_env=False) as client:
                response = await client.post(ENDPOINT, headers={"Authorization": "Bearer " + self.key},
                    json={"model": MODEL, "thinking": {"type": "disabled"},
                          "response_format": {"type": "json_object"}, "max_tokens": 2200,
                          "messages": [{"role": "system", "content": SYSTEM},
                                       {"role": "user", "content": json.dumps(context, ensure_ascii=False)}]})
                if response.status_code != 200:
                    raise ModelError("DeepSeek 请求失败（HTTP %s），本次运行已停止。" % response.status_code)
                if len(response.content) > 262144:
                    raise ModelError("模型响应过大，已停止。")
                envelope = response.json()
                choice = envelope["choices"][0]
                if choice.get("finish_reason") != "stop":
                    raise ModelError("模型未完整结束结构化响应。")
                action = validate_action(parse_json(choice["message"]["content"]))
                usage = envelope.get("usage", {})
                counts = {"input_tokens": usage.get("prompt_tokens", 0),
                          "output_tokens": usage.get("completion_tokens", 0)}
                if any(type(v) is not int or v < 0 for v in counts.values()):
                    raise ModelError("模型计费统计字段无效。")
                return action, counts
        except ModelError:
            raise
        except (KeyError, IndexError, TypeError, ValueError):
            raise ModelError("DeepSeek 返回了无效或非结构化响应。") from None
        except httpx.HTTPError:
            raise ModelError("DeepSeek 网络连接失败或超时；未回退为离线剧本。") from None
