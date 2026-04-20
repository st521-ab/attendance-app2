"""
托管班考勤APP - 数据管理模块
负责学生数据、考勤记录、账单的CRUD操作
"""

import json
import os
from datetime import datetime, date
from config import (
    STUDENTS_FILE, ATTENDANCE_FILE, CONFIG_FILE,
    DEFAULT_WORKDAYS_PER_MONTH, ensure_data_dir
)
# 导入套餐配置（使用引用，确保settings界面修改后生效）
from config import MEAL_PLANS

class DataManager:
    """数据管理器类"""
    
    def __init__(self):
        ensure_data_dir()
        self.students = self.load_students()
        self.attendance = self.load_attendance()
        self.config = self.load_config()
    
    # ==================== 学生管理 ====================
    
    def load_students(self):
        """加载学生数据"""
        if os.path.exists(STUDENTS_FILE):
            try:
                with open(STUDENTS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_students(self):
        """保存学生数据"""
        with open(STUDENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.students, f, ensure_ascii=False, indent=2)
    
    def add_student(self, name, meal_plan, custom_price=None):
        """添加学生"""
        student_id = str(datetime.now().timestamp())
        price = custom_price if custom_price else MEAL_PLANS[meal_plan]['default_price']
        
        self.students[student_id] = {
            'id': student_id,
            'name': name,
            'meal_plan': meal_plan,
            'monthly_price': price,
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'active': True
        }
        self.save_students()
        return student_id
    
    def update_student(self, student_id, name=None, meal_plan=None, monthly_price=None):
        """更新学生信息"""
        if student_id in self.students:
            if name:
                self.students[student_id]['name'] = name
            if meal_plan:
                self.students[student_id]['meal_plan'] = meal_plan
            if monthly_price:
                self.students[student_id]['monthly_price'] = monthly_price
            self.save_students()
            return True
        return False
    
    def delete_student(self, student_id):
        """删除学生"""
        if student_id in self.students:
            del self.students[student_id]
            self.save_students()
            return True
        return False
    
    def get_student(self, student_id):
        """获取单个学生信息"""
        return self.students.get(student_id)
    
    def get_all_students(self, active_only=True):
        """获取所有学生列表"""
        if active_only:
            return [s for s in self.students.values() if s.get('active', True)]
        return list(self.students.values())
    
    def get_active_student_count(self):
        """获取活跃学生数量"""
        return len([s for s in self.students.values() if s.get('active', True)])
    
    # ==================== 考勤管理 ====================
    
    def load_attendance(self):
        """加载考勤数据"""
        if os.path.exists(ATTENDANCE_FILE):
            try:
                with open(ATTENDANCE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_attendance(self):
        """保存考勤数据"""
        with open(ATTENDANCE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.attendance, f, ensure_ascii=False, indent=2)
    
    def get_attendance_key(self, check_date=None):
        """获取考勤记录的键名"""
        if check_date is None:
            check_date = date.today()
        return check_date.strftime('%Y-%m-%d')
    
    def ensure_attendance_date(self, check_date=None):
        """确保某天的考勤记录存在"""
        key = self.get_attendance_key(check_date)
        if key not in self.attendance:
            self.attendance[key] = {}
        return key
    
    def toggle_attendance(self, student_id, check_date=None):
        """切换学生考勤状态"""
        key = self.ensure_attendance_date(check_date)
        
        if student_id not in self.attendance[key]:
            # 新增记录，默认记为"到"
            self.attendance[key][student_id] = 'present'
        elif self.attendance[key][student_id] == 'present':
            # 已到 -> 改为缺勤
            self.attendance[key][student_id] = 'absent'
        else:
            # 已缺勤 -> 改为到
            self.attendance[key][student_id] = 'present'
        
        self.save_attendance()
        return self.attendance[key][student_id]
    
    def set_attendance(self, student_id, status, check_date=None):
        """设置学生考勤状态"""
        key = self.ensure_attendance_date(check_date)
        self.attendance[key][student_id] = status
        self.save_attendance()
    
    def get_attendance(self, student_id, check_date=None):
        """获取学生考勤状态"""
        key = self.get_attendance_key(check_date)
        return self.attendance.get(key, {}).get(student_id, None)
    
    def get_day_attendance(self, check_date=None):
        """获取某天所有学生的考勤状态"""
        key = self.get_attendance_key(check_date)
        return self.attendance.get(key, {})
    
    def mark_all_present(self, check_date=None):
        """一键全到"""
        key = self.ensure_attendance_date(check_date)
        for student_id in self.students:
            if self.students[student_id].get('active', True):
                if student_id not in self.attendance[key]:
                    self.attendance[key][student_id] = 'present'
        self.save_attendance()
    
    def get_attendance_dates(self, start_date, end_date):
        """获取日期范围内的考勤记录"""
        result = {}
        current = start_date
        while current <= end_date:
            key = self.get_attendance_key(current)
            if key in self.attendance:
                result[key] = self.attendance[key]
            current = date.fromordinal(current.toordinal() + 1)
        return result
    
    # ==================== 账单计算 ====================
    
    def calculate_refund(self, monthly_price, absent_days, workdays):
        """计算退费金额"""
        if workdays <= 0:
            return 0
        daily_rate = monthly_price / workdays
        return round(daily_rate * absent_days, 2)
    
    def get_monthly_bill(self, year, month):
        """获取指定月份的账单"""
        # 获取该月的所有日期
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        end_date = date.fromordinal(end_date.toordinal() - 1)
        
        # 统计工作日（周一到周五）
        workdays = 0
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # 0-4 是周一到周五
                workdays += 1
            current = date.fromordinal(current.toordinal() + 1)
        
        bills = []
        total_refund = 0
        total_actual = 0
        
        for student in self.get_all_students():
            student_id = student['id']
            monthly_price = student['monthly_price']
            
            # 统计该月出勤和请假天数
            present_days = 0
            absent_days = 0
            
            current = start_date
            while current <= end_date:
                if current.weekday() < 5:  # 只统计工作日
                    status = self.get_attendance(student_id, current)
                    if status == 'present':
                        present_days += 1
                    elif status == 'absent':
                        absent_days += 1
                    # None 表示未记录，默认算到
                    elif status is None:
                        present_days += 1
                current = date.fromordinal(current.toordinal() + 1)
            
            # 计算退费和实收
            refund = self.calculate_refund(monthly_price, absent_days, workdays)
            actual_amount = monthly_price - refund
            
            bills.append({
                'student_id': student_id,
                'name': student['name'],
                'meal_plan': student['meal_plan'],
                'monthly_price': monthly_price,
                'workdays': workdays,
                'present_days': present_days,
                'absent_days': absent_days,
                'refund': refund,
                'actual_amount': actual_amount
            })
            
            total_refund += refund
            total_actual += actual_amount
        
        return {
            'year': year,
            'month': month,
            'workdays': workdays,
            'bills': bills,
            'total_refund': round(total_refund, 2),
            'total_actual': round(total_actual, 2)
        }
    
    def get_monthly_summary(self, year, month):
        """获取月度汇总"""
        bill_data = self.get_monthly_bill(year, month)
        return {
            'year': year,
            'month': month,
            'student_count': len(bill_data['bills']),
            'workdays': bill_data['workdays'],
            'total_refund': bill_data['total_refund'],
            'total_actual': bill_data['total_actual']
        }
    
    # ==================== 配置管理 ====================
    
    def load_config(self):
        """加载配置"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_config(self):
        """保存配置"""
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def update_plan_price(self, plan_name, price):
        """更新套餐价格"""
        if plan_name in MEAL_PLANS:
            MEAL_PLANS[plan_name]['default_price'] = price
            self.save_config()
            return True
        return False
    
    def get_plan_price(self, plan_name):
        """获取套餐价格"""
        return MEAL_PLANS.get(plan_name, {}).get('default_price', 0)


# 全局数据管理器实例
data_manager = DataManager()
