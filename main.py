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
        "genreId": 563727,
        "page": 1,
    }

    item_key = ['rank','itemName', 'itemPrice','reviewCount','affiliateUrl','mediumImageUrls','startTime','endTime']
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
    items_df.columns = ['順位','商品名', '商品価格', 'レビュー数','A_URL','IMG_URL','セール開始時期','セール終了時期']
    items_df.index = np.arange(1, len(items_df) + 1)

    items_df["セール終了時期"] = pd.to_datetime(items_df["セール終了時期"], errors="coerce").dt.strftime("%-m月%-d日%H:%M")
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
    
    def extract_product_name(full_name):
        """商品名の冒頭60文字＋次のスペースまでを取得"""
        truncated = full_name[:60]  # 最初の30文字を取得
        if " " in full_name[60:]:  # 30文字目以降にスペースがあるか確認
            truncated += full_name[60:].split(" ")[0]  # 次のスペースまで追加
        return truncated
    
    df = pd.read_csv("rakuten_protein_data.csv")
    if df.empty:
        print("データが見つかりません。ツイートをスキップします。")
        return

    random_index = random.randint(0, min(19, len(df) - 1))
    name = extract_product_name(df.iloc[random_index, 1])
    price = df.iloc[random_index, 2]
    affiliateUrl = df.iloc[random_index, 4]
    sale_end = df.iloc[random_index, 7]


    tweet_templates = [
        f"💪【{name}】が登場！\n 今なら【{price}円】で購入可能💰\n#楽天\n#プロテイン\n#ad\n{affiliateUrl}",
        f"🏋️‍♂️ 話題の【{name}】で栄養補給🏋️‍♀️\n トレーニングのお供に！【{price}円】とお買い得💰\n#楽天\n#プロテイン\n#ad\n{affiliateUrl}",
        f"💰【{name}】が大好評💰\n お得な【{price}円】でゲットしよう！\n#楽天\n#プロテイン\n#ad\n{affiliateUrl}",
        f"✨人気の【{name}】がお買い得✨\n たんぱく質補給に最適！【{price}円】で爆売れ中⭐️\n#楽天\n#プロテイン\n#ad\n{affiliateUrl}",
        f"🔥【{name}】が話題沸騰🔥\n【{price}円】で好評販売中\n#楽天\n#プロテイン\n#ad\n{affiliateUrl}",
        f"🍀 健康サポートに【{name}】がオススメ🍀\n 価格は【{price}円】とお買い得！\n#楽天\n#プロテイン\n#ad\n{affiliateUrl}",
        f"💥筋トレ・ダイエットのお供に【{name}】💥\n 今なら【{price}円】とお買い得！\n#楽天\n#プロテイン\n#ad\n{affiliateUrl}",
        f"💪 筋トレにおすすめ【{name}】💪\n【{price}円】からお得に買える💰\n#楽天\n#プロテイン\n#ad\n{affiliateUrl}",
        f"🏋️‍♀️【{name}】が大人気🏋️‍♂️\n 嬉しい価格【{price}円】で販売中！\n#楽天\n#プロテイン\n#ad\n{affiliateUrl}",
        f"🔍話題の【{name}】をチェック🔍\n 人気のプロテインが【{price}円】で手に入れるチャンス！\n#楽天\n#プロテイン\n#ad\n{affiliateUrl}"
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
