"""User-scoped DPAPI credential storage, outside the course and its package."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path


def credential_path():
    return Path(os.environ.get('LOCALAPPDATA', Path.home() / '.local' / 'share')) / 'N5AI' / 'deepseek.key.dpapi'


def _crypt(data, protect):
    if os.name != 'nt':
        raise OSError('DPAPI storage requires Windows; use DEEPSEEK_API_KEY on other systems.')

    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]

    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    operation = crypt.CryptProtectData if protect else crypt.CryptUnprotectData
    operation.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob), ctypes.c_void_p,
                          ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    operation.restype = wintypes.BOOL
    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    source = Blob(len(data), buffer)
    output = Blob()
    if not operation(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output)):
        raise OSError('Windows credential protection failed.')
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        kernel.LocalFree(output.data)


def save_deepseek_key(key, path=None):
    if not isinstance(key, str) or not key.strip():
        raise ValueError('Empty credential')
    target = Path(path) if path else credential_path()
    encrypted = _crypt(key.strip().encode('utf-8'), True)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(encrypted)
    return target


def load_deepseek_key(path=None):
    if path is None and os.environ.get('DEEPSEEK_API_KEY', '').strip():
        return os.environ['DEEPSEEK_API_KEY'].strip()
    target = Path(path) if path else credential_path()
    if not target.is_file():
        return None
    return _crypt(target.read_bytes(), False).decode('utf-8')
