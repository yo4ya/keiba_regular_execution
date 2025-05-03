# スクレイピングに必要なモジュール
import numpy as np  # csv操作
import re  # 正規表現
import sys  # エラー検知用
import time  # sleep用
import requests
from bs4 import BeautifulSoup
import pandas as pd
import itertools  # レースIDの作成
import datetime
from retry.retry_decorator import retry
from notify import send_slack_notify
from logging_setup import get_logger

logger = get_logger("Keiba")



result_df = pd.DataFrame()  # ファイルに出力するためのデータフレームb
current_date: datetime.date  # 現在のレース日のための宣言
Exception_Horse: int  # 出走しなかった馬のための例外処理
cancel_umaban_list=[]   # 出走しなかった馬のための例外処理(未発走限定)
Site_Exists: bool  # サイトが存在しなかったときの例外処理

headers = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def isint(s):  # 整数値を表しているかどうかを判定
    try:
        int(s, 10)  # 文字列を実際にint関数で変換してみる
    except ValueError:
        return False
    else:
        return True


def isfloat(s):  # 浮動小数点数値を表しているかどうかを判定
    try:
        float(s)  # 文字列を実際にfloat関数で変換してみる
    except ValueError:
        return False
    else:
        return True


def current_data(year, place, race_count, day, race_num):

    global result_df
    global current_date
    global Exception_Horse
    global Site_Exists
    Exception_Horse = 100
    result_df = pd.DataFrame()

    YEAR = [str(year).zfill(2)]
    PLACE = [str(place).zfill(2)]  # 05
    RACE_COUNT = [str(race_count).zfill(2)]
    DAYS = [str(day).zfill(2)]
    RACE_NUM = [str(race_num).zfill(2)]
    race_ids = list(itertools.product(YEAR, PLACE, RACE_COUNT, DAYS, RACE_NUM))


    # サイトURLの作成
    SITE_URL = ["https://race.netkeiba.com/race/shutuba.html?race_id={}&rf=race_list".format(
        ''.join(race_id)) for race_id in race_ids]
    res = requests.get(SITE_URL[0], headers=headers)
    soup = BeautifulSoup(res.content, 'html.parser')

    # title タグ、開催月日を取得する
    title_text = soup.find('title').get_text()
    if title_text == '  |    - netkeiba.com':
        # raise ValueError('サイトが存在しません')
        print('サイトが存在しません')
        Site_Exists = False
        return None
    elif "新馬" in title_text or "障害" in title_text:
        Site_Exists = False
        return None

    print(title_text)
    Site_Exists = True

    Month_Day = soup.find_all('meta')[5]
    Month_Day = Month_Day.get('content')
    # Month = re.findall(r'年(.*)月', Month_Day)[0]
    # Day = re.findall(r'月(.*)日', Month_Day)[0]
    Month = re.findall(r'\d+', Month_Day)[1]
    Day = re.findall(r'\d+', Month_Day)[2]
    current_date = datetime.date(
        year=int(YEAR[0]), month=int(Month), day=int(Day))

    # 以下、tableの情報はtbodyタグの中からの抽出
    tbody = soup.find('tbody')
    if tbody == None:  # レースが開催されていなかったときの処理
        Site_Exists = False
        return

    # Cancel_Txtクラスを持つすべての<td>タグを検索
    cancel_td_tags = soup.find_all('td', class_='Cancel_Txt')

    # 各Cancel_Txtタグをループして処理
    for cancel_td in cancel_td_tags:
        # Cancel_Txtタグの直前の<td>タグを見つける
        previous_td = cancel_td.find_previous('td')

        # 直前の<td>タグのテキストを取得してリストに追加
        if previous_td:
            #results.append(previous_td.get_text().strip())
            cancel_umaban=int(previous_td.get_text().strip())
            cancel_umaban_list.append(cancel_umaban-1)


    # 枠取得
    Wakus = soup.find_all('td', class_=re.compile(r'\bWaku\d+\s+Txt_C\b'))
    Wakus_list = []
    for i, Waku in enumerate(Wakus):
        if i in cancel_umaban_list:  # 出走しなかった馬の例外処理
            continue
        Waku = Waku.get_text().replace('\n', '')
        # リスト作成
        Wakus_list.append(Waku)

    # 馬番
    Horse_Numbers = soup.find_all('td', class_=re.compile("Umaban"))
    Horse_Numbers_list = []
    for i, Horse_Number in enumerate(Horse_Numbers):
        if i in cancel_umaban_list:  # 出走しなかった馬の例外処理
            continue
        Horse_Number = Horse_Number.get_text().replace('\n', '')
        Horse_Numbers_list.append(Horse_Number)

    # 馬名取得
    Horse_Names = []
    for horse_name_span in soup.find_all('span', class_='HorseName'):
        if horse_name_span.find('a'):  # aタグを持つspanだけを取得
            Horse_Names.append(horse_name_span)
    # Horse_Names.pop(0)
    Horse_Names_list = []
    for i, Horse_Name in enumerate(Horse_Names):
        if i in cancel_umaban_list:  # 出走しなかった馬の例外処理
            continue
        # 馬名のみ取得(lstrip()先頭の空白削除，rstrip()改行削除)
        Horse_Name = Horse_Name.get_text().lstrip().rstrip('\n')
        # リスト作成
        Horse_Names_list.append(Horse_Name)

    # 厩舎取得
    Horse_Houses=soup.find_all('td', class_="Trainer")
    Horse_Houses_list=[]
    for i, Horse_House in enumerate(Horse_Houses):
        if i in cancel_umaban_list:  # 出走しなかった馬の例外処理
            continue
        # 馬名のみ取得(lstrip()先頭の空白削除，rstrip()改行削除)
        Horse_House = Horse_House.find('span').get_text().lstrip().rstrip('\n')
        # リスト作成
        Horse_Houses_list.append(Horse_House)
        
    # 性別、年齢の取得
    sex_ages = soup.find_all('td', class_=re.compile('Barei'))
    Sex_list = []
    Age_list = []
    for i, sex_age in enumerate(sex_ages):
        #if i in cancel_umaban_list:  # 出走しなかった馬の例外処理
        #    continue
        sex_age = sex_age.get_text().lstrip().rstrip('\n')
        sex = sex_age[:1]
        age = sex_age[1:]
        Sex_list.append(sex)
        Age_list.append(age)

    # 斤量
    #Jockey_Weits = soup.find_all('td', class_='Txt_C')
    Jockey_Weits = soup.select('td[class="Txt_C"]')
    Jockey_Weits_list = []
    for i, Jockey_Weight in enumerate(Jockey_Weits):
        #if i in cancel_umaban_list:  # 出走しなかった馬の例外処理
        #    continue
        Jockey_Weight = Jockey_Weight.get_text().replace('\n', '')
        Jockey_Weits_list.append(Jockey_Weight)

    # 騎手
    Jockeys = soup.find_all('td', class_="Jockey")
    Jockeys_list = []
    for i, Jockey in enumerate(Jockeys):
        if i in cancel_umaban_list:  # 出走しなかった馬の例外処理
            continue
        Jockey = Jockey.get_text().lstrip().rstrip('\n').rstrip(' ')
        Jockeys_list.append(Jockey)

    """
    # タイム
    Times = tbody.find_all('span', class_="RaceTime")
    Times_list = []
    Minutes_list = []
    Seconds_list = []
    for i, Time in enumerate(Times):
        if i == 2*Exception_Horse:  # 出走しなかった馬の例外処理
            break
        Time = Time.get_text()
        Times_list.append(Time)
    Times_list = Times_list[0::2]
    [Minutes_list.append(time[0]) for time in Times_list]
    [Seconds_list.append(time[2:]) for time in Times_list]
    Times_list = np.array(list(map(int, Minutes_list))) * \
        60+np.array(list(map(float, Seconds_list)))
    """

    # 人気取得
    Ninkis = tbody.find_all('span', class_='OddsPeople')
    Ninkis_list = []
    for i, Ninki in enumerate(Ninkis):
        if i in cancel_umaban_list:  # 出走しなかった馬の例外処理
            continue
        Ninki = Ninki.get_text()
        # リスト作成
        Ninkis_list.append(Ninki)

    # オッズ取得
    Odds = tbody.find_all('td', class_='Odds Txt_R')
    Odds_list = []
    for i, Odd in enumerate(Odds):
        if i in cancel_umaban_list:  # 出走しなかった馬の例外処理
            continue
        Odd = Odd.get_text().lstrip().rstrip('\n')
        # リスト作成
        Odds_list.append(Odd)

    """"
    # 上がり3ハロン取得
    Three_Fs = tbody.find_all('td', class_='Time')
    Three_Fs_list = []
    for i, Three_F in enumerate(Three_Fs):
        if i == 3*Exception_Horse:  # 出走しなかった馬の例外処理
            break
        Three_F = Three_F.get_text().lstrip().rstrip('\n')
        # リスト作成
        Three_Fs_list.append(Three_F)
    Three_Fs_list = Three_Fs_list[2::3]
    """

    # 馬体重、増減取得
    Horse_Weights = soup.find_all('td', class_="Weight")
    Horse_Weights_list = []
    Zougens_list = []
    for i, Horse_Weight in enumerate(Horse_Weights):
 
        content = Horse_Weight.get_text().lstrip().rstrip('\n')
        Horse_Weight = re.search(r'\d+(?=\()', content)
        if Horse_Weight:
            Horse_Weight=int(Horse_Weight.group())
        else:
            Horse_Weight=np.nan
        Horse_Weights_list.append(Horse_Weight)

        Zougen = re.search(r'(?<=\()\s*[+-]?\d+\s*(?=\))', content)
        if Zougen:
            Zougen=int(Zougen.group())
        else:
            Zougen=np.nan
        Zougens_list.append(Zougen)

    # コース,距離取得
    Distance_Course = soup.find_all('span')
    Distance_Course = re.search(r'.[0-9]+m', str(Distance_Course))
    Course = Distance_Course.group()[0]
    Distance = re.sub("\\D", "", Distance_Course.group())

    # 左右、天候、馬場状態取得
    RL_Weather_Condition = soup.find('div', class_='RaceData01')
    RL_Weather_Condition = RL_Weather_Condition.get_text()
    # 以下はRL_Wether_Conditionからそれぞれを抽出している
    # re.findall()はリストを返すため、ほしい部分をさらに抽出する
    RL = re.findall(r'\((.*)\)', RL_Weather_Condition)[0]
    Weather = re.findall(r'天候:.', RL_Weather_Condition)[0][3]
    Condition = re.findall(r'馬場:.', RL_Weather_Condition)[0][3]

    # 優勝賞金取得
    Prize = soup.find_all('span')
    Prize = re.findall(r'本賞金:(\d+)', str(Prize))[0]

    # ジョッキーの獲得賞金
    Jockey_Prizes_list=[]
    Jockey_soups=soup.find_all('td', class_='Jockey')
    for i, Jockey_soup in enumerate(Jockey_soups):
        if i in cancel_umaban_list:  # 出走しなかった馬の例外処理
            continue
        time.sleep(2)
        Jockey_url=Jockey_soup.find('a')['href']
        Jockey_url=Jockey_url.replace('/recent','')
        Jockey_res=requests.get(Jockey_url, headers=headers)
        Jockey_soup=BeautifulSoup(Jockey_res.content, 'html.parser')
        
        table = Jockey_soup.find('table', class_='nk_tb_common race_table_01')

        # 各年度の収得賞金を抽出
        total_prize_money = 0
        average_count=0
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            # 行に少なくとも1つのtdタグがあるか確認
            if cells:
                year = cells[0].text.strip()
                if not year.isdigit():
                    continue
                prize_money = cells[-2].text.strip()  # 収得賞金は最後から2番目のセル
                # 過去三年の平均獲得賞金を計算
                if int(year) < int(YEAR[0]) and int(year) > int(YEAR[0])-4:
                    # 収得賞金を数値に変換して累計
                    prize_money = float(prize_money.replace(',', ''))  # カンマを削除
                    total_prize_money += prize_money
                    average_count+=1
        if average_count==0:
            Jockey_Prizes_list.append(total_prize_money)
        else:
            Jockey_Prizes_list.append(int(total_prize_money/average_count))

    # 調教
    time.sleep(2)

    TRAINING_URL = ["https://race.netkeiba.com/race/oikiri.html?race_id={}&type=3&rf=shutuba_submenu".format(
        ''.join(race_id)) for race_id in race_ids]
    res = requests.get(TRAINING_URL[0], headers=headers)
    soup = BeautifulSoup(res.content, 'html.parser')

    Trainings = soup.find_all('tr', class_=re.compile('OikiriDataHead'))
    Trainings_list = []
    #print(Trainings[0].find('td', class_=re.compile('Rank')).get_text())
    for i in Horse_Numbers_list:
        for Training_data in Trainings:
            umaban = Training_data.find('td', class_='Umaban').get_text()
            if i == umaban:
                Training = Training_data.find(
                    'td', class_=re.compile('Rank')).get_text()
                Trainings_list.append(Training)
                continue
    logger.info('waku: length=%d, values=%s', len(Wakus_list), Wakus_list)
    logger.info("Horse_Numbers_list: length=%d, values=%s", len(Horse_Numbers_list), Horse_Numbers_list)
    logger.info("Horse_Names_list: length=%d, values=%s", len(Horse_Names_list), Horse_Names_list)
    logger.info("Sex_list: length=%d, values=%s", len(Sex_list), Sex_list)
    logger.info("Age_list: length=%d, values=%s", len(Age_list), Age_list)
    logger.info("Jockey_Weits_list: length=%d, values=%s", len(Jockey_Weits_list),Jockey_Weits_list)
    logger.info("Jockeys_list: length=%d, values=%s", len(Jockeys_list),Jockeys_list)
    logger.info("Ninkis_list: length=%d, values=%s", len(Ninkis_list),Ninkis_list)
    logger.info("Odds_list: length=%d, values=%s", len(Odds_list),Odds_list)
    logger.info("Horse_Houses_list: length=%d, values=%s", len(Horse_Houses_list),Horse_Houses_list)
    logger.info("Horse_Weights_list: length=%d, values=%s", len(Horse_Weights_list),Horse_Weights_list)
    logger.info("Zougens_list: length=%d, values=%s", len(Zougens_list),Zougens_list)
    logger.info("Jockey_Prizes_list: length=%d, values=%s", len(Jockey_Prizes_list),Jockey_Prizes_list)
    logger.info("Trainings_list: length=%d, values=%s", len(Trainings_list),Trainings_list)
    '''
    

    print(len(Three_Fs_list))
    print(len(Times_list))
    print(Jockeys_list)
        '上がり3ハロン': Three_Fs_list,
        'タイム': Times_list,
    '''

    df = pd.DataFrame({
        'Race_ID': ''.join(race_ids[0]),  # ループで回すときはここを修正##########
        'Year': YEAR[0],
        'Month': Month,
        'Date': Day,
        'Race_Count': RACE_COUNT[0],  # ここも要修正？
        'Day': DAYS[0],  # ここも要修正？
        'Race_Num': RACE_NUM[0],  # ここも要修正？
        'Prize': Prize,
        'Sum_Num': len(Wakus_list),
        'Tansho':np.nan,
        'Fukusho':np.nan,
        'Umaren':np.nan,
        'Wide':np.nan,
        'Umatan':np.nan,
        'Fuku3':np.nan,
        'Tan3':np.nan,
        'Rank': np.nan,
        # 'Rank': Ranks_list,
        'Waku': Wakus_list,
        'Horse_Num': Horse_Numbers_list,
        'Horse_Name': Horse_Names_list,
        'Sex': Sex_list,
        'Age': Age_list,
        'Jockey_Weight': Jockey_Weits_list,
        'Jockey': Jockeys_list,
        'Jockey_Prize': Jockey_Prizes_list,
        'Ninki': np.nan,
        # 'Ninki': Ninkis_list,
        'Odds': np.nan,
        # 'Odds': Odds_list,
        'Horse_House': Horse_Houses_list,
        #'Horse_Weight': np.nan,
        'Horse_Weight': Horse_Weights_list,
        #'Weight_Change': np.nan,
        'Weight_Change': Zougens_list,
        'Course': Course,
        'Distanse': Distance,
        'Right_Left': RL,
        'Weather': Weather,
        'Condition': Condition,
        'Training': Trainings_list,
    })
    result_df = pd.concat([result_df, df], axis=0)


