import requests
import json
import pymysql
import datetime
import time

# 최신 패치 버젼 가져오기
patch_version_url = 'https://ddragon.leagueoflegends.com/api/versions.json'
r = requests.get(patch_version_url)
patch_version = r.json()[0]

# API 키(앞 2개 소환사 정보 수집 전용)
api_keys = ['RGAPI-de6db5ca-44d5-4dc8-be3d-34a617348e67','RGAPI-4e30da8a-7441-4381-b779-df28834df824' \
           'RGAPI-3eb981c2-1f8a-41fc-93f9-a51f6999fee1', 'RGAPI-856ad351-d275-43e1-ad28-06e4a40e9b43', 'RGAPI-f4956437-ee69-4d26-a270-5f841f4be283']

# matchlist 저장 공간
matchidlist = list()
# 한 경기당 10명의 소환사 이름 저장 공간
summonerslist = list()
# 이긴 팀 챔피언 번호 저장 공간
winchampionlist = [0, 0, 0, 0, 0]
# 진 팀 챔피언 번호 저장 공간
losechampionlist = [0, 0, 0, 0, 0]
# 이긴 팀 챔피언 라인 저장 공간
winrolelist = [0, 0, 0, 0, 0]
# 진 팀 챔피언 라인 저장 공간
loserolelist = [0, 0, 0, 0, 0]
# 이긴 팀 챔피언 라인 저장 공간
winlanelist = [0, 0, 0, 0, 0]
# 진 팀 챔피언 라인 저장 공간
loselanelist = [0, 0, 0, 0, 0]

# DB 연결
print("DATABASE 연결 중")
con = pymysql.connect(host='tae2089.synology.me',
                      port=51420,
                      user='test',
                      password='test',
                      db='test')
print("DATABASE 연결 완료")

# 디폴트 커서 생성
cur = con.cursor()

# 솔로 랭크
queue = 'RANKED_SOLO_5x5'

def limit(r, api):
    print("속도 제한이 걸려 sleep 상태로 변경됩니다.")

    while r.status_code == 429:
        print("10초만 기다려 주세요.")
        time.sleep(10)
        r = requests.get(api)
        
    print("속도 제한이 풀려 sleep 상태를 해제합니다.")

    return r

def list_index_remove(bufferlist):
    templist = list()
    templist_2 = list()
    
    for i in range(len(bufferlist)):
        if bufferlist[i][0] not in templist:
           templist.append(bufferlist[i][0])
        else:
           templist_2.append(i)
           
    templist_2.reverse()

    for i in templist_2:
        del bufferlist[i]

    return bufferlist

def get_high_sumonerid(tier, api_key):
    # 데이터 저장 전, 저장되어 있던 데이터 삭제 O
    # 데이터를 수집할 소환사의 summonerId와 nickname 수집

    print("소환사의 기본 정보 수집을 시작합니다.")
    leagues_api = 'https://kr.api.riotgames.com/lol/league/v4/' + tier + '/by-queue/' + queue + '?api_key=' + api_key
    r = requests.get(leagues_api)
    if r.status_code == 429:
        r = limit(r, leagues_api)

    INSERT_tier = str()
    bufferlist = list()
    bufferlist_2 = list()
    bufferlist_3 = list()
    
    if tier == 'challengerleagues':
        INSERT_tier = 'CHALLENGER'
    elif tier == 'grandmasterleagues':
        INSERT_tier = 'GRANDMASTER'
    elif tier =='masterleagues':
        INSERT_tier = 'MASTER'

    # 실행 날짜 기준으로 해당 티어가 아닌 유저가 존재할 수 있으므로 DELETE 실행
    sql = 'DELETE FROM summoners_tier WHERE patch_version = (%s) and tier in (%s)'
    cur.execute(sql, (patch_version, INSERT_tier))
    con.commit()

    # 해당 티어의 소환사 수 만큼 탐색
    for i in range(len(r.json()['entries'])):
        bufferlist.append([r.json()['entries'][i]['summonerId'], r.json()['entries'][i]['summonerName'], api_key])
        bufferlist_2.append([r.json()['entries'][i]['summonerName'], INSERT_tier, patch_version])
        bufferlist_3.append(r.json()['entries'][i]['summonerName'])

        print(i+1, "번째 소한사: summoners_tier table에 존재하지 않은 소환사를 찾았습니다.")

    # 중복 제거
    bufferlist = list_index_remove(bufferlist)
    bufferlist_2 = list_index_remove(bufferlist_2)

    # summoners_tier table의 중복을 확인한 것이므로 summoners table에 등록 하기 전에 제거를 해줘야 pymysql.err.IntegrityError가 발생하지 않는다.
    sql = 'DELETE FROM summoners WHERE nickname = (%s)'
    cur.executemany(sql, bufferlist_3)
    con.commit()
    bufferlist_3.clear()

    sql = 'INSERT INTO summoners(encrypt_summoner_id, nickname, api_number) values(%s, %s, %s)'
    cur.executemany(sql, bufferlist)
    con.commit()
    bufferlist.clear()
            
    sql = 'INSERT INTO summoners_tier(nickname, tier, patch_version) values(%s, %s, %s)'
    cur.executemany(sql, bufferlist_2)
    con.commit()
    bufferlist_2.clear()

    print(len(r.json()['entries']), "개의 소환사 정보를 DB에 등록하였습니다.")

