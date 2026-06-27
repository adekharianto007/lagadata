"""
ADEK HARIANTO - QR/Barcode Scan & Excel Match
Aplikasi shell Kivy yang membungkus Android WebView native.

Kenapa WebView Android native (lewat pyjnius), bukan kivy.uix.webview?
- WebView bawaan Kivy tidak mendukung getUserMedia() (akses kamera dari JS),
  yang dibutuhkan oleh library html5-qrcode di index.html.
- Dengan mengakses android.webkit.WebView langsung dan mengoverride
  WebChromeClient.onPermissionRequest, kita bisa memberi izin kamera ke
  konten web sehingga scanner QR/barcode berfungsi.

File HTML utuh ada di assets/index.html dan dimuat via file:///android_asset/.
"""

import os
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.utils import platform

KV_LAYOUT = """
FloatLayout:
"""


class RootWidget(FloatLayout):
    pass


class QRScanApp(App):
    def build(self):
        self.title = "ADEK HARIANTO"
        root = RootWidget()
        if platform == "android":
            self.attach_android_webview(root)
        else:
            # Fallback untuk testing di desktop (Linux/Windows/Mac):
            # buka index.html di browser default, karena WebView Android
            # native tidak tersedia di luar Android.
            self.open_desktop_fallback()
        return root

    def open_desktop_fallback(self):
        import webbrowser
        html_path = os.path.join(os.path.dirname(__file__), "assets", "index.html")
        webbrowser.open("file://" + os.path.abspath(html_path))

    def attach_android_webview(self, root):
        from jnius import autoclass, PythonJavaClass, java_method
        from android.runnable import run_on_ui_thread  # noqa: F401  (provided by p4a)

        WebView = autoclass("android.webkit.WebView")
        WebViewClient = autoclass("android.webkit.WebViewClient")
        WebChromeClient = autoclass("android.webkit.WebChromeClient")
        WebSettings = autoclass("android.webkit.WebSettings")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        LayoutParams = autoclass("android.view.ViewGroup$LayoutParams")
        Manifest = autoclass("android.Manifest$permission")
        ActivityCompat = autoclass("androidx.core.app.ActivityCompat")
        ContextCompat = autoclass("androidx.core.content.ContextCompat")
        PackageManager = autoclass("android.content.pm.PackageManager")

        activity = PythonActivity.mActivity

        # --- Minta izin kamera & storage saat runtime (Android 6+) ---
        needed = [Manifest.CAMERA, Manifest.WRITE_EXTERNAL_STORAGE]
        to_request = []
        for perm in needed:
            granted = ContextCompat.checkSelfPermission(activity, perm)
            if granted != PackageManager.PERMISSION_GRANTED:
                to_request.append(perm)
        if to_request:
            ActivityCompat.requestPermissions(activity, to_request, 1001)

        # --- WebChromeClient custom: otomatis grant permission request dari JS (kamera) ---
        class MyWebChromeClient(PythonJavaClass):
            __javacontext__ = "app"
            __javainterfaces__ = ["android/webkit/WebChromeClient"]
            __javaclass__ = "android/webkit/WebChromeClient"

        # pyjnius tidak mudah dipakai untuk subclass Java langsung di banyak versi p4a,
        # jadi kita pakai pendekatan paling kompatibel: extend via recipe Java kecil
        # tidak tersedia di sini, maka kita gunakan WebChromeClient bawaan yang sudah
        # otomatis meminta izin runtime Android lalu izinkan permission JS lewat
        # override sederhana menggunakan android.webkit.PermissionRequest API
        # (tersedia mulai API 21) melalui kelas Java pembantu di src/ (lihat README).

        WebViewHelper = autoclass("org.adekharianto.qrscan.WebViewHelper")

        webview = WebView(activity)
        webview.getSettings().setJavaScriptEnabled(True)
        webview.getSettings().setDomStorageEnabled(True)
        webview.getSettings().setMediaPlaybackRequiresUserGesture(False)
        webview.getSettings().setAllowFileAccess(True)
        webview.getSettings().setAllowFileAccessFromFileURLs(True)
        webview.getSettings().setAllowUniversalAccessFromFileURLs(True)
        webview.setWebViewClient(WebViewClient())

        # Helper Java kecil yang menangani izin kamera utk getUserMedia
        # dan menyediakan jembatan penyimpanan file export (AndroidBridge).
        chrome_client = WebViewHelper.createChromeClient(activity)
        webview.setWebChromeClient(chrome_client)

        bridge = WebViewHelper.createBridge(activity)
        webview.addJavascriptInterface(bridge, "AndroidBridge")

        webview.loadUrl("file:///android_asset/index.html")

        activity.setContentView(webview)

        # Tangani tombol back Android agar menutup WebView history dulu
        from kivy.core.window import Window

        def on_keyboard(window, key, *args):
            if key == 27:  # tombol back
                if webview.canGoBack():
                    webview.goBack()
                    return True
            return False

        Window.bind(on_keyboard=on_keyboard)

        self._webview = webview


if __name__ == "__main__":
    QRScanApp().run()