def past_data(year, place, race_count, day, race_num):
    global result_df
    global current_date
    global Site_Exists

    if Site_Exists == False:
        return

    Horse_Count = 1

    YEAR = [str(year).zfill(2)]
    PLACE = [str(place).zfill(2)]
    RACE_COUNT = [str(race_count).zfill(2)]
    DAYS = [str(day).zfill(2)]
    RACE_NUM = [str(race_num).zfill(2)]
    race_ids = list(itertools.product(YEAR, PLACE, RACE_COUNT, DAYS, RACE_NUM))

    # サイトURLの作成
    SITE_URL = ["https://race.netkeiba.com/race/shutuba.html?race_id={}".format(
        ''.join(race_id)) for race_id in race_ids]

    res = requests.get(SITE_URL[0], headers=headers)
    # res = requests.get(
    #    "https://race.netkeiba.com/race/shutuba.html?race_id=202109050411&rf=race_submenu")
    soup = BeautifulSoup(res.content, 'html.parser')

    # 馬名取得
    Horse_Names = []
    for horse_name_span in soup.find_all('span', class_='HorseName'):
        if horse_name_span.find('a'):  # aタグを持つspanだけを取得
            Horse_Names.append(horse_name_span)
    Horse_Names_list = []
    for i, Horse_Name in enumerate(Horse_Names):
        if i in cancel_umaban_list:  # 出走しなかった馬の例外処理
            continue
        # 馬名のみ取得(lstrip()先頭の空白削除，rstrip()改行削除)
        Horse_Name = Horse_Name.get_text().lstrip().rstrip('\n')
        # リスト作成
        Horse_Names_list.append(Horse_Name)

    # 過去データのURL取得
    URLs_list = []
    tbody = soup.find('tbody')
    for i in range(len(Horse_Names_list)):
        URL = soup.find('a', title=Horse_Names_list[i])
        URL = URL.get('href')
        URLs_list.append(URL)

    Elapsed_Days_list = []
    p_Past_Dates_list = [[], [], []]
    p_Places_list = [[], [], []]
    p_Race_Counts_list = [[], [], []]
    p_Days_list = [[], [], []]
    p_Race_Numbers_list = [[], [], []]
    p_Horse_Numbers_list = [[], [], []]
    p_Ranks_list = [[], [], []]
    p_Courses_list = [[], [], []]
    p_Dists_list = [[], [], []]
    p_Three_Fs_list = [[], [], []]
    p_Conditions_list = [[], [], []]
    p_Prizes_list = [[], [], []]
    p_Condition_Index_list = [[], [], []]
    p_Time_Index_list = [[], [], []]
    f_Prize_list = []
    m_Prize_list = []
    mf_Prize_list = []
    for url in URLs_list:

        time.sleep(2)
        print(str(Horse_Count)+'頭目 : '+Horse_Names_list[Horse_Count-1])
        Horse_Count += 1

    # ログインする
        login_info = {'login_id': 'takahara.yoshiya@gmail.com',
                      'pswd': 'Aa0713525'}
        session = requests.session()
        url_login = 'https://regist.netkeiba.com/account/?pid=login&action=auth'
        ses = session.post(url_login, data=login_info)
        res_past = session.get(url, headers=headers)
        soup_past = BeautifulSoup(res_past.content, 'html.parser')
        tbodys = soup_past.find_all('tbody')

        for tbody_i in tbodys:  # 順位とかの表の前に余分な表があった時に回避する用
            if len(tbody_i.find_all('a', href=re.compile('^/race/list/'))) > 0:
                tbody = tbody_i
                break
        # 開催日
        p_Dates_list = []
        p_Dates = tbody.find_all('a', href=re.compile('^/race/list/'))
        for p_Date in p_Dates:
            p_Date = p_Date.get_text()
            year = int(p_Date[0:4])
            month = int(p_Date[5:7])
            day = int(p_Date[8:10])
            p_Dates_list.append(datetime.date(year, month, day))

        # 過去の開催日が何行目からか見つける
        for i, p_Date in enumerate(p_Dates_list):
            recent_date = 1000  # 過去の開催日がないときの例外処理用
            if current_date > p_Date:
                recent_date = i
                break


        # 過去の開催日
        for i in range(recent_date, recent_date+3):
            if i+1 > len(p_Dates):  # 過去データが3つないとき
                p_Past_Dates_list[i-recent_date].append(np.nan)
            else:
                p_Date = p_Dates[i].get_text()
                year = int(p_Date[0:4])
                month = int(p_Date[5:7])
                day = int(p_Date[8:10])
                p_Past_Dates_list[i -
                                  recent_date].append(datetime.date(year, month, day))

        # 開催場所、回数、日数
        p_Places_RaceCounts_Days = tbody.find_all(
            'a', href=re.compile('^/race/sum/'))
        for i in range(recent_date, recent_date+3):
            if i+1 > len(p_Places_RaceCounts_Days):
                p_Places_list[i-recent_date].append(np.nan)
                p_Race_Counts_list[i-recent_date].append(np.nan)
                p_Days_list[i-recent_date].append(np.nan)
            else:
                p_Place_RaceCount_Day = p_Places_RaceCounts_Days[i].get_text()
                """
                p_Places_list[i-1].append(p_Place_RaceCount_Day[1:-1])
                p_Race_Counts_list[i-1].append(p_Place_RaceCount_Day[0])
                p_Days_list[i-1].append(p_Place_RaceCount_Day[3])
                """
                # print(re.sub(r'\d', '', p_Place_RaceCount_Day))
                p_Places_list[i-recent_date].append(re.sub(r'\d',
                                                           '', p_Place_RaceCount_Day))
                # p_Race_Counts_list[i-1].append(re.sub(r'\d', '', p_Place_RaceCount_Day))
                # p_Days_list[i-1].append(re.findall(r'\d+', p_Place_RaceCount_Day)[1])

        # レース数、馬番、順位
        txt_right = tbody.find_all('td', class_='txt_right')
        for i in range(recent_date, recent_date+3):
            if 0+i*11+1 > len(txt_right):
                p_Race_Numbers_list[i-recent_date].append(np.nan)
                p_Horse_Numbers_list[i-recent_date].append(np.nan)
                p_Ranks_list[i-recent_date].append(np.nan)
                p_Condition_Index_list[i-recent_date].append(np.nan)
                p_Time_Index_list[i-recent_date].append(np.nan)
            else:
                p_Race_Numbers_list[i -
                                    recent_date].append(txt_right[0+i*11].get_text())
                p_Horse_Numbers_list[i -
                                     recent_date].append(txt_right[3+i*11].get_text())
                p_Ranks_list[i -
                             recent_date].append(txt_right[6+i*11].get_text())
                p_Condition_Index_list[i -
                                       recent_date].append(txt_right[7+i*11].get_text().lstrip().rstrip('\n'))
                p_Time_Index_list[i -
                                  recent_date].append(txt_right[10+i*11].get_text().lstrip().rstrip('\n'))

        # コース、距離、馬場状態、上がり3ハロン
        # 表のどこにあるか+表の列数(28)*何行目か(i)
        td = tbody.find_all('td')
        for i in range(recent_date, recent_date+3):
            if 15+i*28+1 > len(td):
                p_Courses_list[i-recent_date].append(np.nan)
                p_Dists_list[i-recent_date].append(np.nan)
                p_Conditions_list[i-recent_date].append(np.nan)
                p_Three_Fs_list[i-recent_date].append(np.nan)
                p_Prizes_list[i-recent_date].append(np.nan)
            else:
                p_Courses_list[i-recent_date].append(td[14+i*28].get_text()[0])
                p_Dists_list[i-recent_date].append(td[14+i*28].get_text()[1:])
                p_Conditions_list[i-recent_date].append(td[15+i*28].get_text())
                p_Three_Fs_list[i-recent_date].append(td[22+i*28].get_text())
                p_Prizes_list[i-recent_date].append(td[27+i *
                                                       28].get_text().replace('\xa0', ''))

