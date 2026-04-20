"""
托管班考勤APP - 配置文件
定义套餐类型和默认价格
"""

导入 os

# 套餐类型
MEAL_PLANS = {
    '午托': {
        '名称': '午托',
        '描述': '午餐+午休',
        '默认价格': 800,  # 默认月费
    },
    '晚托': {
        '名称': '晚托',
        '描述': '晚餐+作业辅导',
        '默认价格': 1000,
    },
    全托: 
        '名称': '全托',
        '描述': '午餐+午休+晚餐+作业辅导',
        '默认价格': 1500,
    },
}

# 每天工作日数量（用于退费计算）
每月默认工作日 =22

获取应用目录():
    """获取APP私有目录"""
    尝试:
        # Android环境
        从 android.storage 导入 app_storage_path
        return app_storage_path()
    except ImportError:
        # 桌面环境：使用用户主目录下的隐藏文件夹
        return os.path.expanduser('~/.托管班考勤数据')

# 数据文件路径
DATA_DIR = os.path.join(获取应用目录(), 'attendance_data')
STUDENTS_FILE = os.path.join(DATA_DIR, 'students.json')
ATTENDANCE_FILE = os.path.join(DATA_DIR, 'attendance.json')
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')

# 确保数据目录存在
定义 ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

# APP信息
APP_NAME = '托管班考勤'
APP_VERSION = '1.0.0'
