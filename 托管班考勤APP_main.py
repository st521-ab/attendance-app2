"""
托管班考勤APP - 主程序入口
使用Kivy框架开发的托管班考勤管理应用
"""

import os
import sys

# 设置Kivy环境
os.environ['KIVY_AUDIO'] = 'sdl2'
os.environ['KIVY_NO_ARGS'] = '1'

from kivy.config import Config
Config.set('kivy', 'window_icon', '')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy import require
require('2.1.0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.recycleview import RecycleView
from kivy.properties import (
    StringProperty, ListProperty, BooleanProperty, 
    NumericProperty, ObjectProperty
)
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line

from datetime import date, datetime
from data_manager import data_manager, MEAL_PLANS
from config import APP_NAME, APP_VERSION

# 颜色定义
PRIMARY_COLOR = get_color_from_hex('#1976D2')
ACCENT_COLOR = get_color_from_hex('#FF5722')
SUCCESS_COLOR = get_color_from_hex('#4CAF50')
WARNING_COLOR = get_color_from_hex('#FFC107')
ERROR_COLOR = get_color_from_hex('#F44336')
WHITE = (1, 1, 1, 1)
DARK_TEXT = (0.2, 0.2, 0.2, 1)
GRAY_TEXT = (0.5, 0.5, 0.5, 1)

# 设置窗口大小（用于测试）
Window.size = (360, 640)


# ==================== 通用组件 ====================

class Card(BoxLayout):
    """卡片容器"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10
        with self.canvas.before:
            Color(rgba=WHITE)
            self.rect = RoundedRectangle(radius=[12], pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class ActionButton(Button):
    """操作按钮"""
    def __init__(self, color=PRIMARY_COLOR, **kwargs):
        super().__init__(**kwargs)
        self.background_color = color
        self.color = WHITE
        self.font_size = '16sp'
        self.bold = True
        self.size_hint_y = None
        self.height = '50dp'


# ==================== 考勤界面 ====================

class AttendanceScreen(Screen):
    """考勤记录界面"""
    
    current_date = StringProperty()
    present_count = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_date = date.today().strftime('%Y年%m月%d日')
        Clock.schedule_once(lambda dt: self.build_ui(), 0.1)
    
    def build_ui(self):
        """构建界面"""
        self.clear_widgets()
        
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 日期显示卡片
        date_card = Card(size_hint_y=None, height='100dp')
        date_card.add_widget(Label(
            text=self.current_date,
            font_size='24sp',
            bold=True,
            color=PRIMARY_COLOR
        ))
        self.stats_label = Label(
            text=f'应到: 0 人  |  已到: 0 人',
            font_size='16sp',
            color=GRAY_TEXT
        )
        date_card.add_widget(self.stats_label)
        main_layout.add_widget(date_card)
        
        # 一键全到按钮
        all_present_btn = ActionButton(
            text='📋 一键全到',
            color=SUCCESS_COLOR
        )
        all_present_btn.bind(on_press=lambda x: self.mark_all_present())
        main_layout.add_widget(all_present_btn)
        
        # 学生考勤列表
        self.scroll_view = ScrollView(do_scroll_x=False)
        self.student_list = GridLayout(cols=1, spacing=8, size_hint_y=None, padding=5)
        self.scroll_view.add_widget(self.student_list)
        main_layout.add_widget(self.scroll_view)
        
        # 底部留白（为导航栏腾空间）
        main_layout.add_widget(BoxLayout(size_hint_y=None, height='70dp'))
        
        self.add_widget(main_layout)
        self.refresh()
    
    def on_enter(self):
        """进入界面时刷新"""
        self.refresh()
    
    def refresh(self):
        """刷新考勤数据"""
        self.current_date = date.today().strftime('%Y年%m月%d日')
        students = data_manager.get_all_students()
        day_attendance = data_manager.get_day_attendance()
        
        self.student_list.clear_widgets()
        self.student_list.height = 0
        
        present = 0
        for student in students:
            status = day_attendance.get(student['id'], None)
            is_present = status == 'present' or status is None
            if is_present:
                present += 1
            
            card = self.create_attendance_card(
                student['id'],
                student['name'],
                student['meal_plan'],
                is_present
            )
            self.student_list.add_widget(card)
            self.student_list.height += 90
        
        self.present_count = present
        self.stats_label.text = f'应到: {len(students)} 人  |  已到: {present} 人'
    
    def create_attendance_card(self, student_id, name, meal_plan, is_present):
        """创建考勤卡片"""
        card = BoxLayout(
            orientation='horizontal',
            padding=15,
            spacing=15,
            size_hint_y=None,
            height='80dp'
        )
        
        with card.canvas.before:
            Color(rgba=SUCCESS_COLOR if is_present else ERROR_COLOR)
            card.rect = RoundedRectangle(radius=[12], pos=card.pos, size=card.size)
        card.bind(pos=lambda *x: self._update_card_rect(card), 
                  size=lambda *x: self._update_card_rect(card))
        
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.6)
        info_layout.add_widget(Label(
            text=name,
            font_size='20sp',
            bold=True,
            color=WHITE,
            halign='left',
            text_size=(200, None)
        ))
        info_layout.add_widget(Label(
            text=meal_plan,
            font_size='14sp',
            color=(1, 1, 1, 0.8)
        ))
        card.add_widget(info_layout)
        
        status_label = Label(
            text='✓ 已到' if is_present else '✗ 缺勤',
            font_size='18sp',
            bold=True,
            color=WHITE,
            size_hint_x=0.4
        )
        card.add_widget(status_label)
        
        # 点击切换状态
        card.bind(on_touch_down=lambda inst, touch: self.on_card_touch(inst, touch, student_id, status_label))
        
        return card
    
    def _update_card_rect(self, card):
        card.rect.pos = card.pos
        card.rect.size = card.size
    
    def on_card_touch(self, card, touch, student_id, status_label):
        """处理卡片点击"""
        if card.collide_point(*touch.pos):
            data_manager.toggle_attendance(student_id)
            self.refresh()
            return True
        return False
    
    def mark_all_present(self):
        """一键全到"""
        data_manager.mark_all_present()
        self.refresh()


# ==================== 学生管理界面 ====================

class StudentScreen(Screen):
    """学生管理界面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.build_ui(), 0.1)
    
    def build_ui(self):
        """构建界面"""
        self.clear_widgets()
        
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题栏
        title_card = Card(size_hint_y=None, height='80dp')
        title_layout = BoxLayout(orientation='horizontal')
        title_layout.add_widget(Label(
            text='学生列表',
            font_size='24sp',
            bold=True,
            color=PRIMARY_COLOR,
            size_hint_x=0.6
        ))
        add_btn = ActionButton(
            text='+ 添加学生',
            color=SUCCESS_COLOR,
            size_hint_x=0.4,
            height='50dp'
        )
        add_btn.bind(on_press=lambda x: self.add_student_popup())
        title_layout.add_widget(add_btn)
        title_card.add_widget(title_layout)
        main_layout.add_widget(title_card)
        
        # 学生列表
        self.scroll_view = ScrollView(do_scroll_x=False)
        self.student_list = GridLayout(cols=1, spacing=8, size_hint_y=None, padding=5)
        self.scroll_view.add_widget(self.student_list)
        main_layout.add_widget(self.scroll_view)
        
        # 底部留白
        main_layout.add_widget(BoxLayout(size_hint_y=None, height='70dp'))
        
        self.add_widget(main_layout)
        self.refresh()
    
    def on_enter(self):
        """进入界面时刷新"""
        self.refresh()
    
    def refresh(self):
        """刷新学生列表"""
        students = data_manager.get_all_students()
        
        self.student_list.clear_widgets()
        self.student_list.height = 0
        
        if not students:
            empty_label = Label(
                text='暂无学生\n点击上方"添加学生"按钮添加',
                font_size='16sp',
                color=GRAY_TEXT,
                halign='center'
            )
            self.student_list.add_widget(empty_label)
            self.student_list.height += 100
            return
        
        for student in students:
            card = self.create_student_card(
                student['id'],
                student['name'],
                student['meal_plan'],
                student['monthly_price']
            )
            self.student_list.add_widget(card)
            self.student_list.height += 120
    
    def create_student_card(self, student_id, name, meal_plan, monthly_price):
        """创建学生卡片"""
        card = Card()
        card.height = '110dp'
        
        info_layout = BoxLayout(orientation='horizontal', size_hint_y=0.6)
        
        name_label = Label(
            text=name,
            font_size='20sp',
            bold=True,
            color=DARK_TEXT,
            size_hint_x=0.5,
            halign='left',
            text_size=(150, None)
        )
        info_layout.add_widget(name_label)
        
        info_layout.add_widget(Label(
            text=f'{meal_plan}  ¥{monthly_price}/月',
            font_size='14sp',
            color=GRAY_TEXT,
            size_hint_x=0.5
        ))
        card.add_widget(info_layout)
        
        # 操作按钮
        btn_layout = BoxLayout(size_hint_y=0.4, spacing=10)
        edit_btn = ActionButton(
            text='✏️ 编辑',
            color=WARNING_COLOR,
            font_size='14sp',
            height='40dp'
        )
        edit_btn.bind(on_press=lambda x: self.edit_student_popup(student_id))
        delete_btn = ActionButton(
            text='🗑️ 删除',
            color=ERROR_COLOR,
            font_size='14sp',
            height='40dp'
        )
        delete_btn.bind(on_press=lambda x: self.delete_student_popup(student_id, name))
        btn_layout.add_widget(edit_btn)
        btn_layout.add_widget(delete_btn)
        card.add_widget(btn_layout)
        
        return card
    
    def add_student_popup(self):
        """添加学生弹窗"""
        content = StudentFormPopup()
        popup = Popup(
            title='添加学生',
            content=content,
            size_hint=(0.9, 0.75),
            auto_dismiss=False,
            background_color=WHITE
        )
        content.setup_ui(popup, self)
        popup.open()
    
    def edit_student_popup(self, student_id):
        """编辑学生弹窗"""
        student = data_manager.get_student(student_id)
        if student:
            content = StudentFormPopup(student)
            popup = Popup(
                title='编辑学生',
                content=content,
                size_hint=(0.9, 0.75),
                auto_dismiss=False,
                background_color=WHITE
            )
            content.setup_ui(popup, self)
            popup.open()
    
    def delete_student_popup(self, student_id, name):
        """删除确认弹窗"""
        content = BoxLayout(orientation='vertical', padding=20, spacing=20)
        content.add_widget(Label(
            text=f'确定要删除学生\n"{name}"吗？\n\n删除后考勤记录将保留。',
            font_size='18sp',
            color=DARK_TEXT,
            halign='center'
        ))
        
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        cancel_btn = ActionButton(text='取消', color=GRAY_TEXT)
        confirm_btn = ActionButton(text='删除', color=ERROR_COLOR)
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(confirm_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title='确认删除',
            content=content,
            size_hint=(0.85, 0.4),
            auto_dismiss=False,
            background_color=WHITE
        )
        
        cancel_btn.bind(on_press=popup.dismiss)
        confirm_btn.bind(on_press=lambda x: self.confirm_delete(student_id, popup))
        popup.open()
    
    def confirm_delete(self, student_id, popup):
        """确认删除"""
        data_manager.delete_student(student_id)
        popup.dismiss()
        self.refresh()


