"""Apply a narrowly scoped profile hook to the pinned upstream source."""
from pathlib import Path
import sys

source = Path(sys.argv[1]) / "Source/ui_qt/mainwindow.cpp"
text = source.read_text(encoding="utf-8")
anchor = "\tRegisterPreferences();\n"
if text.count(anchor) != 1:
    raise SystemExit("Unexpected upstream preferences anchor")
hook = r'''
    // PS2 Studio: explicit startup profile, before status UI and GS creation.
    auto studioRenderer = qgetenv("PS2STUDIO_RENDERER");
    if(studioRenderer == "opengl" || studioRenderer == "vulkan")
    {
        auto& studioConfig = CAppConfig::GetInstance();
        CGSH_OpenGL::RegisterPreferences();
        auto studioScale = qgetenv("PS2STUDIO_RESOLUTION").toInt();
        if(studioScale == 1 || studioScale == 2 || studioScale == 4 || studioScale == 8)
        {
            studioConfig.SetPreferenceInteger(PREF_CGSH_OPENGL_RESOLUTION_FACTOR, studioScale);
        }
        studioConfig.SetPreferenceInteger(PREF_VIDEO_GS_HANDLER, SettingsDialog::GS_HANDLERS::OPENGL);
#ifdef HAS_GSH_VULKAN
        if(studioRenderer == "vulkan" && GSH_Vulkan::CDeviceInfo::GetInstance().HasAvailableDevices())
        {
            studioConfig.SetPreferenceInteger(PREF_VIDEO_GS_HANDLER, SettingsDialog::GS_HANDLERS::VULKAN);
        }
#endif
        // Explicit selection must not silently claim Vulkan if the device is absent.
        if(studioRenderer == "vulkan" && studioConfig.GetPreferenceInteger(PREF_VIDEO_GS_HANDLER) == SettingsDialog::GS_HANDLERS::OPENGL)
        {
            QMessageBox::critical(nullptr, "PS2 Studio", "No compatible Vulkan device. Select OpenGL.");
            qFatal("PS2 Studio: requested Vulkan device unavailable");
        }
    }
'''
source.write_text(text.replace(anchor, anchor + hook), encoding="utf-8")
