package org.adekharianto.qrscan;

import android.app.Activity;
import android.content.ContentValues;
import android.content.Context;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.widget.Toast;

import java.io.FileOutputStream;
import java.io.OutputStream;

/**
 * Helper kecil yang dipanggil dari Python (lewat pyjnius) supaya:
 * 1. WebView mengizinkan permintaan kamera dari JavaScript (getUserMedia),
 *    yang dibutuhkan oleh library html5-qrcode di index.html.
 * 2. JavaScript bisa menyimpan file .xlsx hasil export ke folder Download
 *    publik di HP (lewat AndroidBridge.saveXlsxBase64).
 */
public class WebViewHelper {

    public static WebChromeClient createChromeClient(final Activity activity) {
        return new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                activity.runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        // Otomatis izinkan semua resource yang diminta (kamera/mic)
                        // karena kita sudah meminta izin runtime Android sebelumnya.
                        request.grant(request.getResources());
                    }
                });
            }
        };
    }

    public static AndroidBridge createBridge(Activity activity) {
        return new AndroidBridge(activity);
    }

    public static class AndroidBridge {
        private final Activity activity;

        public AndroidBridge(Activity activity) {
            this.activity = activity;
        }

        /**
         * Dipanggil dari JavaScript: window.AndroidBridge.saveXlsxBase64(base64, namaFile)
         * Menyimpan file ke folder Download publik (terlihat oleh user/File Manager).
         */
        @JavascriptInterface
        public void saveXlsxBase64(final String base64Data, final String fileName) {
            try {
                byte[] bytes = Base64.decode(base64Data, Base64.DEFAULT);

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    ContentValues values = new ContentValues();
                    values.put(MediaStore.Downloads.DISPLAY_NAME, fileName);
                    values.put(MediaStore.Downloads.MIME_TYPE,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
                    values.put(MediaStore.Downloads.IS_PENDING, 1);

                    Uri uri = activity.getContentResolver().insert(
                            MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
                    if (uri != null) {
                        OutputStream out = activity.getContentResolver().openOutputStream(uri);
                        if (out != null) {
                            out.write(bytes);
                            out.close();
                        }
                        values.clear();
                        values.put(MediaStore.Downloads.IS_PENDING, 0);
                        activity.getContentResolver().update(uri, values, null, null);
                    }
                } else {
                    java.io.File downloadsDir = Environment.getExternalStoragePublicDirectory(
                            Environment.DIRECTORY_DOWNLOADS);
                    if (!downloadsDir.exists()) downloadsDir.mkdirs();
                    java.io.File outFile = new java.io.File(downloadsDir, fileName);
                    FileOutputStream fos = new FileOutputStream(outFile);
                    fos.write(bytes);
                    fos.close();
                }

                activity.runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        Toast.makeText(activity, "Tersimpan di Download: " + fileName,
                                Toast.LENGTH_LONG).show();
                    }
                });
            } catch (Exception e) {
                activity.runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        Toast.makeText(activity, "Gagal menyimpan file: " + e.getMessage(),
                                Toast.LENGTH_LONG).show();
                    }
                });
            }
        }
    }
}
