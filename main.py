import threading
from mainwindow import Ui_MainWindow
from portDialog import Ui_Dialog as port_dialog
from joystickDialog import Ui_Dialog as joystick_dialog
from axisSetDialog import Ui_Dialog as axis_dialog
import serial_widget_thread
from robot_control import Robot
from joystick_control import joystick_manager, flash_joyState_text, save_joy_options, load_joy_options
from robot_control import Robot
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog


main_window = Ui_MainWindow()
dialog_port = port_dialog()
dialog_joyconfig = joystick_dialog()
dialog_axis_add = axis_dialog()

QueryTimer = QTimer()
QueryTimer.setInterval(10)
app = QApplication(sys.argv)
w = QMainWindow()
diaPortAPP = QDialog()
diaJoyAPP  = QDialog()
axisAPP = QDialog()

dialog_joyconfig.setupUi(diaJoyAPP)
dialog_port.setupUi(diaPortAPP)
dialog_axis_add.setupUi(axisAPP)
main_window.setupUi(w)



SurgRobot = Robot(main_window=main_window)
JoyStick = joystick_manager(SurgRobot, main_window)
thread_listen    = serial_widget_thread.read_thr(SurgRobot, dialog_port)
thread_listen.name = "串口调试助手线程"
thread_joylisten = flash_joyState_text()
thread_joylisten.name = "手柄调试助手线程"

robo_options = {
    "temp_ports_list": [],
    "temp_joys_list" : [],
    "last_port"      : 0,
    "last_joy"       : 0,
    "end_char"       : 0,
}


def fresh_ports():
    ports, names = SurgRobot.scan_ports()    
    for k, i in enumerate(robo_options["temp_ports_list"]):
        if i not in names:
            main_window.com_select.removeItem(k+1)
    
    for k, i in zip(ports, names):
        if i not in robo_options["temp_ports_list"]:
            main_window.com_select.addItem(i)    
    robo_options["temp_ports_list"] = names


def fresh_joystick():
    joys = JoyStick.scan_joystick()
    for k, i in enumerate(robo_options["temp_joys_list"]):
        if i not in joys:
            main_window.joystick_select.removeItem(k+1)
    
    for  i in joys:
        if i not in robo_options["temp_joys_list"]:
            main_window.joystick_select.addItem(i)
    robo_options["temp_joys_list"] = joys


def func_for_show_ports(*args):
    """展示串口的函数"""
    fresh_ports()
    main_window.com_select.showPopup()


def func_for_select_port(*args):
    """选择连接到某个串口"""
    index = args[0]
    if index > 0:
        SurgRobot.open_robot_port(SurgRobot.port_list[index-1]) 
    else:
        SurgRobot.close_robot_port()
    robo_options["last_port"] = index


def func_for_show_joysticks(*args):
    """展示手柄的函数"""
    fresh_joystick()
    main_window.joystick_select.showPopup()


def func_for_select_joystick(*args):
    """连接并启动某个手柄的函数"""
    index = args[0]
    if index > 0:
        JoyStick.start_joystick(index-1)
    else:
        JoyStick.close_joystick()
    robo_options["last_joy"] = index
    
def func_for_gearlevel_change(*args):
    SurgRobot.gear_level = (main_window.gear_level_slider.value() * 0.2)
    print(SurgRobot.gear_level)
    pass

def func_for_send_serial_msg(*args):
    endings = ["", "\n", "\r", "\r\n"]
    msg = dialog_port.send_Input.text()
    msg += endings[dialog_port.end_select.currentIndex()]
    SurgRobot.write_ser(msg)
    dialog_port.send_Input.clear()

def open_serial_thread():
    """打开监听串口的后台线程"""
    global thread_listen
    thread_listen.start()

def open_joy_thread():
    """打开监听手柄的后台线程"""
    global thread_joylisten
    thread_joylisten.start()

def func_for_open_joySet_dialog(*args):
    dialog_joyconfig.joyStateShow.clear()
    global thread_joylisten
    JoyStick.close_joystick()
    index = robo_options["last_joy"]
    if index > 0:
        thread_joylisten.set_joy(robo_options["last_joy"]-1)
    else:
        dialog_joyconfig.joyStateShow.append("手柄未选择")

def func_for_close_joySet_dialog(*args):
    global thread_joylisten
    thread_joylisten.ignore_joy()
    index = robo_options["last_joy"]
    if index > 0:
        JoyStick.start_joystick(robo_options["last_joy"]-1)
    

def func_for_open_serial_dialog(*args):
    """打开串口小部件时运行的函数"""
    dialog_port.recv_Text.clear()
    if not SurgRobot.ser.isOpen():
        dialog_port.recv_Text.append("串口未打开")
    global thread_listen
    SurgRobot.flush_ser()
    thread_listen.show = True
    pass