class StudentFormPopup(BoxLayout):
    """学生信息表单弹窗"""
    
    def __init__(self, student=None, **kwargs):
        super().__init__(**kwargs)
        self.student = student
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
    
    def setup_ui(self, popup, parent_screen):
        """设置UI"""
        self.popup = popup
        self.parent_screen = parent_screen
        
        # 名称输入
        self.add_widget(Label(text='学生姓名', size_hint_y=None, height=40, color=DARK_TEXT))
        self.name_input = TextInput(
            hint_text='请输入学生姓名',
            multiline=False,
            size_hint_y=None,
            height=50,
            font_size=18,
            padding=[10, 10, 10, 10]
        )
        if self.student:
            self.name_input.text = self.student['name']
        self.add_widget(self.name_input)
        
        # 套餐选择
        self.add_widget(Label(text='选择套餐', size_hint_y=None, height=40, color=DARK_TEXT))
        self.plan_spinner = Spinner(
            text=self.student['meal_plan'] if self.student else '午托',
            values=['午托', '晚托', '全托'],
            size_hint_y=None,
            height=50,
            font_size=18
        )
        self.add_widget(self.plan_spinner)
        
        # 价格输入
        self.add_widget(Label(text='月费（元）', size_hint_y=None, height=40, color=DARK_TEXT))
        self.price_input = TextInput(
            hint_text='留空使用默认价格',
            multiline=False,
            input_filter='float',
            size_hint_y=None,
            height=50,
            font_size=18,
            padding=[10, 10, 10, 10]
        )
        if self.student:
            self.price_input.text = str(self.student['monthly_price'])
        self.add_widget(self.price_input)
        
        # 按钮
        btn_layout = BoxLayout(size_hint_y=None, height=60, spacing=10)
        cancel_btn = ActionButton(text='取消', color=GRAY_TEXT)
        confirm_btn = ActionButton(
            text='保存' if self.student else '添加',
            color=SUCCESS_COLOR
        )
        cancel_btn.bind(on_press=popup.dismiss)
        confirm_btn.bind(on_press=self.save)
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(confirm_btn)
        self.add_widget(btn_layout)
    
    def save(self, instance):
        """保存"""
        name = self.name_input.text.strip()
        if not name:
            self.name_input.hint_text = '请输入学生姓名！'
            return
        
        plan = self.plan_spinner.text
        price_text = self.price_input.text.strip()
        price = float(price_text) if price_text else None
        
        if self.student:
            data_manager.update_student(
                self.student['id'],
                name=name,
                meal_plan=plan,
                monthly_price=price
            )
        else:
            data_manager.add_student(name, plan, price)
        
        self.parent_screen.refresh()
        self.popup.dismiss()


