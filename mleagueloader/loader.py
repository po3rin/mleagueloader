import time
import json
import pandas as pd

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class MLEAGUELoader():
    """
    Mリーグのデータをスクレイピングする
    """

    def __init__(self, driver):
        self.driver = driver
        self.now_season = 2022

    def login_fun(self, _mail: str, _pass: str):
        self.driver.get("https://m-league.jp/supporter/login")
        id_input = self.driver.find_element(By.ID, "login_mail")
        id_input.send_keys(_mail)
        pass_input = self.driver.find_element(By.ID, "login_password")
        pass_input.send_keys(_pass)
        login_button = self.driver.find_elements(By.NAME, "login")
        login_button[1].click()

    def get_match_schedule(self, season: str):
        match_schedule_list = []

        if self.now_season == 2022:
            url = "https://m-league.jp/games"
        else:
            url = f"https://m-league.jp/games/{season}-season"
        self.driver.get(url)

        # 20xxシーズンは20xx+1まで開催
        for y in [season, season+1]:
            for m in range(1, 12+1, 1):
                    for d in range(1, 31+1, 1):
                        ymd = str(y) + str(m).zfill(2) + str(d).zfill(2)
                        if len(self.driver.find_elements(By.XPATH, f".//div[@id='js-modal-key{ymd}']")) == 1:
                            match_schedule_list += [ymd]

        return match_schedule_list

    def html2df(self, html):
        soup = BeautifulSoup(html, "html.parser")

        # 必要な個所だけ抽出
        start_mark = "UMP_PLAYER.init(true, true, \'"
        end_mark = "\', autoplay);"
        start_position = str(soup).find(start_mark) + len(start_mark)
        end_position = str(soup).find(end_mark)
        score = str(soup)[start_position:end_position]

        return pd.DataFrame(json.loads(score))

    def _load_game_data(self):
        # 制御するタブの移動
        self.driver.switch_to.window(self.driver.window_handles[1])
        # 文字コードをUTF-8に変換
        html = self.driver.page_source.encode('utf-8')

        # DataFrameに変換
        df = self.html2df(html)
        # 牌譜ビューアを閉じる
        self.driver.close()
        # 制御するタブの移動
        self.driver.switch_to.window(self.driver.window_handles[0])
        return df

    def load(self, match_schedule_list):
        self.driver.get("https://m-league.jp/games")

        dat_list = []
        button_count = 0
        # 試合日程は時系列にソート済み想定
        for ms in match_schedule_list:
            # 月選択
            tmp = self.driver.find_element(By.XPATH, f".//a[@href='/games/?mly={ms[0:4]}&mlm={int(ms[4:6])}#schedule']")
            tmp.click()
            # 日程選択
            tmp = self.driver.find_element(By.XPATH, f".//li[@data-target='key{ms}']")
            tmp.click()
            
            time.sleep(1)

            # 牌譜ビューアにアクセスするボタン取得
            button = self.driver.find_elements(By.XPATH, ".//button[@class='c-button -primary -small']")

            ### 第1試合
            button[button_count].click()
            d1 = self._load_game_data()
            dat_list += [d1]

            ### 第2試合
            button[button_count+1].click()
            d2 = self._load_game_data()
            dat_list += [d2]

            # ページのリセット
            self.driver.get("https://m-league.jp/games")
            # button_countを次の日程にズラす
            button_count += 2

            time.sleep(5)

        return pd.concat(dat_list).reset_index(drop=True)
