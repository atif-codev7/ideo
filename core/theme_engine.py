import ctypes
from ctypes import wintypes
import time
import winreg
from typing import Tuple, Optional
from database.repository import Repository

ole32 = ctypes.windll.ole32
oleaut32 = ctypes.windll.oleaut32

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8)
    ]

    @classmethod
    def from_str(cls, s: str):
        guid = cls()
        ole32.CLSIDFromString(ctypes.c_wchar_p(s), ctypes.byref(guid))
        return guid

CLSID_ThemeManager = GUID.from_str("{9324da94-50ec-4a14-a770-e90ca03e7c8f}")
IID_IThemeManager2 = GUID.from_str("{c1e8c83e-845d-4d95-81db-e283fdffc000}")

def _get_vtable(ptr):
    return ctypes.cast(ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents

class ThemeEngine:
    @staticmethod
    def get_current_theme() -> str:
        """
        Queries Windows registry to check if current theme is light or dark.
        Returns: 'light' or 'dark'
        """
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            val, _ = winreg.QueryValueEx(key, "SystemUsesLightTheme")
            winreg.CloseKey(key)
            return "light" if val == 1 else "dark"
        except Exception:
            return "dark"

    @classmethod
    def _get_theme_indices(cls, p_mgr) -> Tuple[int, int]:
        """
        Scans themes via IThemeManager2 and returns (dark_index, light_index).
        """
        vt = _get_vtable(p_mgr)
        InitFunc = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, wintypes.DWORD)(vt[3])
        GetThemeCountFunc = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD))(vt[8])
        GetThemeFunc = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p))(vt[9])

        InitFunc(p_mgr, 0)
        count = wintypes.DWORD()
        GetThemeCountFunc(p_mgr, ctypes.byref(count))

        dark_idx = -1
        light_idx = -1

        for i in range(count.value):
            p_theme = ctypes.c_void_p()
            if GetThemeFunc(p_mgr, i, ctypes.byref(p_theme)) == 0 and p_theme:
                t_vt = _get_vtable(p_theme)
                GetDisplayNameFunc = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, ctypes.POINTER(ctypes.c_wchar_p))(t_vt[3])
                name_ptr = ctypes.c_wchar_p()
                GetDisplayNameFunc(p_theme, ctypes.byref(name_ptr))
                name = (name_ptr.value or "").lower()
                oleaut32.SysFreeString(name_ptr)

                ReleaseFunc = ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(t_vt[2])
                ReleaseFunc(p_theme)

                if "dark" in name:
                    dark_idx = i
                elif "light" in name or name == "windows":
                    if light_idx == -1:
                        light_idx = i

        return dark_idx, light_idx

    @classmethod
    def set_theme(cls, target_theme: str, trigger_source: str = "manual") -> bool:
        """
        Directly sets the Windows 11 theme to 'dark' or 'light'.
        Tracks latency and writes an audit log to SQLite.
        """
        start_time = time.perf_counter()
        target_theme = target_theme.lower()
        if target_theme not in ("dark", "light"):
            raise ValueError("Target theme must be 'dark' or 'light'")

        current = cls.get_current_theme()
        if current == target_theme:
            # Already in desired theme, log and return
            duration_ms = (time.perf_counter() - start_time) * 1000
            Repository.log_switch(target_theme, trigger_source, duration_ms, "SUCCESS")
            return True

        ole32.CoInitialize(None)
        p_mgr = ctypes.c_void_p()
        try:
            hr = ole32.CoCreateInstance(
                ctypes.byref(CLSID_ThemeManager),
                None,
                0x17,  # CLSCTX_ALL
                ctypes.byref(IID_IThemeManager2),
                ctypes.byref(p_mgr)
            )
            if hr != 0 or not p_mgr:
                duration_ms = (time.perf_counter() - start_time) * 1000
                Repository.log_switch(target_theme, trigger_source, duration_ms, "FAILED")
                return False

            dark_idx, light_idx = cls._get_theme_indices(p_mgr)
            target_idx = dark_idx if target_theme == "dark" else light_idx

            if target_idx >= 0:
                vt = _get_vtable(p_mgr)
                SetCurrentThemeFunc = ctypes.WINFUNCTYPE(
                    ctypes.HRESULT,
                    ctypes.c_void_p,
                    wintypes.HWND,
                    wintypes.DWORD,
                    wintypes.DWORD,
                    wintypes.DWORD,
                    wintypes.DWORD
                )(vt[12])
                # Flags: 1 = IgnoreBackground (preserve user wallpaper), 256 = NoHourglass
                SetCurrentThemeFunc(p_mgr, None, target_idx, 1, 1 | 256, 0)
                duration_ms = (time.perf_counter() - start_time) * 1000
                Repository.log_switch(target_theme, trigger_source, duration_ms, "SUCCESS")
                return True
            else:
                duration_ms = (time.perf_counter() - start_time) * 1000
                Repository.log_switch(target_theme, trigger_source, duration_ms, "FAILED")
                return False
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            Repository.log_switch(target_theme, trigger_source, duration_ms, f"ERROR: {str(e)[:15]}")
            return False
        finally:
            if p_mgr:
                vt = _get_vtable(p_mgr)
                ReleaseMgr = ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(vt[2])
                ReleaseMgr(p_mgr)
            ole32.CoUninitialize()

    @classmethod
    def toggle(cls, trigger_source: str = "manual") -> str:
        """
        Toggles current theme and returns new theme ('dark' or 'light').
        """
        current = cls.get_current_theme()
        target = "light" if current == "dark" else "dark"
        success = cls.set_theme(target, trigger_source)
        return target if success else current