def func_for_close_serial_dialog(*args):
    """关闭串口小部件时运行的函数"""
    global thread_listen
    thread_listen.show = False
    pass

def func_for_select_end_char(*args):
    '''串口监视器选择结束符的函数'''
    robo_options["end_char"]=args[0]


def func_for_print_args(*args):
    print(args)


def func_for_menu(*args):
    text = args[0].text()
    if text == "串口调试":
        diaPortAPP.exec()
    if text == "手柄映射设置":
        diaJoyAPP.exec()

def dialog_joy_setting_update(dict):
    dialog_joyconfig.nowSettingShow.clear()
    motoName = ["导管递送", "导丝递送", "导丝旋转"]
    for axis_bind_tuple in dict["axis"]:
        motoID, axis, fromLow, fromHigh, toLow, toHigh = axis_bind_tuple
        dialog_joyconfig.nowSettingShow.addItem(f"轴{axis}: {motoName[motoID]}\n    ({fromLow},{fromHigh})->({toLow},{toHigh})")
    pass
        

def bind_methods():
    """为各个小部件绑定函数"""
    global thread_listen
    # com_select
    main_window.com_select.mousePressEvent = func_for_show_ports
    main_window.com_select.currentIndexChanged.connect(func_for_select_port) 
    # joystick_select
    main_window.joystick_select.mousePressEvent = func_for_show_joysticks
    main_window.joystick_select.currentIndexChanged.connect(func_for_select_joystick)     
    # gear_level_slider
    main_window.gear_level_slider.setPageStep(1)
    main_window.gear_level_slider.valueChanged.connect(func_for_gearlevel_change)
    # menu
    main_window.menu.triggered.connect(func_for_menu)
    # dialog_port
    dialog_port.pushButton.clicked.connect(func_for_send_serial_msg)
    dialog_port.pushButton_2.clicked.connect(dialog_port.recv_Text.clear)
    dialog_port.end_select.currentIndexChanged.connect(func_for_select_end_char)
    dialog_port.AutoLast.clicked.connect(thread_listen.jump_to_last_line)
    thread_listen.worker.jump_sig.connect(dialog_port.recv_Text.setTextCursor)
    diaPortAPP.showEvent = func_for_open_serial_dialog
    diaPortAPP.closeEvent = func_for_close_serial_dialog
    # dialog_joy
    dialog_joyconfig.addSettingButton.clicked.connect(axisAPP.exec)
    dialog_joyconfig.nowSettingShow.itemDoubleClicked.connect(func_for_print_args)
    thread_joylisten.signal_boject.sender.connect(dialog_joyconfig.joyStateShow.setPlainText)
    thread_joylisten.signal_boject.dic_sender.connect(dialog_joy_setting_update)
    # dialog_joyconfig.joyStateShow.textCursor()
    diaJoyAPP.rejected.connect(func_for_close_joySet_dialog)
    diaJoyAPP.showEvent = func_for_open_joySet_dialog
    diaJoyAPP.closeEvent = func_for_close_joySet_dialog
    # buttons
    main_window.all_stop_button.clicked.connect(SurgRobot.all_stop) 
    main_window.cath_up_button.clicked.connect(save_joy_options)  
    pass

def close_methods(*args):
    """主窗口关闭时进行的动作"""
    save_options()
    thread_listen.isRunning = False
    thread_joylisten.isRunning = False
    SurgRobot.close_robot_port()
    JoyStick.close_joystick()

    

def init_methods(*args):
    """主函数开始运行时的动作"""
    load_joy_options()
    load_options()
    
    open_serial_thread()
    open_joy_thread()


def save_options():
    """导出配置到文件中"""
    import json as json
    with open("main_config.json", 'w') as js_file:
        js_string = json.dumps(robo_options, sort_keys=True, indent=4, separators=(',', ': '))
        js_file.write(js_string)

def load_options():
    """从文件中加载配置"""
    import json as json
    with open("main_config.json", 'r') as js_file:
        temp_robo_options = json.load(js_file)
    fresh_ports()
    fresh_joystick()
    if temp_robo_options["temp_ports_list"] == robo_options["temp_ports_list"]:
        main_window.com_select.setCurrentIndex(temp_robo_options["last_port"])

    if temp_robo_options["temp_joys_list"] == robo_options["temp_joys_list"]:
        main_window.joystick_select.setCurrentIndex(temp_robo_options["last_joy"])
    
    dialog_port.end_select.setCurrentIndex(temp_robo_options["end_char"])


if __name__ == "__main__":
    # app = QApplication(sys.argv)
    # w = QMainWindow()

    # main_window.setupUi(w)
    main_window.speed_UI_list = [main_window.cath_speed_lcd, 
                                 main_window.wire_speed_lcd,
                                 main_window.wire_rotSpeed_lcd]
    

    bind_methods()
    init_methods()
    

    w.show()
    w.closeEvent = close_methods
    sys.exit(app.exec())