# 父親の情報
        time.sleep(2)
        URL_f = soup_past.find_all('td', class_='b_ml')[0].find('a')
        URL_f = URL_f.get('href')
        URL_f = URL_f.replace('ped', 'result')
        URL_f = 'https://db.netkeiba.com/'+URL_f

        res_f = session.get(URL_f, headers=headers)
        soup_f = BeautifulSoup(res_f.content, 'html.parser')
        tbodys = soup_f.find_all('tbody')

        if len(tbodys) > 0:
            for tbody_i in tbodys:  # 順位とかの表の前に余分な表があった時に回避する用
                if len(tbody_i.find_all('a', href=re.compile('^/race/list/'))) > 0:
                    tbody = tbody_i
                    break

            tr = tbody.find_all('tr')
            f_race_num = int(len(tr))
            f_Prize_sum = 0
            for i in range(f_race_num):
                f_Prize = tr[i].find_all(
                    'td')[-1].get_text().lstrip().rstrip('\n')
                f_Prize = f_Prize.replace(',', '')
                if (f_Prize != '') and isfloat(f_Prize):
                    f_Prize_sum += float(f_Prize)

        else:
            f_Prize_sum = np.nan

        f_Prize_list.append(f_Prize_sum)

        # 母親の情報
        time.sleep(2)
        URL_m = soup_past.find_all('td', class_='b_fml')[1].find('a')
        URL_m = URL_m.get('href')
        URL_m = URL_m.replace('ped', 'result')
        URL_m = 'https://db.netkeiba.com/'+URL_m

        res_m = session.get(URL_m, headers=headers)
        soup_m = BeautifulSoup(res_m.content, 'html.parser')
        tbodys = soup_m.find_all('tbody')

        if len(tbodys) > 0:
            for tbody_i in tbodys:  # 順位とかの表の前に余分な表があった時に回避する用
                if len(tbody_i.find_all('a', href=re.compile('^/race/list/'))) > 0:
                    tbody = tbody_i
                    break

            tr = tbody.find_all('tr')
            m_race_num = int(len(tr))
            m_Prize_sum = 0
            for i in range(m_race_num):
                m_Prize = tr[i].find_all(
                    'td')[-1].get_text().lstrip().rstrip('\n')
                m_Prize = m_Prize.replace(',', '')
                if (m_Prize != '') and isfloat(m_Prize):
                    m_Prize_sum += float(m_Prize)

        else:
            m_Prize_sum = np.nan

        m_Prize_list.append(m_Prize_sum)

        # 母方の父親の情報
        time.sleep(2)
        URL_mf = soup_past.find_all('td', class_='b_fml')[1].find('a')
        URL_mf = URL_mf.get('href')
        URL_mf = URL_mf.replace('ped', 'result')
        URL_mf = 'https://db.netkeiba.com/'+URL_mf

        res_mf = session.get(URL_mf, headers=headers)
        soup_mf = BeautifulSoup(res_mf.content, 'html.parser')
        tbodys = soup_mf.find_all('tbody')

        if len(tbodys) > 0:
            for tbody_i in tbodys:  # 順位とかの表の前に余分な表があった時に回避する用
                if len(tbody_i.find_all('a', href=re.compile('^/race/list/'))) > 0:
                    tbody = tbody_i
                    break

            tr = tbody.find_all('tr')
            mf_race_num = int(len(tr))
            mf_Prize_sum = 0
            for i in range(mf_race_num):
                mf_Prize = tr[i].find_all(
                    'td')[-1].get_text().lstrip().rstrip('\n')
                mf_Prize = mf_Prize.replace(',', '')
                if (mf_Prize != '') and isfloat(mf_Prize):
                    mf_Prize_sum += float(mf_Prize)

        else:
            mf_Prize_sum = np.nan

        mf_Prize_list.append(mf_Prize_sum)
        """
        print(p_Places_list)
        print(p_Race_Numbers_list)
        print(p_Courses_list)
        print(p_Dists_list)
        print(p_Conditions_list)
        print(p_Three_Fs_list)

    print(len(p_Places_list[0]), len(p_Places_list[1]), len(p_Places_list[2]))
    print(len(p_Race_Counts_list[0]), len(p_Race_Counts_list[1]), len(p_Race_Counts_list[2]))
    print(len(p_Days_list[0]), len(p_Days_list[1]), len(p_Days_list[2]))
    print(len(p_Dates_list[0]), len(p_Dates_list[1]), len(p_Dates_list[2]))
    print(len(p_Race_Numbers_list[0]), len(p_Race_Numbers_list[1]), len(p_Race_Numbers_list[2]))
    print(len(p_Horse_Numbers_list[0]), len(p_Horse_Numbers_list[1]), len(p_Horse_Numbers_list[2]))
    print(len(p_Ranks_list[0]), len(p_Ranks_list[1]), len(p_Ranks_list[2]))
    print(len(p_Courses_list[0]), len(p_Courses_list[1]), len(p_Courses_list[2]))
    print(len(p_Dists_list[0]), len(p_Dists_list[1]), len(p_Dists_list[2]))
    print(len(p_Conditions_list[0]), len(p_Conditions_list[1]), len(p_Conditions_list[2]))
    """

    # 現在のレースと直近のレースの日数差
    for past_date in p_Past_Dates_list[0]:
        if type(past_date) == float:
            Elapsed_Days_list.append(np.nan)
        else:
            Elapsed_Days_list.append(current_date - past_date)

    """
    '回数1': p_Race_Counts_list[0],
    '回数2': p_Race_Counts_list[1],
    '回数3': p_Race_Counts_list[2],
    '日数1': p_Days_list[0],
    '日数2': p_Days_list[1],
    '日数3': p_Days_list[2],
    """
    
    logger.info("Elapsed_Days_list: length=%d, values=%s", len(Elapsed_Days_list), Elapsed_Days_list)
    logger.info("p_Places_list: length=%d, values=%s", len(p_Places_list), p_Places_list)
    logger.info("p_Past_Dates_list: length=%d, values=%s", len(p_Past_Dates_list), p_Past_Dates_list)
    logger.info("p_Race_Numbers_list: length=%d, values=%s", len(p_Race_Numbers_list), p_Race_Numbers_list)
    logger.info("p_Horse_Numbers_list: length=%d, values=%s", len(p_Horse_Numbers_list), p_Horse_Numbers_list)
    logger.info("p_Ranks_list: length=%d, values=%s", len(p_Ranks_list), p_Ranks_list)
    logger.info("p_Courses_list: length=%d, values=%s", len(p_Courses_list), p_Courses_list)
    logger.info("p_Dists_list: length=%d, values=%s", len(p_Dists_list), p_Dists_list)
    logger.info("p_Conditions_list: length=%d, values=%s", len(p_Conditions_list), p_Conditions_list)
    logger.info("p_Three_Fs_list: length=%d, values=%s", len(p_Three_Fs_list), p_Three_Fs_list)
    logger.info("p_Prizes_list: length=%d, values=%s", len(p_Prizes_list), p_Prizes_list)
    logger.info("p_Condition_Index_list: length=%d, values=%s", len(p_Condition_Index_list), p_Condition_Index_list)
    logger.info("p_Time_Index_list: length=%d, values=%s", len(p_Time_Index_list), p_Time_Index_list)
    logger.info("f_Prize_list: length=%d, values=%s", len(f_Prize_list), f_Prize_list)
    logger.info("m_Prize_list: length=%d, values=%s", len(m_Prize_list), m_Prize_list)
    logger.info("mf_Prize_list: length=%d, values=%s", len(mf_Prize_list), mf_Prize_list)
    
    df = pd.DataFrame({
        'Elapsed_Day': Elapsed_Days_list,
        'Place1': p_Places_list[0],
        'Place2': p_Places_list[1],
        'Place3': p_Places_list[2],
        'Day1': p_Past_Dates_list[0],
        'Day2': p_Past_Dates_list[1],
        'Day3': p_Past_Dates_list[2],
        'Race_Num1': p_Race_Numbers_list[0],
        'Race_Num2': p_Race_Numbers_list[1],
        'Race_Num3': p_Race_Numbers_list[2],
        'Horse_Num1': p_Horse_Numbers_list[0],
        'Horse_Num2': p_Horse_Numbers_list[1],
        'Horse_Num3': p_Horse_Numbers_list[2],
        'Rank1': p_Ranks_list[0],
        'Rank2': p_Ranks_list[1],
        'Rank3': p_Ranks_list[2],
        'Course1': p_Courses_list[0],
        'Course2': p_Courses_list[1],
        'Course3': p_Courses_list[2],
        'Distanse1': p_Dists_list[0],
        'Distanse2': p_Dists_list[1],
        'Distanse3': p_Dists_list[2],
        'Condition1': p_Conditions_list[0],
        'Condition2': p_Conditions_list[1],
        'Condition3': p_Conditions_list[2],
        'Last3F1': p_Three_Fs_list[0],
        'Last3F2': p_Three_Fs_list[1],
        'Last3F3': p_Three_Fs_list[2],
        'Prize1': p_Prizes_list[0],
        'Prize2': p_Prizes_list[1],
        'Prize3': p_Prizes_list[2],
        'Condition_Index1': p_Condition_Index_list[0],
        'Condition_Index2': p_Condition_Index_list[1],
        'Condition_Index3': p_Condition_Index_list[2],
        'Time_Index1': p_Time_Index_list[0],
        'Time_Index2': p_Time_Index_list[1],
        'Time_Index3': p_Time_Index_list[2],
        'Father_Time_Index': f_Prize_list,
        'Mother_Time_Index': m_Prize_list,
        'MothersFather_Time_Index': mf_Prize_list,
    })
    result_df = pd.concat([result_df, df], axis=1)

    # 馬数

    # オッズ

    # 人気

    # 天気

@retry
def scraping(Race_ID):
    send_slack_notify("スクレイピング開始")
    logger.info("スクレイピング開始")
    
    year=Race_ID[0:4]
    place=Race_ID[4:6]
    race_count=Race_ID[6:8]
    day=Race_ID[8:10]
    race_num=Race_ID[10:12]

    current_data(year, place, race_count, day, race_num)
    past_data(year, place, race_count, day, race_num)
    result_df.to_csv("file_name.csv", mode='a', index=False, encoding='shift jis', errors='ignore', header=True, line_terminator='\n')
    send_slack_notify("スクレイピング終了")
    logger.info("スクレイピング終了")

    
    if Site_Exists == False:
        return None
    else:
        return result_df
    
if __name__=="__main__":
    result_df=scraping("202506020612")
    print(result_df)