# ==================== 账单界面 ====================

class BillScreen(Screen):
    """账单界面"""
    
    selected_year = NumericProperty()
    selected_month = NumericProperty()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        today = date.today()
        self.selected_year = today.year
        self.selected_month = today.month
        Clock.schedule_once(lambda dt: self.build_ui(), 0.1)
    
    def build_ui(self):
        """构建界面"""
        self.clear_widgets()
        
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 月份选择器
        month_card = Card(size_hint_y=None, height='80dp')
        month_layout = BoxLayout(orientation='horizontal', spacing=10)
        
        prev_btn = Button(text='◀', font_size='24sp', background_color=PRIMARY_COLOR)
        prev_btn.bind(on_press=lambda x: self.change_month(-1))
        
        self.month_label = Label(
            text=f'{self.selected_year}年{self.selected_month}月',
            font_size='22sp',
            bold=True,
            color=PRIMARY_COLOR
        )
        
        next_btn = Button(text='▶', font_size='24sp', background_color=PRIMARY_COLOR)
        next_btn.bind(on_press=lambda x: self.change_month(1))
        
        month_layout.add_widget(prev_btn)
        month_layout.add_widget(self.month_label)
        month_layout.add_widget(next_btn)
        month_card.add_widget(month_layout)
        main_layout.add_widget(month_card)
        
        # 汇总信息
        self.summary_card = Card(size_hint_y=None, height='120dp')
        main_layout.add_widget(self.summary_card)
        
        # 表头
        header_layout = GridLayout(
            cols=6,
            size_hint_y=None,
            height=45,
            padding=5
        )
        with header_layout.canvas.before:
            Color(rgba=PRIMARY_COLOR)
            Rectangle(pos=header_layout.pos, size=header_layout.size)
        
        headers = ['姓名', '套餐', '月费', '出勤', '请假', '实收']
        for h in headers:
            header_layout.add_widget(Label(
                text=h, bold=True, color=WHITE, font_size='13sp'
            ))
        main_layout.add_widget(header_layout)
        
        # 账单列表
        self.scroll_view = ScrollView(do_scroll_x=False)
        self.bill_list = GridLayout(cols=6, spacing=2, size_hint_y=None, padding=[0, 0, 0, 10])
        self.scroll_view.add_widget(self.bill_list)
        main_layout.add_widget(self.scroll_view)
        
        # 底部留白
        main_layout.add_widget(BoxLayout(size_hint_y=None, height='70dp'))
        
        self.add_widget(main_layout)
        self.load_bill()
    
    def on_enter(self):
        """进入界面时刷新"""
        self.load_bill()
    
    def change_month(self, delta):
        """切换月份"""
        self.selected_month += delta
        if self.selected_month > 12:
            self.selected_month = 1
            self.selected_year += 1
        elif self.selected_month < 1:
            self.selected_month = 12
            self.selected_year -= 1
        self.load_bill()
    
    def load_bill(self):
        """加载账单"""
        self.month_label.text = f'{self.selected_year}年{self.selected_month}月'
        
        data = data_manager.get_monthly_bill(self.selected_year, self.selected_month)
        
        # 更新汇总
        self.summary_card.clear_widgets()
        summary_layout = GridLayout(cols=2, spacing=10)
        summary_layout.add_widget(Label(text=f'工作日: {data["workdays"]}天', font_size='16sp', color=GRAY_TEXT))
        summary_layout.add_widget(Label(text=f'退费合计: ¥{data["total_refund"]}', font_size='16sp', color=ERROR_COLOR))
        summary_layout.add_widget(Label(text=f'总学生: {len(data["bills"])}人', font_size='16sp', color=GRAY_TEXT))
        summary_layout.add_widget(Label(
            text=f'实收合计: ¥{data["total_actual"]}',
            font_size='18sp',
            bold=True,
            color=SUCCESS_COLOR
        ))
        self.summary_card.add_widget(summary_layout)
        
        # 更新列表
        self.bill_list.clear_widgets()
        self.bill_list.height = 0
        
        if not data['bills']:
            self.bill_list.add_widget(Label(
                text='暂无账单数据',
                font_size='16sp',
                color=GRAY_TEXT,
                size_hint_x=1,
                height=50
            ))
            self.bill_list.height += 50
            return
        
        for bill in data['bills']:
            self.bill_list.add_widget(Label(text=bill['name'], font_size='12sp', color=DARK_TEXT))
            self.bill_list.add_widget(Label(text=bill['meal_plan'], font_size='11sp', color=GRAY_TEXT))
            self.bill_list.add_widget(Label(text=f'¥{bill["monthly_price"]}', font_size='12sp', color=DARK_TEXT))
            self.bill_list.add_widget(Label(text=f'{bill["present_days"]}天', font_size='12sp', color=SUCCESS_COLOR))
            self.bill_list.add_widget(Label(text=f'{bill["absent_days"]}天', font_size='12sp', color=ERROR_COLOR))
            self.bill_list.add_widget(Label(
                text=f'¥{bill["actual_amount"]}',
                font_size='13sp',
                bold=True,
                color=PRIMARY_COLOR
            ))
            self.bill_list.height += 50


