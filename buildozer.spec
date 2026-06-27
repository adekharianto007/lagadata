[app]

title = ADEK HARIANTO
package.name = adekharianto
package.domain = org.adekharianto

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,html,js,css,json
source.include_patterns = assets/*,assets/**/*

version = 1.0

# Kivy hanya dipakai sebagai shell minimal; kamera & rendering
# sesungguhnya ditangani Android WebView native.
requirements = python3,kivy,pyjnius

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/icon.png

[buildozer]
log_level = 2
warn_on_root = 1

[app:android]
# Source Java tambahan (WebViewHelper.java) ikut dikompilasi bersama APK.
add_src = src

android.permissions = CAMERA,INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# WebView modern (getUserMedia, dsb) butuh minimal API yang cukup baru.
android.minapi = 24
android.api = 34
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a

android.allow_backup = True

# Diperlukan agar PermissionRequest.grant() & androidx tersedia.
android.gradle_dependencies = androidx.core:core:1.12.0

p4a.bootstrap = sdl2
