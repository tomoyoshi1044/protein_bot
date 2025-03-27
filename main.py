import requests
import pandas as pd
import numpy as np
import time
import tweepy
import random
import os

def get_rank():
    REQUEST_URL = "https://app.rakuten.co.jp/services/api/IchibaItem/Ranking/20220601"
    APP_ID = os.getenv("RAKUTEN_APP_ID")
    AFFILIATE_ID = os.getenv("RAKUTEN_AFFILIATE_ID")

    search_params = {
        "format": "json",
        "applicationId": APP_ID,
        "affiliateId": AFFILIATE_ID,
        "genreId": 100938,
        "hits": 30,
        "page": 1,
    }

    item_key = ['itemName', 'itemPrice', 'reviewCount', 'affiliateUrl', 'mediumImageUrls', 'startTime', 'endTime']
    item_list = []

    response = requests.get(REQUEST_URL, params=search_params)
    result = response.json()

    if 'pageCount' in result:
        max_pages = min(result['pageCount'], 30)
    else:
        max_pages = 30

    for page in range(1, max_pages + 1):
        search_params["page"] = page
        response = requests.get(REQUEST_URL, params=search_params)
        result = response.json()

        if 'Items' not in result or len(result['Items']) == 0:
            break

        for item_data in result['Items']:
            item = item_data['Item']
            tmp_item = {key: item[key] for key in item_key if key in item}
            item_list.append(tmp_item)

        time.sleep(1)

    items_df = pd.DataFrame(item_list)
    items_df.columns = ['商品名', '商品価格', 'レビュー数', 'A_URL', 'IMG_URL', 'セール開始時期', 'セール終了時期']
    items_df.index = np.arange(1, len(items_df) + 1)

    items_df["セール終了時期"] = pd.to_datetime(items_df["セール終了時期"], errors="coerce").dt.strftime("%-m月%-d日%H:%M")
    items_df = items_df.dropna(subset=["セール終了時期"])
    items_df = items_df[items_df["商品名"].str.contains("プロテイン", na=False)]
    items_df["商品価格"] = items_df["商品価格"].astype(float).apply(lambda x: f"{x:,.0f}")

    items_df.to_csv("./rakuten_protein_data.csv", index=False)
    print(f"データ取得完了！合計 {len(items_df)} 件の商品を取得しました。")


def post():
    CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
    CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
    ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
    ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

    client = tweepy.Client(
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET
    )

    df = pd.read_csv("rakuten_protein_data.csv")
    if df.empty:
        print("データが見つかりません。ツイートをスキップします。")
        return

    name = df.iloc[0, 0]
    price = df.iloc[0, 1]
    affiliateUrl = df.iloc[0, 3]
    sale_end = df.iloc[0, 6]

    tweet_templates = [
        f"🔥セール速報🔥\n あの人気プロテインが今だけ【{price}円】💰\n セール終了: {sale_end} \n詳しくはこちら {affiliateUrl} #PR",
        f"💪 プロテインセール情報 💪\n 今がチャンス！【{price}円】で買えるのは {sale_end} まで⏳\n 詳しくはこちら {affiliateUrl} #PR",
        f"【お得情報】\n 今だけ特別価格【{price}円】！\n あの話題のプロテインがセール中🔥\n セール終了: {sale_end} まで\n詳しくはこちら {affiliateUrl} #PR",
        f"⚠️期間限定⚠️\n この価格【{price}円】は {sale_end} まで！\n 今が買い時💥 詳しくはこちら {affiliateUrl} #PR",
        f"💥セール開催中💥\n 話題のプロテインが【{price}円】で買える！\n セール終了: {sale_end} まで⏳\n お見逃しなく！{affiliateUrl} #PR",
        f"🏋️‍♂️ 期間限定セール 🏋️‍♀️\n 今なら【{price}円】でGET！\n セールは {sale_end} まで⏳\n 詳しくはこちら {affiliateUrl} #PR",
        f"🔥数量限定🔥\n 特価！【{price}円】のチャンス！\n {sale_end} までの限定セール💨\n すぐチェック👉 {affiliateUrl} #PR",
        f"💰プロテインセール💰\n【{price}円】の特別セール中！\n 終了は {sale_end}まで ⏳ お早めに！\n 詳細: {affiliateUrl} #PR",
        f"💪筋トレ応援💪\n お得なプロテインが【{price}円】で買える！\n {sale_end} までの限定価格🏃‍♂️💨\n 詳細: {affiliateUrl} #PR",
        f"⏳ラストチャンス⏳\n {sale_end} までこの価格【{price}❗】\n お得なプロテインを見逃すな👀\n 詳細: {affiliateUrl} #PR"
    ]

    message = random.choice(tweet_templates)

    try:
        client.create_tweet(text=message)
        print("ツイート投稿成功！")
    except Exception as e:
        print(f"ツイート投稿に失敗: {e}")

if __name__ == "__main__":
    get_rank()
    post()