def get_high_sumonerid_2(tier, api_key):
    # 데이터 저장 전, 저장되어 있던 데이터 삭제 X
    # 데이터를 수집할 소환사의 summonerId와 nickname 수집

    print("소환사의 기본 정보 수집을 시작합니다.")
    leagues_api = 'https://kr.api.riotgames.com/lol/league/v4/' + tier + '/by-queue/' + queue + '?api_key=' + api_key
    r = requests.get(leagues_api)
    if r.status_code == 429:
        r = limit(r, leagues_api)

    INSERT_tier = str()
    bufferlist = list()
    bufferlist_2 = list()
    bufferlist_3 = list()
    
    if tier == 'challengerleagues':
        INSERT_tier = 'CHALLENGER'
    elif tier == 'grandmasterleagues':
        INSERT_tier = 'GRANDMASTER'
    elif tier =='masterleagues':
        INSERT_tier = 'MASTER'


    # 해당 티어의 소환사 수 만큼 탐색
    for i in range(len(r.json()['entries'])):

        # DB에 이미 등록된 소환사 이름이 있는지 필터링
        sql = 'SELECT nickname FROM summoners_tier WHERE nickname in (%s) and patch_version in (%s)'
        cur.execute(sql, (r.json()['entries'][i]['summonerName'], patch_version))
        result = cur.fetchall()   
        
        bufferlist.append([r.json()['entries'][i]['summonerId'], r.json()['entries'][i]['summonerName'], api_key])
        bufferlist_3.append(r.json()['entries'][i]['summonerName'])

        # 이미 등록된 소환사 이름이 있는 경우
        try:
            if result[0][0] == r.json()['entries'][i]['summonerName']:
                print(i+1, "번째 소환사: summoners_tier table에 이미 등록되어 있습니다.")
                continue

        # 이미 등록된 소환사 이름이 없는 경우
        except IndexError:
            print(i+1, "번째 소한사: summoners_tier table에 존재하지 않은 소환사를 찾았습니다.")
            bufferlist_2.append([r.json()['entries'][i]['summonerName'], INSERT_tier, patch_version])

    bufferlist = list_index_remove(bufferlist)
    bufferlist_2 = list_index_remove(bufferlist_2)

    # summoners_tier table의 중복을 확인한 것이므로 summoners table에 등록 전 제거를 해줘야 pymysql.err.IntegrityError가 발생하지 않는다.
    sql = 'DELETE FROM summoners WHERE nickname = (%s)'
    cur.executemany(sql, bufferlist_3)
    con.commit()
    bufferlist_3.clear()

    # 입력받은 상위티어의 소환사를 모두 가져온 경우
    sql = 'INSERT INTO summoners(encrypt_summoner_id, nickname, api_number) values(%s, %s, %s)'
    cur.executemany(sql, bufferlist)
    con.commit()
    bufferlist.clear()
            
    sql = 'INSERT INTO summoners_tier(nickname, tier, patch_version) values(%s, %s, %s)'
    cur.executemany(sql, bufferlist_2)
    con.commit()
    bufferlist_2.clear()
    print(len(r.json()['entries']), "개의 소환사 정보를 DB에 등록하였습니다.")

def get_low_sumonerid(tier, api_key):
    # 데이터 저장 전, 저장되어 있던 데이터 삭제 O
    # 데이터를 수집할 소환사의 summonerId와 nickname 수집
    # divisionlist = ['I', 'II', 'III', 'IV']
    divisionlist = ['I']
    bufferlist = list()
    bufferlist_2 = list()
    bufferlist_3 = list()
    # bufferlist_4 = list()

    # 실행 날짜 기준으로 해당 티어가 아닌 유저가 존재할 수 있으므로 DELETE 실행
    sql = 'DELETE FROM summoners_tier WHERE patch_version = (%s) and tier LIKE (%s)'
    cur.execute(sql, (patch_version, str('%' + tier + '%')))
    con.commit()
    
    for i in range(len(divisionlist)):
        print(tier, str(divisionlist[i]), "티어의 소환사를 검색합니다.")
        page = 1
        
        while(True):
            leagues_api = 'https://kr.api.riotgames.com/lol/league/v4/entries/' + queue + '/' + tier + '/' + str(divisionlist[i]) + '?page=' + str(page) + '&api_key=' + api_key
            r = requests.get(leagues_api)
            if r.status_code == 429:
                r = limit(r, leagues_api)
            
            # 페이지의 데이터 수가 0이면 while문을 탈출한다.
            if len(r.json()) == 0:
                break

            # r.json의 크기만큼 소환사 추가
            for user_number in range(len(r.json())):
    
                print(tier, str(divisionlist[i]), page, user_number+1, "의 소환사를 검색했습니다.")

                bufferlist.append([r.json()[user_number]['summonerId'], r.json()[user_number]['summonerName'], api_key])
                bufferlist_2.append([r.json()[user_number]['summonerName'], tier + ' ' + str(divisionlist[i]), patch_version])
                bufferlist_3.append(r.json()[user_number]['summonerName'])
                # bufferlist_4.append([r.json()[user_number]['summonerName'], patch_version])
                  
            print(tier, str(divisionlist[i]), page, "페이지의 모든 소환사를 검색했습니다.")
            page += 1

    bufferlist = list_index_remove(bufferlist)
    bufferlist_2 = list_index_remove(bufferlist_2)
    
    print("DB 데이터를 정리합니다.")
    # 다른 패치 버젼에서 INSERT FROM summoner을 통해 이미 등록되어 있을 수 있으므로 DELETE 실행
    sql = 'DELETE FROM summoners WHERE nickname in (%s)'
    cur.executemany(sql, bufferlist_3)
    con.commit()
    print("summoners table에 중복된 유저 데이터를 지웠습니다.")
    bufferlist_3.clear()

    # 전 page에서 등록된 경우 혹은 대소문자가 다른 경우, 데이터를 삭제한다.        
    # sql = 'DELETE FROM summoners_tier WHERE nickname in (%s) and patch_version = (%s)'
    # cur.executemany(sql, bufferlist_4)
    # con.commit()
    # print("summoners_tier table에 중복된 유저 데이터를 지웠습니다.")
    # bufferlist_4.clear()
                    
    sql = 'INSERT INTO summoners(encrypt_summoner_id, nickname, api_number) values(%s, %s, %s)'
    cur.executemany(sql, bufferlist)
    con.commit()
    print("summoners table에 저장하였습니다.")
    bufferlist.clear()
                
    sql = 'INSERT INTO summoners_tier(nickname, tier, patch_version) values(%s, %s, %s)'
    cur.executemany(sql, bufferlist_2)
    con.commit()
    print("summoners_tier table에 저장하였습니다.")
    bufferlist_2.clear()

