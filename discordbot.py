import discord
import asyncio
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import time
from discord.ext import tasks
import feedparser
import bme280_custom
from irrpm import IRRP
import TSL2572_custom

TOKEN = 'TOKEN'
channel_id = channel_id
client = discord.Client()
COMMAND_PREFIX = "!"
JST = timezone(timedelta(hours=+9), "JST")

@tasks.loop(seconds=60)
async def loop():
    now_time = datetime.now(JST).strftime("%H:%M")
    if now_time == "07:00":
        channel = client.get_channel(channel_id)
        RSS_URL = 'https://rss-weather.yahoo.co.jp/rss/days/14.xml'
        d = feedparser.parse(RSS_URL)
        for entry in d.entries:
            if  '横浜' in entry.title:
                now = datetime.now(JST)
                descsplit = entry.title, entry.description.split(' ')
                descsplit1 = descsplit[1]
                weather = descsplit1[0]
                temp = descsplit1[2]
                tempsplit = temp.split('/')
                templu = tempsplit[0]
                templd = tempsplit[1]
                msg = "おはようございます。ただいまの時刻は07:00です。本日の横浜の天気は"+ weather +"で、最高気温は" + templu + "、最低気温は" + templd + "です。"
                await channel.send(msg)


#タイマー用の時間変換
def convert_times(time_strings):
    
    result = 0
    for time in time_strings:
        if 'd' in time:
            result += int(time.replace('d','')) * 86400
        elif 'h' in time:
            result += int(time.replace('h','')) * 3600
        elif 'm' in time:
            result += int(time.replace('m','')) * 60
        elif 's' in time:
            result += int(time.replace('s',''))
        else:
            return False
    return result

@client.event
async def on_ready(): 
    print('ログインしました')
    print(client.user.name)
    print(client.user.id)
    print('------')
    channel = client.get_channel(channel_id)
    msg = 'ログインしました'
    await channel.send(msg)

me_id = "冷茶#5982"

