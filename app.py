from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from traceback import format_exc
import sys
import os

import utils.logger
import utils.config
import utils.screen_rate
import utils.check_font
import utils.thread
import utils.http
import utils.email
import utils.message
import utils.port
import utils.update
import utils.hwnd

import ui.login
import ui.register
import ui.translation
import ui.filter
import ui.range
import ui.settin
import ui.static.icon

import translator.update_chrome_driver
import translator.update_edge_driver
import translator.upload_trans_file


class DangoTranslator() :

    # 配置初始化
    def __init__(self) :

        # 错误日志
        self.logger = utils.logger.setLog()
        # 本地配置
        self.yaml = utils.config.openConfig(self.logger)
        # 版本号
        self.yaml["version"] = "4.3.1"
        # 配置中心
        self.yaml["dict_info"] = utils.config.getDictInfo(self.yaml["dict_info_url"], self.logger)
        # 屏幕分辨率
        self.yaml["screen_scale_rate"] = utils.screen_rate.getScreenRate(self.logger)
        # 保存配置
        utils.config.saveConfig(self.yaml, self.logger)


    # 登录
    def login(self) :

        if not self.login_ui.login() :
            return

        # 从云端获取配置信息
        self.config = utils.config.getDangoSettin(self)
        utils.config.configConvert(self)
        # 登录OCR服务获取token
        utils.thread.createThread(utils.http.loginDangoOCR, self)

        # 翻译界面
        self.translation_ui = ui.translation.Translation(self)
        self.login_ui.close()
        self.translation_ui.show()

        # 设置界面
        self.settin_ui = ui.settin.Settin(self)
        # 翻译界面设置页面按键信号
        self.translation_ui.settin_button.clicked.connect(self.clickSettin)
        # 翻译界面充电按钮信号
        self.translation_ui.battery_button.clicked.connect(self.clickBattery)

        # 屏蔽词界面
        self.filter_ui = ui.filter.Filter(self)
        # 范围框界面
        self.range_ui = ui.range.Range(self)
        self.translation_ui.hide_range_sign.connect(self.range_ui.hideRangeUI)

        # 检查邮箱
        thread = utils.thread.createCheckBindEmailQThread(self)
        thread.signal.connect(self.register_ui.showBindEmailMessage)
        utils.thread.runQThread(thread)

        # 自动启动本地OCR
        utils.thread.createThread(self.autoOpenOfflineOCR)
        # 界面置顶
        self.hwndObj = utils.hwnd.WindowHwnd(self)
        if self.settin_ui.set_top_use :
            self.hwndObj.run()

        # 同步翻译历史
        if self.config["agreeCollectUse"]:
            utils.thread.createThread(translator.upload_trans_file.proccess(self))


    # 按下充电键后做的事情
    def clickBattery(self) :

        self.translation_ui.unregisterHotKey()
        self.translation_ui.close()
        self.range_ui.close()
        self.settin_ui.tab_widget.setCurrentIndex(4)
        self.settin_ui.show()


    # 按下设置键后做的事情
    def clickSettin(self) :

        # 直接跳转到正在使用的ocr页签
        if self.settin_ui.online_ocr_use :
            self.settin_ui.ocr_tab_widget.setCurrentIndex(0)
        elif self.settin_ui.offline_ocr_use :
            self.settin_ui.ocr_tab_widget.setCurrentIndex(1)
        elif self.settin_ui.baidu_ocr_use :
            self.settin_ui.ocr_tab_widget.setCurrentIndex(2)

        self.translation_ui.unregisterHotKey()
        self.translation_ui.close()
        self.range_ui.close()
        self.settin_ui.show()


    # 自动打开本地OCR
    def autoOpenOfflineOCR(self) :

        if not self.config["offlineOCR"] :
            return
        if not utils.port.detectPort(self.yaml["port"]) :
            try :
                # 启动本地OCR
                os.startfile(self.yaml["ocr_cmd_path"])
            except Exception :
                self.logger.error(format_exc())


    # 初始化资源
    def InitLoadFile(self) :

        # 更新谷歌浏览器引擎文件
        utils.thread.createThread(translator.update_chrome_driver.updateChromeDriver, self.logger)
        # 更新Edge浏览器引擎文件
        utils.thread.createThread(translator.update_edge_driver.updateEdgeDriver, self.logger)

        # 更新ocr源码文件
        ocr_src_file = self.yaml["dict_info"]["ocr_src_file"]
        utils.update.updateOCRSrcFile(ocr_src_file, self.logger)
        # 加载注册界面图片
        qq_group_url = self.yaml["dict_info"]["register_image_url"]
        utils.http.downloadFile(qq_group_url, "./config/background/register.gif", self.logger)
        # 加载设置界面图片
        settin_image_url = self.yaml["dict_info"]["settin_image_url"]
        utils.http.downloadFile(settin_image_url, "./config/background/settin.jpg", self.logger)
        # 加载测试ocr图片
        test_image_url = self.yaml["dict_info"]["test_image"]
        utils.http.downloadFile(test_image_url, "./config/other/image.jpg", self.logger)


    # 主函数
    def main(self) :

        # 更新贴字翻译所需的pil运行库
        utils.update.updatePilFile(self.yaml, self.logger)
        # 自适应高分辨率
        QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        app = QApplication(sys.argv)

        # 连接配置中心
        if not self.yaml["dict_info"] :
            utils.message.serverClientFailMessage(self)
        # 加载静态资源
        ui.static.icon.initIcon(self.yaml["screen_scale_rate"])
        # 检查是否为测试版本
        utils.message.checkIsTestVersion(self)
        # 检查字体
        utils.check_font.checkFont(self.logger)
        # 检查版本更新线程
        if "Beta" not in self.yaml["version"] :
            thread = utils.thread.createCheckVersionQThread(self)
            thread.signal.connect(lambda: utils.message.showCheckVersionMessage(self))
            utils.thread.runQThread(thread)
        # 初始化图片资源
        utils.thread.createThread(self.InitLoadFile)

        # 登录界面
        self.login_ui = ui.login.Login(self)
        self.login_ui.show()
        self.login_ui.login_button.clicked.connect(self.login)

        # 注册页面
        self.register_ui = ui.register.Register(self)
        # 登录界面注册按键
        self.login_ui.register_button.clicked.connect(self.register_ui.clickRegister)
        # 登录界面忘记密码按键
        self.login_ui.forget_password_button.clicked.connect(self.register_ui.clickForgetPassword)

        # 自动登录
        if self.yaml["auto_login"] :
            self.login()

        app.exit(app.exec_())


if __name__ == "__main__" :

    app = DangoTranslator()
    app.main()