def get_low_sumonerid_2(tier, api_key):
    # 데이터 저장 전, 저장되어 있던 데이터 삭제 X
    # 데이터를 수집할 소환사의 summonerId와 nickname 수집
    divisionlist = ['I', 'II', 'III', 'IV']
    division_number = 0
    page = 1
    bufferlist = list()
    bufferlist_2 = list()
    bufferlist_3 = list()
    bufferlist_4 = list()

    # 실행 날짜 기준으로 해당 티어가 아닌 유저가 존재할 수 있으므로 DELETE 실행
    sql = 'DELETE FROM summoners_tier WHERE patch_version = (%s) and tier LIKE (%s)'
    cur.execute(sql, (patch_version, str('%' + tier + '%')))
    con.commit()
    
    while(True):
        leagues_api = 'https://kr.api.riotgames.com/lol/league/v4/entries/' + queue + '/' + tier + '/' + str(divisionlist[division_number]) + '?page=' + str(page) + '&api_key=' + api_key
        r = requests.get(leagues_api)
        if r.status_code == 429:
            r = limit(r, leagues_api)
    
        # 해당 티어 division의 페이지에 값이 있는지 확인
        try:
            r.json()[0]
            print(tier, str(divisionlist[division_number]), "page", page ,"값이 존재합니다.")
        
        # 없으면 해당 티어 divsion이 끝난 것이므로 다음 division으로 변경 
        except IndexError:
            division_number += 1
            page = 1
            
            # division_number 가 4가 되면 while문 탈출
            if division_number == 4:
                break
            leagues_api = 'https://kr.api.riotgames.com/lol/league/v4/entries/' + queue + '/' + tier + '/' + str(divisionlist[division_number]) + '?page=' + str(page) + '&api_key=' + api_key
            r = requests.get(leagues_api)
            if r.status_code == 429:
                r = limit(r, leagues_api)

            print(tier, str(divisionlist[division_number]), "으로 변경 됐습니다.")

        # r.json의 크기만큼 소환사 추가
        for user_number in len(r.json()):

            # 이미 등록된 소환사 이름이 있는지 필터링
            sql = 'SELECT nickname FROM summoners_tier WHERE nickname in (%s) and patch_version in (%s) and tier LIKE (%s)'
            cur.execute(sql, (r.json()[user_number]['summonerName'], patch_version, str('%' + tier + '%')))            
            result = cur.fetchall()
            
            #이미 등록된 소환사가 있는 경우
            try:    
                if result[0][0] == r.json()[user_number]['summonerName']:
                    print("summoners_tier table에 이미 등록되어 있습니다.")
                    continue

            # 이미 등록된 소환사 이름이 없는 경우
            except IndexError:
                print("summoners_tier table에 존재하지 않은 소환사를 찾았습니다.")

            bufferlist.append([r.json()[user_number]['summonerId'], r.json()[user_number]['summonerName'], api_key])
            bufferlist_2.append([r.json()[user_number]['summonerName'], tier + ' ' + str(divisionlist[division_number]), patch_version])
            bufferlist_3.append(r.json()[user_number]['summonerName'])
            bufferlist_4.append([r.json()[user_number]['summonerName'], patch_version])

        bufferlist = list_index_remove(bufferlist)
        bufferlist_2 = list_index_remove(bufferlist_2)
      
        
        # 다른 패치 버젼에서 INSERT FROM summoner을 통해 이미 등록되어 있을 수 있으므로 DELETE 실행
        sql = 'DELETE FROM summoners WHERE nickname in (%s)'
        cur.executemany(sql, bufferlist_3)
        con.commit()
        print("summoners table에 중복된 유저 데이터를 지웠습니다.")
        bufferlist_3.clear()
                   
        sql = 'DELETE FROM summoners_tier WHERE nickname in (%s) and pacth_version = (%s)'
        cur.executemany(sql, bufferlist_4)
        con.commit()
        print("summoners_tier table에 중복된 유저 데이터를 지웠습니다.")
        bufferlist_4.clear()
                        
        sql = 'INSERT INTO summoners(encrypt_summoner_id, nickname, api_number) values(%s, %s, %s)'
        cur.executemany(sql, bufferlist)
        con.commit()
        print("summoners table에 저장하였습니다.")
        bufferlist.clear()
                    
        sql = 'INSERT INTO summoners_tier(nickname, tier, patch_version) values(%s, %s, %s)'
        cur.executemany(sql, bufferlist_2)
        con.commit()
        print("summoners_tier table에 저장하였습니다.")
        bufferlist_2.clear()
                    
        print(tier, str(divisionlist[division_number]), page, "페이지의 모든 소환사를 검색했습니다.")
        page += 1
           
def get_accountid(num, api_key):
    sql = 'SELECT * FROM summoners WHERE api_number in (%s) and account_id is NULL'
    cur.execute(sql, api_key)
    result = cur.fetchall()
    
    bufferlist = list()

    if num > len(result):
        num = len(result)

    for i in range(num):
        accountid_api = 'https://kr.api.riotgames.com/lol/summoner/v4/summoners/' + result[i][0] + '?api_key=' + api_key
        r = requests.get(accountid_api)
        if r.status_code == 429:
            r = limit(r, accountid_api)

        #accountid 저장
        bufferlist.append((r.json()['accountId'], r.json()['id']))
        
      
        
    sql = 'UPDATE summoners SET account_id = (%s) WHERE encrypt_summoner_id in (%s)'
    cur.executemany(sql, bufferlist)
    con.commit()
    bufferlist.clear()
    print("get_accountid complete")

