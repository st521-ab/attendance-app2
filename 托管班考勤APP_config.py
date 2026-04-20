"""
托管班考勤APP - 配置文件
定义套餐类型和默认价格
"""

import os

# 套餐类型
MEAL_PLANS = {
    '午托': {
        'name': '午托',
        'description': '午餐+午休',
        'default_price': 800,  # 默认月费
    },
    '晚托': {
        'name': '晚托',
        'description': '晚餐+作业辅导',
        'default_price': 1000,
    },
    '全托': {
        'name': '全托',
        'description': '午餐+午休+晚餐+作业辅导',
        'default_price': 1500,
    },
}

# 每天工作日数量（用于退费计算）
DEFAULT_WORKDAYS_PER_MONTH = 22

def get_app_dir():
    """获取APP私有目录"""
    try:
        # Android环境
        from android.storage import app_storage_path
        return app_storage_path()
    except ImportError:
        # 桌面环境：使用用户主目录下的隐藏文件夹
        return os.path.expanduser('~/.托管班考勤数据')

# 数据文件路径
DATA_DIR = os.path.join(get_app_dir(), 'attendance_data')
STUDENTS_FILE = os.path.join(DATA_DIR, 'students.json')
ATTENDANCE_FILE = os.path.join(DATA_DIR, 'attendance.json')
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')

# 确保数据目录存在
def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

# APP信息
APP_NAME = '托管班考勤'
APP_VERSION = '1.0.0'
