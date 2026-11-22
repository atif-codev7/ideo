import ctypes
from ctypes import wintypes
import time
import winreg
from typing import Tuple, Optional, Dict, Any
from database.repository import Repository

ole32 = ctypes.windll.ole32
oleaut32 = ctypes.windll.oleaut32
user32 = ctypes.windll.user32

HWND_BROADCAST = 0xFFFF
WM_SETTINGCHANGE = 0x001A
SMTO_ABORTIFHUNG = 0x0002

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
    def _broadcast_change(cls):
        """
        Broadcasts WM_SETTINGCHANGE to top-level windows.
        """
        res = ctypes.c_ulong()
        user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            "ImmersiveColorSet",
            SMTO_ABORTIFHUNG,
            1000,
            ctypes.byref(res)
        )

    @classmethod
    def _fallback_registry_switch(cls, target_theme: str) -> bool:
        """
        Defensive Fallback: Directly writes registry keys and notifies Windows shell.
        """
        try:
            val = 1 if target_theme == "light" else 0
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, val)
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, val)
            winreg.CloseKey(key)

            cls._broadcast_change()
            return True
        except Exception:
            return False

    @classmethod
    def _get_theme_indices(cls, p_mgr) -> Tuple[int, int]:
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
    def set_theme(cls, target_theme: str, trigger_source: str = "manual", profile_id: Optional[int] = None) -> bool:
        """
        Directly sets the Windows 11 theme to 'dark' or 'light'.
        Uses low-level COM VTable dispatch with automatic defensive fallback to registry.
        """
        start_time = time.perf_counter()
        target_theme = target_theme.lower()
        if target_theme not in ("dark", "light"):
            raise ValueError("Target theme must be 'dark' or 'light'")

        success = False
        method_used = "COM_VTABLE"

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
            if hr == 0 and p_mgr:
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
                    # Flags: 1 = IgnoreBackground (keep wallpaper), 256 = NoHourglass
                    SetCurrentThemeFunc(p_mgr, None, target_idx, 1, 1 | 256, 0)
                    success = True
        except Exception:
            success = False
        finally:
            if p_mgr:
                vt = _get_vtable(p_mgr)
                ReleaseMgr = ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(vt[2])
                ReleaseMgr(p_mgr)
            ole32.CoUninitialize()

        # Defensive Fallback: If COM failed, execute registry switch
        if not success:
            method_used = "REGISTRY_FALLBACK"
            success = cls._fallback_registry_switch(target_theme)

        duration_ms = (time.perf_counter() - start_time) * 1000
        status = "SUCCESS" if success else "FAILED"

        # Resolve profile_id if not given
        if profile_id is None:
            p_name = "Dark Mode" if target_theme == "dark" else "Light Mode"
            p = Repository.get_profile_by_name(p_name)
            if p:
                profile_id = p["id"]

        Repository.log_switch(
            switched_to=target_theme,
            trigger_source=f"{trigger_source}:{method_used}",
            duration_ms=duration_ms,
            status=status,
            profile_id=profile_id
        )
        return success

    @classmethod
    def apply_profile(cls, profile_name: str, trigger_source: str = "manual") -> bool:
        """
        Applies a named profile ("Dark Mode", "Light Mode", etc.).
        """
        profile = Repository.get_profile_by_name(profile_name)
        if profile:
            return cls.set_theme(profile["base_theme"], trigger_source=trigger_source, profile_id=profile["id"])

        # Fallback if raw theme string passed
        clean_name = profile_name.lower()
        if "dark" in clean_name:
            return cls.set_theme("dark", trigger_source=trigger_source)
        elif "light" in clean_name:
            return cls.set_theme("light", trigger_source=trigger_source)
        return False

    @classmethod
    def toggle(cls, trigger_source: str = "manual") -> str:
        """
        Toggles current theme and returns new theme ('dark' or 'light').
        """
        current = cls.get_current_theme()
        target = "light" if current == "dark" else "dark"
        success = cls.set_theme(target, trigger_source=trigger_source)
        return target if success else current
