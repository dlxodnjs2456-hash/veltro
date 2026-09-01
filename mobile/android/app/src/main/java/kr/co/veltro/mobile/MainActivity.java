package kr.co.veltro.mobile;

import android.app.Activity;
import android.app.DownloadManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.view.Gravity;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.DownloadListener;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final String START_URL = "https://veltro-n8v3.vercel.app/";
    private WebView webView;
    private TextView loadingView;

    private static final String MOBILE_FIX_JS =
            "(function(){" +
            "if(window.__veltroMobileFix101)return;window.__veltroMobileFix101=true;" +
            "var st=document.createElement('style');" +
            "st.textContent='.drawer{overflow-y:auto!important;overflow-x:hidden!important;-webkit-overflow-scrolling:touch!important;overscroll-behavior:contain!important;padding-bottom:calc(32px + env(safe-area-inset-bottom))!important}.m-main{overflow-x:hidden!important}.mobile{min-height:100vh!important}';" +
            "document.head.appendChild(st);" +
            "document.addEventListener('click',function(e){" +
            "var t=e.target&&e.target.closest?e.target.closest('#mTabs [data-tab]'):null;" +
            "if(t){e.preventDefault();e.stopImmediatePropagation();try{page='trade';tab=t.dataset.tab;renderAll();closeDrawer();}catch(x){}return;}" +
            "var s=e.target&&e.target.closest?e.target.closest('#mSymbols [data-symbol]'):null;" +
            "if(s){e.preventDefault();e.stopImmediatePropagation();try{var n=INS.find(function(i){return i.symbol===s.dataset.symbol});if(!n)return;if(n.code==='HSI'){toast('현재 점검중인 종목입니다.');closeDrawer();return;}cur=n;page='trade';quote=null;renderAll();closeDrawer();loadQuote().then(function(){renderAll();}).catch(function(err){toast('시세 조회 중입니다. 잠시 후 다시 확인해주세요.');});}catch(x){}return;}" +
            "},true);" +
            "})();";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.rgb(4, 10, 24));
        getWindow().setNavigationBarColor(Color.rgb(4, 10, 24));

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(4, 10, 24));

        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(4, 10, 24));
        root.addView(webView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT));

        loadingView = new TextView(this);
        loadingView.setText("VELTRO");
        loadingView.setTextColor(Color.WHITE);
        loadingView.setTextSize(25f);
        loadingView.setGravity(Gravity.CENTER);
        loadingView.setBackgroundColor(Color.rgb(4, 10, 24));
        root.addView(loadingView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT));

        setContentView(root);
        configureWebView();

        if (savedInstanceState == null) {
            webView.loadUrl(START_URL);
        } else {
            webView.restoreState(savedInstanceState);
        }
    }

    private void configureWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setUserAgentString(settings.getUserAgentString() + " VELTRO-Android/1.0.1");

        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String scheme = uri.getScheme();
                if ("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme)) {
                    return false;
                }
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                } catch (Exception ignored) {
                    Toast.makeText(MainActivity.this, "연결할 앱을 찾을 수 없습니다.", Toast.LENGTH_SHORT).show();
                }
                return true;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                view.evaluateJavascript(MOBILE_FIX_JS, null);
                loadingView.animate().alpha(0f).setDuration(180).withEndAction(() -> loadingView.setVisibility(View.GONE)).start();
            }
        });

        webView.setWebChromeClient(new WebChromeClient());
        webView.setDownloadListener(new DownloadListener() {
            @Override
            public void onDownloadStart(String url, String userAgent, String contentDisposition,
                                        String mimetype, long contentLength) {
                try {
                    DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
                    request.setMimeType(mimetype);
                    request.addRequestHeader("User-Agent", userAgent);
                    String cookies = CookieManager.getInstance().getCookie(url);
                    if (cookies != null) request.addRequestHeader("Cookie", cookies);
                    request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                    request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, "VELTRO_download");
                    DownloadManager manager = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
                    manager.enqueue(request);
                    Toast.makeText(MainActivity.this, "다운로드를 시작했습니다.", Toast.LENGTH_SHORT).show();
                } catch (Exception e) {
                    startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
                }
            }
        });
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        webView.saveState(outState);
        super.onSaveInstanceState(outState);
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.stopLoading();
            webView.destroy();
        }
        super.onDestroy();
    }
}
