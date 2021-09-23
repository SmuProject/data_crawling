import pymysql

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

sql = 'INSERT INTO TOP_JUG_MID_combination (win_or_lose, lane_1, id_1, lane_2, id_2, lane_3, id_3) SELECT C.win_or_lose, lane_1, id_1, lane_2, id_2, C.champion_lane as ' + "'" + 'lane_3' + "'" + ', C.champion_id as' + " '" + 'id_3' + "'" + ' FROM winrate_summoner as C JOIN (SELECT A.match_id, A.win_or_lose, A.champion_lane as ' + "'" + 'lane_1' +  "'" +', A.champion_id as' + " '" +  'id_1' + "'" + ', B.champion_lane as lane_2, B.champion_id as id_2 FROM winrate_summoner as A JOIN winrate_summoner as B ON A.match_id = B.match_id and A.win_or_lose = B.win_or_lose and A.champion_lane =' + "'" + 'TOP' + "' " + 'and B.champion_lane = ' + "'" + 'JUNGLE' +"'" + ') as D ON C.match_id = D.match_id and C.win_or_lose = D.win_or_lose and C.champion_lane = ' + "'" + 'MIDDLE' + "'"
print(sql)
cur.execute(sql)