import urllib.request
import urllib.error
import re
try:
    urllib.request.urlopen("http://127.0.0.1:8000/")
except urllib.error.HTTPError as e:
    html = e.read().decode("utf-8", errors='ignore')
    title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
    if title_match:
        print("TITLE:", title_match.group(1))
    
    # Also grab the traceback string if available for context
    exception_val_match = re.search(r'<pre class="exception_value">(.*?)</pre>', html, re.IGNORECASE | re.DOTALL)
    if exception_val_match:
        print("EXCEPTION:", exception_val_match.group(1).strip())
except Exception as e:
    print("Other error:", e)
