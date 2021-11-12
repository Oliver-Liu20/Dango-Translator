from selenium import webdriver
from traceback import format_exc
import time


# 音乐朗读模块实例化
def createSound(obj, config, logger) :

    obj.sound = Sound(config, logger)


# 音乐朗读模块
class Sound() :

    def __init__(self, config, logger) :

        self.config = config
        self.logger = logger
        url = "https://fanyi.qq.com/"

        try:
            # 使用谷歌浏览器
            option = webdriver.ChromeOptions()
            option.add_argument("--headless")
            self.browser = webdriver.Chrome(executable_path="./config/tools/chromedriver.exe",
                                            service_log_path="./logs/geckodriver.log",
                                            options=option)
        except Exception:
            self.logger.error(format_exc())

            try:
                # 使用火狐浏览器
                option = webdriver.FirefoxOptions()
                option.add_argument("--headless")
                self.browser = webdriver.Firefox(executable_path="./config/tools/geckodriver.exe",
                                                 service_log_path="./logs/geckodriver.log",
                                                 options=option)
            except Exception:
                self.logger.error(format_exc())

                try :
                    # 使用Edge浏览器
                    EDGE = {
                        "browserName": "MicrosoftEdge",
                        "version": "",
                        "platform": "WINDOWS",
                        "ms:edgeOptions": {
                            'extensions': [],
                            'args': [
                                '--headless',
                                '--disable-gpu',
                                '--remote-debugging-port=9222',
                            ]}
                    }
                    self.browser = webdriver.Edge(executable_path="../config/tools/msedgedriver.exe",
                                                     service_log_path="../logs/geckodriver.log",
                                                     capabilities=EDGE)
                except Exception:
                    self.logger.error(format_exc())
                    self.close()

        self.browser.get(url)
        self.browser.maximize_window()


    # 播放音乐
    def playSound(self, content, language) :

        try :
            try :
                self.browser.find_element_by_xpath(self.config["dictInfo"]["tencent_xpath"]).click()
            except Exception :
                pass

            # 清空文本框
            self.browser.find_element_by_xpath('/html/body/div[2]/div[2]/div[2]/div[1]/div[1]/textarea').clear()
            # 输入要朗读的文本
            self.browser.find_element_by_xpath('/html/body/div[2]/div[2]/div[2]/div[1]/div[1]/textarea').send_keys(content)
            self.browser.find_element_by_xpath('//*[@id="language-button-group-source"]/div[1]/span').click()
            # 选择朗读语种
            if language == "JAP" :
                self.browser.find_element_by_xpath('//*[@id="language-button-group-source"]/div[2]/ul/li[4]/span').click()
            elif language == "ENG" :
                self.browser.find_element_by_xpath('//*[@id="language-button-group-source"]/div[2]/ul/li[3]/span').click()
            elif language == "KOR" :
                self.browser.find_element_by_xpath('//*[@id="language-button-group-source"]/div[2]/ul/li[5]/span').click()
            else :
                return

            # 判断是否已经开始朗读
            while True :
                start = time.time()
                # 点击朗读键
                self.browser.find_element_by_xpath('/html/body/div[2]/div[2]/div[2]/div[1]/div[3]').click()
                time.sleep(0.1)
                try :
                    # 通过播放图标的css属性判断是否已经开始朗读
                    self.browser.find_element_by_css_selector('body > div.layout-container > div.textpanel > div.textpanel-container.clearfix > div.textpanel-source.active > div.textpanel-tool.tool-voice.ani')
                    break
                except Exception :
                    # 设置如果5s都无法播放就超时
                    now = time.time()
                    if now - start >= 5 :
                        return

            # 判断朗读是否结束
            while True :
                start = time.time()
                time.sleep(0.1)
                try :
                    # 通过播放图标的css属性判断是否已经结束朗读
                    self.browser.find_element_by_css_selector('body > div.layout-container > div.textpanel > div.textpanel-container.clearfix > div.textpanel-source.active > div.textpanel-tool.tool-voice.ani')
                    # 这是如果60s都无法结束就超时
                    now = time.time()
                    if now - start >= 60 :
                        return
                except Exception :
                    break

        except Exception :
            self.logger.error(format_exc())


    def close(self) :

        try :
            self.browser.close()
            self.browser.quit()
        except Exception :
            self.logger.error(format_exc())
        print("音乐模块关闭")