def get_accountid_2(api_key):
    # production키 발급 받으면 사용
    sql = 'SELECT * FROM summoners WHERE api_number in (%s) and account_id is NULL'
    cur.execute(sql, api_key)
    result = cur.fetchall()
    bufferlist = list()
    i = 0

    while(True):
        print(i + 1, '번째 요청 중')

        try:
            print('summonerid: ' + result[i][0] + '에 대한 API 수집 중')

        except IndexError:
            print("summoners table에 존재하는 모든 소환사의 API를 요청했습니다")
            sql = 'UPDATE summoners SET account_id in (%s) WHERE encrypt_summoner_id in (%s)'
            cur.executemany(sql, bufferlist)
            con.commit()
            bufferlist.clear()
            break

        accountid_api = 'https://kr.api.riotgames.com/lol/summoner/v4/summoners/' + result[i][0] + '?api_key=' + api_key
        r = requests.get(accountid_api)
        if r.status_code == 429:
            r = limit(r, accountid_api)

        #accountid 저장
        bufferlist.append((r.json()['accountId'], r.json()['id']))
      
        if (i+1) % 100 == 0:
            sql = 'UPDATE summoners SET account_id in (%s) WHERE encrypt_summoner_id in (%s)'
            cur.executemany(sql, bufferlist)
            con.commit()
            bufferlist.clear()
        
        i += 1

def get_matchid(person_num, game_num, game_date):
    bufferlist = list()
    temp_matchidlist = list()
    new_matchidlist = list()

    sql = 'SELECT account_id, api_number FROM summoners WHERE getmatchid_use is NULL and account_id is NOT NULL'
    cur.execute(sql)
    result = cur.fetchall()
    
    if person_num > len(result):
        person_num = len(result)

    # N명의 소환사 검색
    for i in range(person_num):
        #소환사 선택
        matchid_api = 'https://kr.api.riotgames.com/lol/match/v4/matchlists/by-account/' + result[i][0] + '?api_key=' + result[i][1]
        r = requests.get(matchid_api)
        if r.status_code == 429:
            r = limit(r, matchid_api)
             
        # 한 소환사당 game_num개의 matchidlist 저장 방법 구현
        for j in range(game_num):

            # 특정 시간 이후
            try:
                if r.json()['matches'][j]['timestamp'] >= game_date and r.json()['matches'][j]['queue'] == 420 :
                    matchidlist.append(r.json()['matches'][j]['gameId'])
                elif r.json()['matches'][j]['timestamp'] < game_date:
                    print(datetime.datetime.fromtimestamp(game_date/1000), "ㅇㅣㅎㅜㅇㅡㅣ ㄱㅔㅇㅣㅁㅇㅣ ㅇㅓㅂㅅㅅㅡㅂㄴㅣㄷㅏ.")
                elif r.json()['matches'][j]['queue'] != 420:
                      print('솔로 랭크가 아닙니다.')
                    
            except IndexError:
                print('해당 유저의 게임 경기 수가 충분하지 않습니다.')
                break
        # gamematchid_use ㄷㅡㅇㄹㅗㄱ
        bufferlist.append([1, result[i][0]])

    # matchidlist의 중복 요소 제거 
    for temp in matchidlist:
        if temp not in temp_matchidlist:
            temp_matchidlist.append(temp)
            new_matchidlist.append([temp, patch_version])

    # 이미 등록된 matchid 인지 확인
    for i in range(len(new_matchidlist)):
        sql = 'SELECT match_id FROM matches WHERE match_id in (%s)'
        try:
            cur.execute(sql, new_matchidlist[i][0])

        except IndexError:
            print("dbㅇㅔ ㄷㅡㅇㄹㅗㄱㄷㅗㅣㄴ matchid를 중복 제거하였습니다.")    
            break

        result = cur.fetchall()
        
        while(True):
            try:
                result[0][0]
                del new_matchidlist[i]
                print('중복된 matchid가 있어 제거하였습니다.')
                sql = 'SELECT match_id FROM matches WHERE match_id in (%s)'
                cur.execute(sql, new_matchidlist[i][0])
                result = cur.fetchall()
                break;
            except IndexError:
                print('matches에 해당 matchid가 없습니다.')
                


    sql = 'INSERT INTO matches(match_id, patch_version) values (%s, %s)'
    cur.executemany(sql, new_matchidlist)
    con.commit()
    new_matchidlist.clear()

    sql = 'UPDATE summoners SET getmatchid_use = (%s) WHERE account_id in (%s)'
    cur.executemany(sql, bufferlist)
    con.commit()
    bufferlist.clear()
    print("get_matchid complete")

def get_10_summoners(num, api_key):
    sql = 'SELECT match_id FROM matches WHERE get10summoners_use is NULL'
    cur.execute(sql)
    result = cur.fetchall()
    bufferlist = list()

    if num > len(result):
        num = len(result)

        

    for i in range(num):
        try:
            summonername_api = 'https://kr.api.riotgames.com/lol/match/v4/matches/' + result[i][0] + '?api_key=' + api_key
        except IndexError:
            print(num, "개의 matchid의 소환사 이름을 모두 입력했습니다.")
            break
          
        r = requests.get(summonername_api)
        if r.status_code == 429:
            r = limit(r, summonername_api)

        for temp in range(10):
            summonerslist.append([result[i][0], r.json()['participantIdentities'][temp]['player']['summonerName']])
        
        bufferlist.append([1, result[i][0]])
        
    sql = 'INSERT match_summoners SET match_id = (%s), nickname = (%s)'
    cur.executemany(sql, summonerslist)
    con.commit()
    summonerslist.clear()

    sql =  'UPDATE matches SET get10summoners_use = (%s) WHERE match_id in (%s)'
    cur.executemany(sql, bufferlist)
    con.commit()
    bufferlist.clear()
    print("get_10_summoners complete")
            
