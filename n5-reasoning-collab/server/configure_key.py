"""Interactive, local-only credential setup. No network or browser credential input."""
import ctypes
import getpass
import os
from pathlib import Path
import tempfile
import warnings


def is_windows():
    return os.name == "nt"


def credential_path():
    location = os.environ.get("LOCALAPPDATA")
    if not location:
        raise OSError("LOCALAPPDATA is unavailable")
    return Path(location) / "N5AI" / "deepseek.key.dpapi"


def protect_key(key):
    """Use user-scoped DPAPI, matching the existing course credential format."""
    if not is_windows():
        raise OSError("DPAPI requires Windows")

    class DataBlob(ctypes.Structure):
        _fields_ = [("size", ctypes.c_ulong), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    raw = key.encode("utf-8")
    storage = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
    source, output = DataBlob(len(raw), storage), DataBlob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    crypt.CryptProtectData.argtypes = [
        ctypes.POINTER(DataBlob), ctypes.c_wchar_p, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(DataBlob)]
    crypt.CryptProtectData.restype = ctypes.c_int
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    try:
        # CRYPTPROTECT_UI_FORBIDDEN only. Do NOT set LOCAL_MACHINE:
        # the file must remain decryptable only by the same Windows user.
        if not crypt.CryptProtectData(ctypes.byref(source), None, None, None, None,
                                      1, ctypes.byref(output)):
            raise OSError("DPAPI encryption failed")
        try:
            return ctypes.string_at(output.data, output.size)
        finally:
            kernel.LocalFree(output.data)
    finally:
        ctypes.memset(storage, 0, len(raw))


def save_key(key, target):
    """Only encrypted bytes reach disk; replace atomically after a complete write."""
    encrypted = protect_key(key)
    if not encrypted:
        raise OSError("DPAPI returned an empty blob")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Store Python can redirect AppData to another volume. Resolve the existing
    # directory before creating BOTH paths, so the atomic rename stays on it.
    target = target.parent.resolve() / target.name
    descriptor, temporary = tempfile.mkstemp(prefix=".deepseek-", suffix=".dpapi", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encrypted)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    if not is_windows():
        print("此配置工具仅支持 Windows DPAPI。其他系统请在启动服务的终端设置 DEEPSEEK_API_KEY；不会保存明文文件。")
        return 1
    try:
        target = credential_path()
        if target.exists():
            answer = input("检测到已有本机凭据。输入 yes 覆盖，其他输入取消：")
            if answer.strip().lower() != "yes":
                print("已取消，原凭据未更改。")
                return 1
        with warnings.catch_warnings():
            # Never fall back to echoing a secret when no secure console exists.
            warnings.simplefilter("error", getpass.GetPassWarning)
            key = getpass.getpass("请输入 DeepSeek API Key（隐藏输入）：").strip()
        if not key or len(key) > 4096 or any(character.isspace() for character in key):
            print("凭据为空或包含无效空白，未保存。")
            return 1
        save_key(key, target)
        print("已使用当前 Windows 账户加密保存本机凭据。")
        print("返回本地服务版课件，点击“重新检测”即可启用真实运行。")
        if os.environ.get("DEEPSEEK_API_KEY", "").strip():
            print("提示：服务进程中的 DEEPSEEK_API_KEY 环境变量优先于本机加密文件。")
        return 0
    except (EOFError, KeyboardInterrupt):
        print("\n已取消，未保存新凭据。")
        return 1
    except getpass.GetPassWarning:
        print("当前终端不能隐藏输入，已停止。请双击 configure-deepseek.cmd 在本地控制台配置。")
        return 1
    except (OSError, UnicodeError):
        print("凭据未保存。请确认使用当前 Windows 账户，并且本机应用数据目录可写。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