@client.event
async def on_message(message):
    if client.user !=message.author: \
    and message.content.startswith(COMMAND_PREFIX):
        if not isinstance(message.channel, discord.TextChannel):
            await message.channel.send('DMでの操作はできません。')#DM操作禁止
        #エアコンスイッチ
        elif 'air_on' in message.content:
            if (str)(message.author) == me_id:
                await message.channel.send('この機能はまだ実装されていません。')
            else:
                await message.channel.send(f'{message.author.mention}その操作は許可されていません。')
        #照明スイッチ
        elif 'light_off' in message.content:
            if (str)(message.author) == me_id:
                    
                ir = IRRP(file="codes", no_confirm=True)
                ir.Playback(GPIO=18, ID="light:off")
                ir.stop()
                time.sleep(2)
                lx = TSL2572_custom.main()
                if lx <= 30:
                    await message.channel.send('消灯しました。')
                elif lx > 30:
                    await message.channel.send('操作に失敗しました。もう一度試してください。')
                else:
                    await message.channel.send(f'{message.author.mention}その操作は許可されていません。')

        elif 'light_on' in message.content:
            if (str)(message.author) == me_id:
                ir = IRRP(file="codes", no_confirm=True)
                ir.Playback(GPIO=18, ID="light:on")
                ir.stop()
                time.sleep(1)
                lx = TSL2572_custom.main()
                if lx >= 50:
                    await message.channel.send('点灯しました。')
                elif lx < 50:
                    await message.channel.send('操作に失敗しました。もう一度試してください。')
            else:
                await message.channel.send(f'{message.author.mention}その操作は許可されていません。')
        #テレビをつける
        elif 'tv_on' in message.content:
            if (str)(message.author) == me_id:
                ir = IRRP(file="codes", no_confirm=True)
                ir.Playback(GPIO=18, ID="tv:on")
                ir.stop()
                await message.channel.send('テレビを付けました。')
            else:
                await message.channel.send(f'{message.author.mention}その操作は許可されていません。')
        #チャンネル変更
        #気温
        elif 'temp' in message.content:
            #env = 0
            env = bme280_custom.readData()
            env_par = env.split(',')
            pres = env_par[0]
            temp = env_par[1]
            hum = env_par[2]
            discon_ind = 0.81*float(temp) + 0.01*float(hum)*(0.99*float(temp)-14.3)+46.3
            if discon_ind < 55:
                dimes = '寒い'
            elif 55 < discon_ind < 60:
                dimes = '肌寒い'
            elif 60 < discon_ind < 65:
                dimes = '過ごしやすい'
            elif 65 < discon_ind < 70:
                dimes = '快適'
            elif 70 < discon_ind < 75:
                dimes = '過ごしやすい'
            elif 75 < discon_ind < 80:
                dimes = 'やや暑い'
            elif 80 < discon_ind:
                dimes = '大変暑い'
            #print (dimes)
            env_mes = "現在の気圧は" + pres + "hPa、気温は" + temp + "℃、湿度は" + hum + "%です。不快指数はおよそ" + str(int(discon_ind)) + "で、現在の室内は" + dimes + "です。"
            channel = client.get_channel(channel_id)
            await channel.send(env_mes)
            
        #照度
        elif 'lx' in message.content:
            lx = TSL2572_custom.main()
            lx_mes = "現在の照度はおよそ"+ str(int(lx)) +"lxです。"
            channel = client.get_channel(channel_id)
            await channel.send(lx_mes)
        #現在時刻（デバッグ機能）
        elif 'nowtime' in message.content:
            time_mes = "現在の時刻は" + datetime.now(JST).strftime(" %H時 %M分 %S秒") + "です。"
            channel = client.get_channel(channel_id)
            await channel.send(time_mes)
        #タイマー
        elif 'timer' in message.content:
            all_time_string = message.content
            time_strings = all_time_string.split(',')
            del time_strings[0]
            print(time_strings)
            result = convert_times(time_strings)
            if not result:
                await message.channel.send("時間指定がうまくされていないか、0分になっています。")
                return
            await message.channel.send('{}後にDMで時間とお知らせします。'.format(all_time_string))
            await asyncio.sleep(result)
            #DM送信
            await message.author.send('時間')
        #リマインド
        elif 'remind' in message.content:
            all_date_string = message.content
            date_strings = all_date_string.split(',')
            del date_strings[0]
            sdate = date_strings[0]
            stime = date_strings[1]
            set_date = sdate.split('/')
            set_time = stime.split(':')
            now = datetime.now(JST)
            now = datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
            comp = datetime(int(set_date[0]), int(set_date[1]), int(set_date[2]), int(set_time[0]), int(set_time[1]), int(set_time[2]))
            diff = comp - now
            if int(diff.days) >= 0:
                await message.channel.send('{}にDMで{}とお知らせします。'.format(all_date_string, content))
            else:
                await message.channel.send("指定された日付が本日よりも前になっています。")
                return
            t_time = diff.days * 86400 + diff.seconds
            print(t_time)
            await asyncio.sleep(t_time)
            #DM送信
            await message.author.send(content)
        
        #アラーム
        elif 'dmalarm' in message.content:
            all_alarm_string = message.content
            alarm_strings = all_alarm_string.split(' ')
            del alarm_strings[0]
            atime = alarm_strings[0]
            target_time = atime.split(':')
            now = datetime.now(JST)
            now = datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
            comp1 = datetime(now.year, now.month, now.day, int(target_time[0]), int(target_time[1]), 0)
            comp2 = comp1 + timedelta(days=1)
            diff1 = comp1 - now
            diff2 = comp2 - now
            if int(diff1.seconds) >= 0:
                await message.channel.send('{}にDMでalarm!とお知らせします。'.format(all_alarm_string))
                a_time = diff1.seconds
                print(a_time)
                print("アラームパターン1が実行されます。")
            elif int(diff1.seconds) < 0:
                await message.channel.send('{}にDMでalarm!とお知らせします。'.format(all_alarm_string))
                a_time = diff2.seconds
                print("アラームパターン2が実行されます。")
            else:
                await message.channel.send("時刻が正しく入力されていません。")
                print("アラームエラー:正しい時刻が入力されませんでした。")
            await asyncio.sleep(a_time)
            #DM送信
            await message.author.send('alarm!')
            print("コマンドalarmが実行されました。")

        #電気アラーム
        elif 'lalarm' in message.content:
            all_alarm_string = message.content
            alarm_strings = all_alarm_string.split(' ')
            del alarm_strings[0]
            atime = alarm_strings[0]
            target_time = atime.split(':')
            now = datetime.now(JST)
            now = datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
            comp1 = datetime(now.year, now.month, now.day, int(target_time[0]), int(target_time[1]), 0)
            comp2 = comp1 + timedelta(days=1)
            diff1 = comp1 - now
            diff2 = comp2 - now
            if (str)(message.author) == me_id:
                if int(diff1.seconds) >= 0:
                    await message.channel.send('{}に照明を点灯します。消灯は「電気けして」と送信してください。'.format(all_alarm_string))
                    a_time = diff1.seconds
                    print(a_time)
                    print("アラームパターン1が実行されます。")
                elif int(diff1.seconds) < 0:
                    await message.channel.send('{}に照明を点灯します。消灯は「電気けして」と送信してください。'.format(all_alarm_string))
                    a_time = diff2.seconds
                    print("アラームパターン2が実行されます。")
                else:
                    await message.channel.send("時刻が正しく入力されていません。")
                    print("アラームエラー:正しい時刻が入力されませんでした。")
                await asyncio.sleep(a_time)
                #電気点灯
                ir = IRRP(file="codes", no_confirm=True)
                ir.Playback(GPIO=18, ID="light:on")
                ir.stop()
                time.sleep(1)
                lx = TSL2572_custom.main()
                if lx >= 50:
                    await message.channel.send('点灯しました。')
                elif lx < 50:
                    await message.channel.send('操作に失敗しました。もう一度試してください。')
                print("コマンドlalarmが実行されました。")
            else:
                await message.channel.send(f'{message.author.mention}その操作は許可されていません。')
            
        #天気予報（デバック機能）
        elif 'weather' in message.content:
            channel = client.get_channel(channel_id)
            RSS_URL = 'https://rss-weather.yahoo.co.jp/rss/days/14.xml'
            d = feedparser.parse(RSS_URL)
            for entry in d.entries:
                if  '横浜' in entry.title:
                    now = datetime.now(JST)
                    descsplit = entry.title, entry.description.split(' ')
                    descsplit1 = descsplit[1]
                    weather = descsplit1[0]
                    temp = descsplit1[2]
                    tempsplit = temp.split('/')
                    templu = tempsplit[0]
                    templd = tempsplit[1]
                    msg = "本日の横浜の天気は" + weather + "で、最高気温は" + templu + "、最低気温は"+ templd +"です。"
                    await channel.send(msg)
                    
        #コマンド以外のワードに対して
        else:
            await message.channel.send("そのようなコマンドは設定されていません")

loop.start()
client.run(TOKEN)
