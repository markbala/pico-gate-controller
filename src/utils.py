def parse_request_path(request_bytes):
    """Very small parser for the first line of an HTTP GET request"""
    try:
        line = request_bytes.split(b"\r\n", 1)[0]
        parts = line.split()
        if len(parts) < 2:
            return "/", {}
        url = parts[1].decode("utf-8")
        if "?" in url:
            path, query = url.split("?", 1)
            q = {}
            for kv in query.split("&"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    q[k] = v
                else:
                    q[kv] = ""
            return path, q
        return url, {}
    except Exception:
        return "/", {}

def html_page(led_state="OFF"):
    return f"""<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pico Gate Controller</title>
  <style>
    html,body{{font-family:Arial,Helvetica,sans-serif;margin:0;padding:0;text-align:center}}
    .wrap{{max-width:520px;margin:24px auto;padding:0 16px}}
    h1{{font-size:20px;margin:12px 0}}
    .state{{margin:12px 0;font-weight:bold}}
    .btn{{display:inline-block;margin:6px;padding:14px 22px;border:0;border-radius:6px;cursor:pointer;font-size:16px}}
    .on{{background:#ce1b0e;color:#fff}}
    .off{{background:#000;color:#fff}}
    .foot{{margin-top:20px;font-size:12px;color:#666}}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Pico Gate Controller</h1>
    <div class="state">LED: {led_state}</div>
    <p>
      <a href="/led_on"><button class="btn on">LED ON</button></a>
      <a href="/led_off"><button class="btn off">LED OFF</button></a>
    </p>
    <p>
      <a href="/toggle_gate"><button class="btn off">TOGGLE GATE</button></a>
    </p>
    <div class="foot">© 2025</div>
  </div>
</body>
</html>"""