# ==================== 设置界面 ====================

class SettingsScreen(Screen):
    """设置界面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.build_ui(), 0.1)
    
    def build_ui(self):
        """构建界面"""
        self.clear_widgets()
        
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题
        title_card = Card(size_hint_y=None, height='80dp')
        title_card.add_widget(Label(
            text='套餐价格设置',
            font_size='24sp',
            bold=True,
            color=PRIMARY_COLOR
        ))
        main_layout.add_widget(title_card)
        
        # 说明
        info_card = Card(size_hint_y=None, height='60dp')
        info_card.add_widget(Label(
            text='设置各套餐类型的默认月费价格',
            font_size='14sp',
            color=GRAY_TEXT
        ))
        main_layout.add_widget(info_card)
        
        # 套餐列表
        self.scroll_view = ScrollView(do_scroll_x=False)
        self.settings_list = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=5)
        self.scroll_view.add_widget(self.settings_list)
        main_layout.add_widget(self.scroll_view)
        
        # 底部留白
        main_layout.add_widget(BoxLayout(size_hint_y=None, height='70dp'))
        
        self.add_widget(main_layout)
        self.refresh()
    
    def on_enter(self):
        """进入界面时刷新"""
        self.refresh()
    
    def refresh(self):
        """刷新设置数据"""
        self.settings_list.clear_widgets()
        self.settings_list.height = 0
        
        for name, info in MEAL_PLANS.items():
            card = self.create_price_card(name, info)
            self.settings_list.add_widget(card)
            self.settings_list.height += 130
    
    def create_price_card(self, plan_name, info):
        """创建价格设置卡片"""
        card = Card()
        card.height = '120dp'
        
        # 标题行
        header = BoxLayout(orientation='horizontal', size_hint_y=0.4)
        header.add_widget(Label(
            text=plan_name,
            font_size='20sp',
            bold=True,
            color=DARK_TEXT,
            size_hint_x=0.5,
            halign='left'
        ))
        header.add_widget(Label(
            text=info['description'],
            font_size='13sp',
            color=GRAY_TEXT,
            size_hint_x=0.5
        ))
        card.add_widget(header)
        
        # 价格输入行
        price_layout = BoxLayout(size_hint_y=0.6, spacing=10)
        
        self.price_inputs = getattr(self, 'price_inputs', {})
        self.price_inputs[plan_name] = TextInput(
            text=str(info['default_price']),
            input_filter='float',
            font_size='20sp',
            halign='center',
            multiline=False,
            size_hint_x=0.5
        )
        price_layout.add_widget(self.price_inputs[plan_name])
        price_layout.add_widget(Label(text='元/月', font_size='16sp', color=GRAY_TEXT, size_hint_x=0.25))
        
        save_btn = ActionButton(
            text='保存',
            color=PRIMARY_COLOR,
            font_size='14sp',
            size_hint_x=0.25,
            height='40dp'
        )
        save_btn.bind(on_press=lambda x: self.update_price(plan_name))
        price_layout.add_widget(save_btn)
        
        card.add_widget(price_layout)
        
        return card
    
    def update_price(self, plan_name):
        """更新套餐价格"""
        try:
            price = float(self.price_inputs[plan_name].text)
            MEAL_PLANS[plan_name]['default_price'] = price
            data_manager.save_config()
            self.refresh()
        except ValueError:
            pass


# ==================== 主应用程序 ====================

class MainApp(App):
    """主应用程序"""
    
    title = APP_NAME
    
    def build(self):
        """构建应用"""
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 添加各个屏幕
        sm.add_widget(AttendanceScreen(name='attendance'))
        sm.add_widget(StudentScreen(name='students'))
        sm.add_widget(BillScreen(name='bill'))
        sm.add_widget(SettingsScreen(name='settings'))
        
        # 创建主布局（包含底部导航）
        main_layout = BoxLayout(orientation='vertical')
        main_layout.add_widget(sm)
        
        # 底部导航栏
        nav_bar = BoxLayout(
            size_hint_y=None,
            height='60dp',
            padding=0
        )
        
        with nav_bar.canvas.before:
            Color(rgba=(1, 1, 1, 1))
            Rectangle(pos=nav_bar.pos, size=nav_bar.size)
            Color(rgba=(0.9, 0.9, 0.9, 1))
            Line(points=[nav_bar.x, nav_bar.top, nav_bar.right, nav_bar.top], width=1)
        
        # 导航按钮
        nav_buttons = [
            ('attendance', '📋', '考勤'),
            ('students', '👥', '学生'),
            ('bill', '📊', '账单'),
            ('settings', '⚙️', '设置')
        ]
        
        for screen_name, icon, label in nav_buttons:
            nav_btn = Button(
                background_color=(1, 1, 1, 1),
                on_release=lambda x, s=screen_name: self.switch_screen(s, sm)
            )
            
            btn_layout = BoxLayout(orientation='vertical', padding=5)
            btn_layout.add_widget(Label(text=icon, font_size='22sp', halign='center'))
            btn_layout.add_widget(Label(text=label, font_size='12sp', color=GRAY_TEXT, halign='center'))
            
            nav_btn.add_widget(btn_layout)
            nav_bar.add_widget(nav_btn)
        
        main_layout.add_widget(nav_bar)
        
        return main_layout
    
    def switch_screen(self, screen_name, sm):
        """切换屏幕"""
        sm.current = screen_name
        # 刷新当前屏幕
        if screen_name == 'attendance':
            sm.get_screen('attendance').refresh()
        elif screen_name == 'students':
            sm.get_screen('students').refresh()
        elif screen_name == 'bill':
            sm.get_screen('bill').load_bill()
        elif screen_name == 'settings':
            sm.get_screen('settings').refresh()


if __name__ == '__main__':
    MainApp().run()
