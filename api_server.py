import os
from iwheregis_api import create_app

app = create_app(os.getenv("FLASK_ENV"))

if __name__ == '__main__':
    print("iwhereGIS 网格数据引擎 HTTP API 服务器启动中...")
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=app.config.get('DEBUG', True))