def get_item(num, api_key):
    sql = 'SELECT match_id FROM matches WHERE getitem_use is NULL'
    cur.execute(sql)
    result = cur.fetchall() 
    bufferlist = list()
    bufferlist_2 = list()
    num_2 = int()

    if num < len(result):
        num_2 = num
    else:
        num_2 = len(result)

    for k in range(num_2):
        try:
            item_api = 'https://kr.api.riotgames.com/lol/match/v4/timelines/by-match/' + result[k][0] + '?api_key=' +  api_key
            r = requests.get(item_api)
            if r.status_code == 429:
                r = limit(r, item_api)

        except IndexError:
            print(num, "개의 matchid를 모두 검색하였습니다.")
            break

        #생기는 아이템 + 소모 아이템
        buyitems = [1035, 1039, 2003, 2031, 2033, 2055, 3340, 3363, 3364, 3513]

        #사라지는 아이템 + 소모 아이템 + 오른 업글 가능 아이템
        sellitems = [1035, 1039, 2003, 2010, 2031, 2033, 2052, 2055, 2065, 2422, 3004, 3068,
                    3078, 3152, 3190, 3340, 3363, 3364, 3400, 3513, 3599, 3600, 4005, 4633,
                    4636, 4643, 6617, 6630, 6631, 6632, 6653, 6655, 6656, 6662, 6664, 6671,
                    6672, 6673, 6691, 6692, 6693]

        #사라지면서 바뀌는 아이템들
        nexttiems = [2420, 3850, 3851, 3854, 3855, 3858, 3859]

        #코어 아이템(신발, 전설, 신화)
        coreItems = [2065, 3001, 3003, 3004, 3006, 3009, 3011, 3020, 3026, 3031, 3033, 3036,
                    3041, 3042, 3043, 3046, 3047, 3050, 3053, 3065, 3068, 3071, 3072, 3074,
                    3075, 3078, 3083, 3085, 3089, 3091, 3094, 3095, 3100, 3102, 3107, 3109,
                    3110, 3111, 3115, 3116, 3117, 3124, 3135, 3139, 3142, 3143, 3152, 3153,
                    3156, 3157, 3158, 3165, 3179, 3181, 3190, 3193, 3222, 3504, 3508, 3742,
                    3748, 3814, 4005, 4401, 4628, 4629, 4633, 4636, 4637, 4643, 6035, 6333,
                    6609, 6616, 6617, 6630, 6631, 6632, 6653, 6655, 6656, 6662, 6664, 6671,
                   6672, 6673, 6675, 6676, 6691, 6692, 6693, 6694, 6695]

        dict = {1:[], 2:[], 3:[], 4:[], 5:[], 6:[], 7:[], 8:[], 9:[], 10:[]}
        i = 0

        while (True):
            j = 0
            try:
                r.json()['frames'][i]

            except IndexError:
                print('matchid ' + result[k][0] + '의 아이템 목록을 정리했습니다.')
                break

            while (True):
                try:
                    # print('timestamp:', r.json()['frames'][i]['events'][j]['timestamp'])
                    if (r.json()['frames'][i]['events'][j]['type'] == 'ITEM_PURCHASED'):
                        if r.json()['frames'][i]['events'][j]['itemId'] in buyitems:
                            j += 1
                            continue
                        number = r.json()['frames'][i]['events'][j]['participantId']
                        dict[number].append(r.json()['frames'][i]['events'][j]['itemId'])

                    elif (r.json()['frames'][i]['events'][j]['type'] == 'ITEM_UNDO'):
                        if r.json()['frames'][i]['events'][j]['beforeId'] in sellitems:
                            j += 1
                            continue
                          
                        number = r.json()['frames'][i]['events'][j]['participantId']
                        
                        if r.json()['frames'][i]['events'][j]['beforeId'] in dict[number]:
                            dict[number].remove( r.json()['frames'][i]['events'][j]['beforeId'])
                            
                        elif r.json()['frames'][i]['events'][j]['afterId'] in dict[number]:
                            dict[number].append( r.json()['frames'][i]['events'][j]['afterId'])

                    elif (r.json()['frames'][i]['events'][j]['type'] == 'ITEM_SOLD'):
                        if r.json()['frames'][i]['events'][j]['itemId'] in sellitems:
                            j += 1
                            continue
                          
                        number = r.json()['frames'][i]['events'][j]['participantId']
                        try:
                            dict[number].remove(r.json()['frames'][i]['events'][j]['itemId'])
                            
                        except ValueError:
                            j += 1
                            continue

                    elif (r.json()['frames'][i]['events'][j]['type'] == 'ITEM_DESTROYED'):
                        number = r.json()['frames'][i]['events'][j]['participantId']
                        if r.json()['frames'][i]['events'][j]['itemId'] in sellitems:
                            j += 1
                            continue

                        elif r.json()['frames'][i]['events'][j]['itemId'] in nexttiems:
                            try:
                                dict[number].remove(r.json()['frames'][i]['events'][j]['itemId'])
                                dict[number].append(r.json()['frames'][i]['events'][j]['itemId'] + 1)
                            
                            except ValueError:
                                j += 1
                                continue

                        else:
                            try:
                                dict[number].remove(r.json()['frames'][i]['events'][j]['itemId'])

                            except ValueError:
                                j += 1
                                continue

                except IndexError:
                    print(i+1, '번째의 frame 이벤트를 모두 검색하였습니다.')
                    break
                j += 1
            i += 1

        # 코어템 저장 및 중복 제거
        new_coreitems = {1:[0,0,0,0,0,0], 2:[0,0,0,0,0,0], 3:[0,0,0,0,0,0], 4:[0,0,0,0,0,0], 5:[0,0,0,0,0,0], \
                        6:[0,0,0,0,0,0], 7 :[0,0,0,0,0,0], 8:[0,0,0,0,0,0], 9:[0,0,0,0,0,0], 10:[0,0,0,0,0,0]}
        for participant_id in range(1, 11):
            spot = 0
            for item_number in dict[participant_id]:
                if item_number in coreItems:
                    if item_number not in new_coreitems[participant_id]:
                        new_coreitems[participant_id][spot] = item_number
                        spot += 1
                        if spot == 6:
                            break

        api = 'https://kr.api.riotgames.com/lol/match/v4/matches/' + result[k][0] + '?api_key=' + api_key
        r = requests.get(api)
        if r.status_code == 429:
            r = limit(r, item_api)

        team100_WL = 'temp'
        
        if r.json()['teams'][0]['win'] == 'Win':
            team100_WL = 'win'
        else:
            team100_WL = 'lose'
        WL = team100_WL

        for q in range(10):      
            if team100_WL == 'win':
                if q>4:
                    WL = 'lose' 

                bufferlist.append((result[k][0], r.json()['participants'][q]['championId'], WL, new_coreitems[q+1][0], new_coreitems[q+1][1], new_coreitems[q+1][2], \
                                    new_coreitems[q+1][3], new_coreitems[q+1][4], new_coreitems[q+1][5]))

            else:
                if q>4:
                    WL = 'win'

                bufferlist.append((result[k][0], r.json()['participants'][q]['championId'], WL, new_coreitems[q+1][0], new_coreitems[q+1][1], new_coreitems[q+1][2], \
                                    new_coreitems[q+1][3], new_coreitems[q+1][4], new_coreitems[q+1][5]))

        bufferlist_2.append((1, result[k][0]))

        if (k+1) % 5 == 0 or (k+1) == num:
            sql = 'INSERT INTO coreitems(match_id, champion_id, win, item_1, item_2, item_3, item_4, item_5, item_6) values(%s, %s, %s, %s, %s, %s, %s, %s, %s)'
            cur.executemany(sql, bufferlist)
            con.commit()

            sql = 'UPDATE matches SET getitem_use = (%s) WHERE match_id in (%s)'
            cur.executemany(sql, bufferlist_2)
            con.commit()

            bufferlist.clear()
            bufferlist_2.clear()
            print("코어 아이템 테이블에 데이터를 넣었습니다.")

