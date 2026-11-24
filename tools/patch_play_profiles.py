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
boot_anchor = "void MainWindow::BootElf(fs::path filePath)\n{\n\tm_virtualMachine->Pause();\n\tm_virtualMachine->Reset();\n\tm_virtualMachine->m_ee->m_os->BootFromFile(filePath);\n#ifndef DEBUGGER_INCLUDED\n\tm_virtualMachine->Resume();\n#endif\n"
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
# The Qt status bar already reads real guest GS flips once per second via
# CStatsManager::GetFrames(). Export these values for a CI-only timing report.
stats_anchor = "\tCStatsManager::GetInstance().ClearStats();\n"
if window_text.count(stats_anchor) != 1:
    raise SystemExit("Unexpected upstream frame stats anchor")
stats_hook = r'''
    auto studioStatsPath = qgetenv("PS2STUDIO_CI_STATS_FILE");
    if(!studioStatsPath.isEmpty())
    {
        QFile studioStats(QString::fromLocal8Bit(studioStatsPath));
        if(studioStats.open(QIODevice::WriteOnly | QIODevice::Append | QIODevice::Text))
        {
            studioStats.write(QString("%1\t%2\n").arg(frames).arg(dcpf).toUtf8());
        }
    }
'''
window_text = window_text.replace(stats_anchor, stats_hook + stats_anchor)
mainwindow.write_text(window_text, encoding="utf-8")


# The pinned OpenGL GetScreenshot() returns an empty bitmap (#if 0).
# Capture the actual composed guest output immediately before PresentBackbuffer.
# Enabled only by an explicit CI environment path, never during normal gameplay.
gl_source = Path(sys.argv[1]) / "Source/gs/GSH_OpenGL/GSH_OpenGL.cpp"
gl_text = gl_source.read_text(encoding="utf-8")
gl_include = '#include "GSH_OpenGL.h"'
if gl_text.count(gl_include) != 1:
    raise SystemExit("Unexpected OpenGL include anchor")
gl_text = gl_text.replace(gl_include, gl_include + '\n#include "bitmap/BMP.h"\n#include "StdStream.h"\n#include <cstdlib>', 1)
flip_anchor = "\tPresentBackbuffer();\n\tCGSHandler::FlipImpl(dispInfo);"
if gl_text.count(flip_anchor) != 1:
    raise SystemExit("Unexpected OpenGL flip anchor")
capture = r'''
#ifndef GLES_COMPATIBILITY
    // Test the real OpenGL presentation framebuffer before swapping buffers.
    static const char* studioFramePath = std::getenv("PS2STUDIO_CI_FRAME_PATH");
    static unsigned int studioVisibleFlips = 0;
    static bool studioCaptured = false;
    if(studioFramePath && *studioFramePath && framebuffer && !studioCaptured)
    {
        if(++studioVisibleFlips >= 120)
        {
            const auto width = m_presentationParams.windowWidth;
            const auto height = m_presentationParams.windowHeight;
            if(width >= 128 && height >= 128 && width <= 4096 && height <= 4096)
            {
                try
                {
                    glBindFramebuffer(GL_FRAMEBUFFER, m_presentFramebuffer);
                    auto bitmap = Framework::CBitmap(width, height, 32);
                    glReadPixels(0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, bitmap.GetPixels());
                    if(glGetError() == GL_NO_ERROR)
                    {
                        Framework::CStdStream stream(studioFramePath, "wb");
                        Framework::CBMP::WriteBitmap(bitmap, stream);
                        studioCaptured = true;
                    }
                }
                catch(const std::exception&)
                {
                    // CI will fail if a valid screenshot is not produced.
                }
            }
        }
    }
#endif
'''
gl_text = gl_text.replace(flip_anchor, capture + flip_anchor, 1)
gl_source.write_text(gl_text, encoding="utf-8")
