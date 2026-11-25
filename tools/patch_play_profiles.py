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


# Instrument real GS presentation, independent of the disabled GetScreenshot API.
# Diagnostics are opt-in: no per-frame I/O for normal gameplay.
gl_source = Path(sys.argv[1]) / "Source/gs/GSH_OpenGL/GSH_OpenGL.cpp"
gl_text = gl_source.read_text(encoding="utf-8")
gl_include = '#include "GSH_OpenGL.h"'
if gl_text.count(gl_include) != 1:
    raise SystemExit("Unexpected OpenGL include anchor")
gl_text = gl_text.replace(gl_include, gl_include + '\n#include <cstdlib>\n#include <fstream>\n#include <chrono>\n#include <vector>\n#include <cstdint>', 1)
flip_anchor = "\tPresentBackbuffer();\n\tCGSHandler::FlipImpl(dispInfo);"
if gl_text.count(flip_anchor) != 1:
    raise SystemExit("Unexpected OpenGL flip anchor")
capture = r'''
#ifndef GLES_COMPATIBILITY
    static const char* studioFramePath = std::getenv("PS2STUDIO_CI_FRAME_PATH");
    if(studioFramePath && *studioFramePath)
    {
        using StudioClock = std::chrono::steady_clock;
        static const auto studioStart = StudioClock::now();
        static unsigned int studioFlips = 0;
        static bool studioCaptured = false;
        static std::ofstream studioLog(std::string(studioFramePath) + ".log");
        static std::ofstream studioTiming(std::string(studioFramePath) + ".flips.tsv");
        const auto studioUs = std::chrono::duration_cast<std::chrono::microseconds>(StudioClock::now() - studioStart).count();
        const auto width = m_presentationParams.windowWidth;
        const auto height = m_presentationParams.windowHeight;
        ++studioFlips;
        studioTiming << studioUs << '\t' << (framebuffer ? 1 : 0) << '\t' << m_fbScale << '\n';
        studioTiming.flush();
        if(studioFlips <= 10 || studioFlips % 30 == 0)
        {
            const auto renderer = glGetString(GL_RENDERER);
            studioLog << "flip=" << studioFlips << " layer_enabled=" << dispLayer.enabled
                      << " guest_buffer=" << bool(framebuffer) << " scale=" << m_fbScale
                      << " output=" << width << "x" << height << " guest=" << dispLayer.width
                      << "x" << dispLayer.height << " renderer="
                      << (renderer ? reinterpret_cast<const char*>(renderer) : "unavailable") << std::endl;
            studioTiming.flush();
        }
        // Keep evidence even if black. Try early and periodically to avoid
        // assuming a particular guest generates 120 display flips.
        if(!studioCaptured && framebuffer && width >= 128 && height >= 128 &&
           width <= 4096 && height <= 4096 && (studioFlips <= 10 || studioFlips % 30 == 0))
        {
            try
            {
                glBindFramebuffer(GL_FRAMEBUFFER, m_presentFramebuffer);
                for(unsigned int i = 0; i < 8; i++) { if(glGetError() == GL_NO_ERROR) break; }
                std::vector<unsigned char> rgba(size_t(width) * height * 4);
                glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, rgba.data());
                const auto error = glGetError();
                studioLog << "readback=" << error << " flip=" << studioFlips << std::endl;
                if(error == GL_NO_ERROR)
                {
                    // Write standard 24-bit bottom-up BMP ourselves, so a
                    // framework screenshot writer cannot silently discard it.
                    const uint32_t stride = (uint32_t(width) * 3 + 3) & ~uint32_t(3);
                    const uint32_t dataSize = stride * uint32_t(height);
                    unsigned char header[54] = {};
                    auto put32 = [&](unsigned int off, uint32_t value) {
                        for(unsigned int i = 0; i < 4; ++i) header[off+i] = (value >> (8*i)) & 255;
                    };
                    header[0] = 'B'; header[1] = 'M';
                    put32(2, 54 + dataSize); put32(10, 54); put32(14, 40);
                    put32(18, width); put32(22, height);
                    header[26] = 1; header[28] = 24; put32(34, dataSize);
                    std::ofstream bmp(studioFramePath, std::ios::binary | std::ios::trunc);
                    bmp.write(reinterpret_cast<const char*>(header), sizeof(header));
                    std::vector<unsigned char> row(stride, 0);
                    unsigned int lit = 0;
                    for(unsigned int y = 0; y < height; ++y)
                    {
                        for(unsigned int x = 0; x < width; ++x)
                        {
                            const auto src = (size_t(y) * width + x) * 4;
                            row[3*x] = rgba[src+2]; row[3*x+1] = rgba[src+1]; row[3*x+2] = rgba[src];
                            if(unsigned(rgba[src])+rgba[src+1]+rgba[src+2] > 75) ++lit;
                        }
                        bmp.write(reinterpret_cast<const char*>(row.data()), row.size());
                    }
                    bmp.close();
                    studioLog << "bmp_write=" << bool(bmp) << " lit_pixels=" << lit << std::endl;
                    studioCaptured = bool(bmp) && lit >= (uint64_t(width)*height)/100;
                }
            }
            catch(const std::exception& e)
            {
                studioLog << "capture_exception=" << e.what() << std::endl;
            }
        }
    }
#endif
'''
gl_text = gl_text.replace(flip_anchor, capture + flip_anchor, 1)
gl_source.write_text(gl_text, encoding="utf-8")

# CI-only: upstream skips presentation when display registers are unchanged.
# A guest can draw repeatedly into the same buffer without changing those
# registers. Force presentation for the diagnostic run, not normal gameplay.
gs_source = Path(sys.argv[1]) / "Source/gs/GSHandler.cpp"
gs_text = gs_source.read_text(encoding="utf-8")
gs_anchor = "if(force || m_regsDirty)"
if gs_text.count(gs_anchor) != 1:
    raise SystemExit("Unexpected GS flip scheduling anchor")
gs_text = "#include <cstdlib>\n" + gs_text.replace(
    gs_anchor,
    'if(force || m_regsDirty || std::getenv("PS2STUDIO_CI_FRAME_PATH"))',
    1,
)
gs_source.write_text(gs_text, encoding="utf-8")
