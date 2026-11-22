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
    def get_current_theme_state() -> Dict[str, Any]:
        """
        Queries Windows registry to check system theme, app theme, and active profile name.
        """
        sys_theme = "dark"
        apps_theme = "dark"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            sys_val, _ = winreg.QueryValueEx(key, "SystemUsesLightTheme")
            apps_val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            sys_theme = "light" if sys_val == 1 else "dark"
            apps_theme = "light" if apps_val == 1 else "dark"
        except Exception:
            pass

        # Classify overall profile
        if sys_theme == "dark" and apps_theme == "dark":
            profile_name = "Full Dark"
        elif sys_theme == "light" and apps_theme == "light":
            profile_name = "Full Light"
        elif sys_theme == "dark" and apps_theme == "light":
            profile_name = "Hybrid Focus"
        else:
            profile_name = "Custom"

        return {
            "system_theme": sys_theme,
            "apps_theme": apps_theme,
            "profile_name": profile_name,
            "is_dark": sys_theme == "dark"
        }

    @staticmethod
    def get_current_theme() -> str:
        """
        Returns 'dark' or 'light' for simple checks based on System mode.
        """
        return ThemeEngine.get_current_theme_state()["system_theme"]

    @classmethod
    def _broadcast_change(cls):
        """
        Broadcasts WM_SETTINGCHANGE to all top-level windows without blocking.
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
    def _fallback_registry_switch(cls, system_theme: str, apps_theme: str) -> bool:
        """
        Defensive Fallback: Directly writes registry keys and notifies Windows shell.
        Ensures switches succeed even if IThemeManager2 COM interface is blocked or missing.
        """
        try:
            sys_val = 1 if system_theme == "light" else 0
            apps_val = 1 if apps_theme == "light" else 0

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, sys_val)
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, apps_val)
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
    def apply_profile(cls, profile_name: str, trigger_source: str = "manual") -> bool:
        """
        Applies a named profile ("Full Dark", "Full Light", "Hybrid Focus", or custom).
        Uses COM VTable dispatch when applicable and gracefully falls back to registry broadcast.
        """
        start_time = time.perf_counter()
        profile_data = Repository.get_profile_by_name(profile_name)

        if not profile_data:
            # Fallback for simple "dark" / "light" string names
            if profile_name.lower() in ("dark", "full dark"):
                sys_t, app_t = "dark", "dark"
                p_name = "Full Dark"
                p_id = 1
            elif profile_name.lower() in ("light", "full light"):
                sys_t, app_t = "light", "light"
                p_name = "Full Light"
                p_id = 2
            elif "hybrid" in profile_name.lower():
                sys_t, app_t = "dark", "light"
                p_name = "Hybrid Focus"
                p_id = 3
            else:
                return False
        else:
            sys_t = profile_data["system_theme"]
            app_t = profile_data["apps_theme"]
            p_name = profile_data["name"]
            p_id = profile_data["id"]

        success = False
        method_used = "COM_VTABLE"

        # If system == apps (Full Dark / Full Light), attempt COM dispatch first
        if sys_t == app_t:
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
                    target_idx = dark_idx if sys_t == "dark" else light_idx
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

        # Fallback or Hybrid switch: execute via registry write + broadcast
        if not success:
            method_used = "REGISTRY_FALLBACK" if sys_t == app_t else "HYBRID_SPLIT"
            success = cls._fallback_registry_switch(sys_t, app_t)

        duration_ms = (time.perf_counter() - start_time) * 1000
        status = "SUCCESS" if success else "FAILED"
        Repository.log_switch(
            switched_to=p_name,
            trigger_source=f"{trigger_source}:{method_used}",
            duration_ms=duration_ms,
            status=status,
            profile_id=p_id
        )
        return success

    @classmethod
    def set_theme(cls, target_theme: str, trigger_source: str = "manual") -> bool:
        """
        Backwards compatibility alias for apply_profile.
        """
        target_theme = target_theme.lower()
        if target_theme == "dark":
            return cls.apply_profile("Full Dark", trigger_source)
        elif target_theme == "light":
            return cls.apply_profile("Full Light", trigger_source)
        elif target_theme == "hybrid":
            return cls.apply_profile("Hybrid Focus", trigger_source)
        else:
            return cls.apply_profile(target_theme, trigger_source)

    @classmethod
    def toggle(cls, trigger_source: str = "manual") -> str:
        """
        Toggles between Full Dark and Full Light (or cycles profiles).
        """
        state = cls.get_current_theme_state()
        if state["is_dark"]:
            cls.apply_profile("Full Light", trigger_source)
            return "light"
        else:
            cls.apply_profile("Full Dark", trigger_source)
            return "dark"
