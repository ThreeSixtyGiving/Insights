# -*- coding: utf-8 -*-
import dash

from tsg_insights import create_app

server = create_app()

scripts = []
analytics_script = ''
if server.config.get("GOOGLE_ANALYTICS_TRACKING_ID"):
    scripts.append("https://www.googletagmanager.com/gtag/js?id={}".format(
        server.config.get("GOOGLE_ANALYTICS_TRACKING_ID")
    ))
    analytics_script = """
        <div id="cookie-consent-container">
            <span>
                Allow cookies?
            </span>
            <a href="/about#cookies" target="_blank">More information</a>
            <button id="cookie-consent">Yes</button>
            <button id="cookie-consent-no">No</button>
        </div>
        <script>
        var run_ga = function(){
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());

            gtag('config', '%s');
        }
        if(document.cookie.indexOf('cookie_consent=true')!=-1){
            run_ga();
        }
        if (document.cookie.indexOf('cookie_consent=')==-1){
            console.log("cookies not yet asked");
            var fn = function () {
                document.cookie = "cookie_consent=true";
                document.getElementById('cookie-consent-container').hidden = true;
                run_ga();
            };
            document.getElementById('cookie-consent').onclick = fn;
            var fn_no = function () {
                document.cookie = "cookie_consent=false";
                document.getElementById('cookie-consent-container').hidden = true;
            };
            document.getElementById('cookie-consent-no').onclick = fn_no;
        } else {
            console.log("cookies have been asked");
            document.getElementById('cookie-consent-container').hidden = true;
        }
        </script>""" % server.config.get("GOOGLE_ANALYTICS_TRACKING_ID")

app = dash.Dash(
    __name__,
    meta_tags=[
        {"charset": "UTF-8"},
        {"http-equiv": "X-UA-Compatible", "content": "IE=edge,chrome=1"},
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
    ],
    external_stylesheets=[
        "https://use.typekit.net/nri0jbb.css",
        "https://fonts.googleapis.com/icon?family=Material+Icons",
        "/static/css/sanitize.css",
        "/static/css/styles.css",
    ],
    external_scripts=scripts,
    server=server,
    url_base_pathname='/file/'
)
app.config.suppress_callback_exceptions = True

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="icon" type="image/x-icon" href="/static/favicon.ico">
        {%css%}
    </head>
    <body>
        {%app_entry%}
        {%config%}
        {%scripts%}
        ''' + analytics_script + '''
    </body>
</html>
'''

app.title = '360Giving Insights'
