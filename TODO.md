# J.A.R.V.I.S App Fixes - TODO

## ✅ Step 1: Fix SettingsDialog - Add Scrollbar for scrolling
- Replace static frame with Canvas + Scrollbar + inner frame
- All 7 configuration fields + buttons must be scrollable

## ✅ Step 2: Fix icon cropping - Load jarvis_icon.ico
- Add `self.iconbitmap()` in `JarvisApp.__init__()`
- Add `self.iconbitmap()` in `SettingsDialog.__init__()`

## ✅ Step 3: Fix ESP32 WoL Connection Error Handling
- Improve `trigger_wake()` with retry feedback in UI
- Better ESP32 offline detection in health monitor

## ✅ Step 4: UI Polish Improvements
- Increase main window size for breathing room
- Improve button styling and spacing
- Fix any layout issues

