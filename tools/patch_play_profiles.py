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

# Instrument only the CI homebrew boot: confirm the pinned Play! core really
# loads and resumes a guest ELF, rather than merely opening an idle Qt window.
mainwindow = Path(sys.argv[1]) / "Source/ui_qt/mainwindow.cpp"
window_text = mainwindow.read_text(encoding="utf-8")
boot_anchor = "void MainWindow::BootElf(fs::path filePath)\n{\n\\tm_virtualMachine->Pause();\n\\tm_virtualMachine->Reset();\n\\tm_virtualMachine->m_ee->m_os->BootFromFile(filePath);\n#ifndef DEBUGGER_INCLUDED\n\\tm_virtualMachine->Resume();\n#endif\n"
if window_text.count(boot_anchor) != 1:
    raise SystemExit("Unexpected upstream ELF boot anchor")
boot_report = r'''
    // Only active if a CI runner explicitly supplies a local marker path.
    auto studioBootReportPath = qgetenv("PS2STUDIO_CI_ELF_MARKER");
    if(!studioBootReportPath.isEmpty())
    {
        QFile studioBootReport(QString::fromLocal8Bit(studioBootReportPath));
        if(studioBootReport.open(QIODevice::WriteOnly | QIODevice::Truncate))
        {
            studioBootReport.write("BOOT_ELF_LOADED_AND_VM_RESUMED\n");
            studioBootReport.flush();
        }
    }
'''
window_text = window_text.replace(boot_anchor, boot_anchor + boot_report)
window_text = window_text.replace("#include <QFileDialog>", "#include <QFile>\n#include <QFileDialog>", 1)
mainwindow.write_text(window_text, encoding="utf-8")