def get_overall(num, api_key):
    #매치 테이블에서 매치아이디 가져오기
    sql = 'SELECT match_id FROM matches WHERE overall_use is NULL'
    cur.execute(sql)
    result = cur.fetchall()
    overalllist = list()
    bufferlist = list()
    num_2 = int()

    if num < len(result):
        num_2 = num
    else:
        num_2 = len(result)

    for q in range(num_2):
        #매치정보 가져오기
        try:
            api = 'https://kr.api.riotgames.com/lol/match/v4/matches/' + str(result[q][0]) + '?api_key=' + api_key
        
        except ValueError:
            print("모든 match_id의 overall을 수집했습니다.")
            break
        r = requests.get(api)
        if r.status_code == 429:
            r = limit(r, api)

        print(result[q][0])
        for t in range(10): #플레이어들의 전적 가져오기
            pnum = r.json()['participantIdentities'][t]['participantId']
                
            # 이름 구하기
            name = r.json()['participantIdentities'][pnum - 1]['player']['summonerName']
        
            # 게임이 만들어진 시간, 플레이한 시간
            gameCreation = r.json()['gameCreation']
            gameDuration = r.json()['gameDuration']
                
            # 아이템
            item0 = r.json()['participants'][pnum - 1]['stats']['item0']
            item1 = r.json()['participants'][pnum - 1]['stats']['item1']
            item2 = r.json()['participants'][pnum - 1]['stats']['item2']
            item3 = r.json()['participants'][pnum - 1]['stats']['item3']
            item4 = r.json()['participants'][pnum - 1]['stats']['item4']
            item5 = r.json()['participants'][pnum - 1]['stats']['item5']
            item6 = r.json()['participants'][pnum - 1]['stats']['item6']
    
            # 승패
            if r.json()['participants'][pnum - 1]['stats']['win'] == 1:
                win = 'Win'
            
            else:
                win = 'Lose'
    
            # KDA
            kills = r.json()['participants'][pnum - 1]['stats']['kills']
            deaths = r.json()['participants'][pnum - 1]['stats']['deaths']
            assists = r.json()['participants'][pnum - 1]['stats']['assists']
        
            # CS
            neutralMinionsKilled = r.json()['participants'][pnum - 1]['stats']['neutralMinionsKilled']
            totalMinionsKilled = r.json()['participants'][pnum - 1]['stats']['totalMinionsKilled']
        
            # 챔피언레벨
            champLevel = r.json()['participants'][pnum - 1]['stats']['champLevel']
        
            # 챔피언이 입힌 데미지
            totalDamageDealtToChampions = r.json()['participants'][pnum - 1]['stats']['totalDamageDealtToChampions']
        
            # 총피해량, 마법, 물리
            totalDamageDealt = r.json()['participants'][pnum - 1]['stats']['totalDamageDealt']
            magicDamageDealt = r.json()['participants'][pnum - 1]['stats']['magicDamageDealt']
            physicalDamageDealt = r.json()['participants'][pnum - 1]['stats']['physicalDamageDealt']
        
            # 총 입은 피해량
            totalDamageTaken = r.json()['participants'][pnum - 1]['stats']['totalDamageTaken']
        
            # 시간대별 분당 골드 획득량
            # 획득량 초기화
            gold0to10 = 0
            gold10to20 = 0
            gold20to30 = 0
            gold30toend = 0
            if "goldPerMinDeltas" in r.json()['participants'][pnum - 1]['timeline']:
                if "0-10" in r.json()['participants'][pnum - 1]['timeline']['goldPerMinDeltas']:
                    gold0to10 = r.json()['participants'][pnum - 1]['timeline']['goldPerMinDeltas']['0-10']
                else:
                    pass
                
                if "10-20" in r.json()['participants'][pnum - 1]['timeline']['goldPerMinDeltas']:
                    gold10to20 = r.json()['participants'][pnum - 1]['timeline']['goldPerMinDeltas']['10-20']
                else:
                    pass
                
                if "20-30" in r.json()['participants'][pnum - 1]['timeline']['goldPerMinDeltas']:
                    gold20to30 = r.json()['participants'][pnum - 1]['timeline']['goldPerMinDeltas']['20-30']
                else:
                    pass
                
                if "30-end" in r.json()['participants'][pnum - 1]['timeline']['goldPerMinDeltas']:
                    gold30toend = r.json()['participants'][pnum - 1]['timeline']['goldPerMinDeltas']['30-end']
                else:
                    pass
                    
            else:  # 10분 이전에 경기 끝나는 것 걸러내기
                pass
        
            # 스펠
            spell1Id = r.json()['participants'][pnum - 1]['spell1Id']
            spell2Id = r.json()['participants'][pnum - 1]['spell2Id']
        
            # 룬
            perk0 = r.json()['participants'][pnum - 1]['stats']['perk0']
            perk0Var1 = r.json()['participants'][pnum - 1]['stats']['perk0Var1']
            perk0Var2 = r.json()['participants'][pnum - 1]['stats']['perk0Var2']
            perk0Var3 = r.json()['participants'][pnum - 1]['stats']['perk0Var3']
            perk1 = r.json()['participants'][pnum - 1]['stats']['perk1']
            perk1Var1 = r.json()['participants'][pnum - 1]['stats']['perk1Var1']
            perk1Var2 = r.json()['participants'][pnum - 1]['stats']['perk1Var2']
            perk1Var3 = r.json()['participants'][pnum - 1]['stats']['perk1Var3']
            perk2 = r.json()['participants'][pnum - 1]['stats']['perk2']
            perk2Var1 = r.json()['participants'][pnum - 1]['stats']['perk2Var1']
            perk2Var2 = r.json()['participants'][pnum - 1]['stats']['perk2Var2']
            perk2Var3 = r.json()['participants'][pnum - 1]['stats']['perk2Var3']
            perk3 = r.json()['participants'][pnum - 1]['stats']['perk3']
            perk3Var1 = r.json()['participants'][pnum - 1]['stats']['perk3Var1']
            perk3Var2 = r.json()['participants'][pnum - 1]['stats']['perk3Var2']
            perk3Var3 = r.json()['participants'][pnum - 1]['stats']['perk3Var3']
            perk4 = r.json()['participants'][pnum - 1]['stats']['perk4']
            perk4Var1 = r.json()['participants'][pnum - 1]['stats']['perk4Var1']
            perk4Var2 = r.json()['participants'][pnum - 1]['stats']['perk4Var2']
            perk4Var3 = r.json()['participants'][pnum - 1]['stats']['perk4Var3']
            perk5 = r.json()['participants'][pnum - 1]['stats']['perk5']
            perk5Var1 = r.json()['participants'][pnum - 1]['stats']['perk5Var1']
            perk5Var2 = r.json()['participants'][pnum - 1]['stats']['perk5Var2']        
            perk5Var3 = r.json()['participants'][pnum - 1]['stats']['perk5Var3']
            perkPrimaryStyle = r.json()['participants'][pnum - 1]['stats']['perkPrimaryStyle']
            perkSubStyle = r.json()['participants'][pnum - 1]['stats']['perkSubStyle']
            statPerk0 = r.json()['participants'][pnum - 1]['stats']['statPerk0']
            statPerk1 = r.json()['participants'][pnum - 1]['stats']['statPerk1']
            statPerk2 = r.json()['participants'][pnum - 1]['stats']['statPerk2']

            # 같이 게임한 사람들의 챔피언 번호(본인 포함)
            myChamp = r.json()['participants'][pnum - 1]['championId']
            participant1 = r.json()['participants'][0]['championId']
            participant2 = r.json()['participants'][1]['championId']
            participant3 = r.json()['participants'][2]['championId']
            participant4 = r.json()['participants'][3]['championId']
            participant5 = r.json()['participants'][4]['championId']
            participant6 = r.json()['participants'][5]['championId']
            participant7 = r.json()['participants'][6]['championId']
            participant8 = r.json()['participants'][7]['championId']
            participant9 = r.json()['participants'][8]['championId']
            participant10 = r.json()['participants'][9]['championId']
        
            # 챔피언 롤, 레인
            champRole = r.json()['participants'][pnum - 1]['timeline']['role']
            champLane = r.json()['participants'][pnum - 1]['timeline']['lane']
                
            overalllist.append([result[q][0], name, str(gameCreation), str(gameDuration), str(champRole), str(champLane), win, item0, item1, item2, item3, item4, \
                item5, item6, int(kills), int(deaths), int(assists), int(neutralMinionsKilled), int(totalMinionsKilled), \
                int(champLevel), int(totalDamageDealtToChampions), int(totalDamageDealt), int(magicDamageDealt), int(physicalDamageDealt), \
                int(totalDamageTaken), int(gold0to10), int(gold10to20), int(gold20to30), int(gold30toend), int(spell1Id), int(spell2Id), int(perk0), int(perk0Var1), int(perk0Var2), int(perk0Var3), \
                int(perk1), int(perk1Var1), int(perk1Var2), int(perk1Var3), int(perk2), int(perk2Var1), int(perk2Var2), int(perk2Var3), int(perk3), \
                int(perk3Var1), int(perk3Var2), int(perk3Var3), \
                int(perk4), int(perk4Var1), int(perk4Var2), int(perk4Var3), int(perk5), int(perk5Var1), int(perk5Var2), \
                int(perk5Var3), int(perkPrimaryStyle), int(perkSubStyle), int(statPerk0), int(statPerk1), int(statPerk2), \
                int(myChamp), int(participant1), int(participant2), int(participant3), int(participant4), int(participant5), int(participant6), int(participant7), int(participant8), int(participant9), int(participant10), patch_version])
                
            bufferlist.append((1, result[q][0]))
            
        if (q+1) % 80 == 0 or (q+1) == num:
            sql = '''INSERT INTO overall(match_id, name, game_creation, game_duration, champ_role, champ_lane, win, item_0, item_1, item_2, item_3,\
                item_4, item_5, item_6, kills, deaths, assists, neutral_minions_killed, total_minions_killed, champ_level, \
                total_damage_dealt_to_champions, total_damage_dealt, magic_damage_dealt, physical_damage_dealt, total_damage_taken, gold0_to_10, gold10_to_20, gold20_to_30, gold30_to_end, spell1_id, spell2_id, perk0, perk0_var1, perk0_var2, perk0_var3, \
                perk1, perk1_var1, perk1_var2, perk1_var3, perk2, perk2_var1, perk2_var2, perk2_var3, perk3, perk3_var1, perk3_var2, perk3_var3,\
                perk4, perk4_var1, perk4_var2, perk4_var3, perk5, perk5_var1, perk5_var2, perk5_var3, perk_primary_style, perk_sub_style, stat_perk0, stat_perk1, stat_perk2, \
                my_champ, participant_1, participant_2, participant_3, participant_4, participant_5, participant_6, participant_7, participant_8, participant_9, participant_10, patch_version)\
                values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
            cur.executemany(sql, overalllist)
            con.commit()
            overalllist.clear()
            
            sql = 'UPDATE matches SET overall_use = (%s) WHERE match_id in (%s)'
            cur.executemany(sql, bufferlist)
            con.commit()
            bufferlist.clear()

def data_analysis(num, api_key):
    bufferlist = list()
    bufferlist_2 = list()
    num_2 = int()

    sql = 'SELECT match_id FROM matches WHERE dataanalysis_use is NULL'
    cur.execute(sql)
    result = cur.fetchall()

    if num < len(result):
            num_2 = num
    else:
        num_2 = len(result)

    for i in range(num_2):

        api = 'https://kr.api.riotgames.com/lol/match/v4/matches/' + result[i][0] + '?api_key=' + api_key
        r = requests.get(api)
        if r.status_code == 429:
            r = limit(r, api)

        global winchampionlist
        global winrolelist
        global loserolelist
        global winlanelist
        global loselanelist

        game_duration = r.json()['gameDuration'] / 60
        team100_WL = r.json()['teams'][0]['win']

        #matchId 1개당 10명의 소환사 정보 저장 방법 구현
        for q in range(10):
            if (team100_WL == 'Win'):
                if (q<5):
                    winchampionlist[q] = r.json()['participants'][q]['championId']
                    winrolelist[q] = r.json()['participants'][q]['timeline']['role']
                    winlanelist[q] = r.json()['participants'][q]['timeline']['lane']
                else:
                    losechampionlist[q-5] = r.json()['participants'][q]['championId']
                    loserolelist[q-5] = r.json()['participants'][q]['timeline']['role']
                    loselanelist[q-5] = r.json()['participants'][q]['timeline']['lane']
            else:
                if (q<5):
                    losechampionlist[q] = r.json()['participants'][q]['championId']
                    loserolelist[q] = r.json()['participants'][q]['timeline']['role']
                    loselanelist[q] = r.json()['participants'][q]['timeline']['lane']
                else:
                    winchampionlist[q-5] = r.json()['participants'][q]['championId']
                    winrolelist[q-5] = r.json()['participants'][q]['timeline']['role']
                    winlanelist[q-5] = r.json()['participants'][q]['timeline']['lane']
        
        roletotal = winrolelist + loserolelist
        lanetotal = winlanelist + loselanelist
        j = 0
        for k in range(10):
            if j == 8:
                break

            if lanetotal[k] == 'BOTTOM':
                j += 1
                if roletotal[k] == 'DUO_CARRY':
                    lanetotal[k] = 'AD_CARRY'
                elif roletotal[k] == 'DUO_SUPPORT':
                    lanetotal[k] = 'SUPPORT'

        winlanelist = lanetotal[0:5]
        loselanelist = lanetotal[5:]


        for temp in range(5):
            bufferlist.append([result[i][0], game_duration, 'win', winchampionlist[temp], winlanelist[temp]])
            bufferlist.append([result[i][0], game_duration, 'lose', losechampionlist[temp], loselanelist[temp]])
 
        bufferlist_2.append((1, result[i][0]))

        if (i+1) % 80 == 0 or (i+1) == num:

            #winrate_by_lane 테이블에 라인 및 챔피언 번호 저장
            sql = 'INSERT INTO winrate_summoner(match_id, game_duration, win_or_lose, champion_id, champion_lane) values(%s, %s, %s, %s, %s)' 
            cur.executemany(sql, bufferlist)
            con.commit()

            sql = 'UPDATE matches SET dataanalysis_use = (%s) WHERE match_id in (%s)'
            cur.executemany(sql, bufferlist_2)
            con.commit()
            
            bufferlist.clear()
            bufferlist_2.clear()

# get_high_sumonerid('challengerleagues', 'RGAPI-de6db5ca-44d5-4dc8-be3d-34a617348e67')
# get_high_sumonerid('grandmasterleagues', 'RGAPI-de6db5ca-44d5-4dc8-be3d-34a617348e67')
# get_high_sumonerid('masterleagues', 'RGAPI-de6db5ca-44d5-4dc8-be3d-34a617348e67')
get_low_sumonerid('DIAMOND', 'RGAPI-de6db5ca-44d5-4dc8-be3d-34a617348e67')

# while(True):
# get_accountid(10, 'RGAPI-de6db5ca-44d5-4dc8-be3d-34a617348e67') 
# get_matchid(10, 20, 1622613600) 
    # get_10_summoners(20, 'RGAPI-de6db5ca-44d5-4dc8-be3d-34a617348e67') 
    # get_overall(20, 'RGAPI-de6db5ca-44d5-4dc8-be3d-34a617348e67') 
    # data_analysis(20, 'RGAPI-de6db5ca-44d5-4dc8-be3d-34a617348e67')
# get_item(20, 'RGAPI-de6db5ca-44d5-4dc8-be3d-34a617348e67')